# Package imports
from django.conf import settings
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from datetime import (
    datetime, 
    date,
)
from django.db.models import Q
import razorpay
from django.db import transaction
import environ

# View imports
from app.core.views import (
    CustomPageNumberPagination,
)

# Serializer imports
from app.service_booking.serializers import (
    # Service Booking serializers for Resident User
    ServiceForBookingDisplaySerializer,
    ServiceCategoryForBookingDisplaySerializer,
    ServiceSubCategoryForBookingDisplaySerializer,
    ServiceRequestHistoryRecordsListSerializer,
    ServiceSlotForBookingDisplaySerializer,
    ServiceRequestServiceSlotForBookingCreateSerializer,
    PaymentForBookingCreateSerializer,

    # Service Booking serializers for Organization Administrator
    AssignedUserServiceRequestSerializer,

    # Service Booking serializers for Organization Administrator and Employee
    ServiceRequestAllRecordsListSerializer,
    EstablishmentDisplaySerializer,
    UserDisplaySerializer,

    # Service Booking serializers for Resident User and Organization Administrator
    ServiceRequestCreateSerializer,
    ServiceRequestCompleteSerializer,

    # Service Booking serializers for Employee, Resident User and Organization Administrator
    ServiceRequestDisplaySerializer,
    ServiceRequestServiceSlotForBookingDisplaySerializer
)

# Model imports
from app.core.models import (
    Service,
    ServiceCategory,
    ServiceSubCategory,
    ServiceExclusion,
    ServiceSlot,
    ServiceRequest,
    Establishment,
    Payment,
    ServiceRequestServiceSlot
)   
from django.contrib.auth import get_user_model

# Utility imports
from app.utils import (
    get_response_schema,
    get_global_success_messages,
    get_global_error_messages,
    get_global_values,
    get_current_flat,
    send_notification,
    get_payable_service_request_amount
)
from app.permissions import (
    does_permission_exist
)

# Swagger imports
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

env = environ.Env()
environ.Env.read_env()


# Start Service Booking views for Resident User
class ServiceForBookingListFilter(ListAPIView):
    """ View: List Service for Booking for Resident User """

    serializer_class = ServiceForBookingDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [get_global_values()['RESIDENT_USERS_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        flat_obj = get_current_flat(self.request.user)

        if not flat_obj:
            return []

        queryset = Service.objects.select_related(
            'owner_organization',
            'subcategory',
            'subcategory__category',
        ).filter(
            is_active=True,
        ).order_by(
            'name',
            'owner_organization__name'
        )

        if self.request.query_params.get('search'):
            queryset = queryset.filter(name__icontains=self.request.query_params.get('search'))

        if self.request.query_params.get('category_id'):
            queryset = queryset.filter(subcategory__category__id=self.request.query_params.get('category_id'))

        if self.request.query_params.get('sub_category_id'):
            queryset = queryset.filter(subcategory__id=self.request.query_params.get('sub_category_id'))

        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('category_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('sub_category_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),

        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ServiceCategoryForBookingDropdown(GenericAPIView):
    """ View: List ServiceCategory (dropdown) for Resident User """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['RESIDENT_USERS_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        flat_obj = get_current_flat(request.user)

        if not flat_obj:
            return_data = {
                'no_current_flat': True
            }
            return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

        queryset = ServiceCategory.objects.select_related(
            'owner_organization'
        ).filter(
            is_active=True,
        ).order_by(
            'name',
            'owner_organization__name'
        )

        service_category_display_serializer = ServiceCategoryForBookingDisplaySerializer(queryset, many=True)

        return Response(service_category_display_serializer.data, status=status.HTTP_200_OK)


class ServiceSubCategoryForBookingDropdown(GenericAPIView):
    """ View: List ServiceSubCategory (dropdown) for Resident User """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):

        # Check role permissions
        required_role_list = [get_global_values()['RESIDENT_USERS_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        flat_obj = get_current_flat(request.user)

        if not flat_obj:
            return_data = {
                'no_current_flat': True
            }
            return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

        queryset = ServiceSubCategory.objects.select_related(
            'owner_organization'
        ).filter(
            category=pk,
            is_active=True,
        ).order_by(
            'name',
            'owner_organization__name'
        )

        service_sub_category_display_serializer = ServiceSubCategoryForBookingDisplaySerializer(queryset, many=True)

        return Response(service_sub_category_display_serializer.data, status=status.HTTP_200_OK)


class ServiceSlotFromDate(GenericAPIView):
    """ View: Get ServiceSlot from Date and Service for Resident User """

    authentication_classes = [JWTAuthentication]

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('service', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('requested_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        ]
    )
    def get(self, request, format=None):

        permission_role_list = [get_global_values()['RESIDENT_USERS_ROLE_ID']]

        permissions = does_permission_exist(permission_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        flat_obj = get_current_flat(request.user)

        if not flat_obj:
            return_data = {
                'no_current_flat': True
            }
            return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

        if not (request.query_params.get('service')) or not (request.query_params.get('requested_date')):
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_RESPONSE']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        # Validating service ID
        service_queryset = Service.objects.filter(
            pk=request.query_params.get('service'),
            is_active=True,
        )

        requested_date_str = request.query_params.get('requested_date')

        try:
            requested_date = datetime.strptime(requested_date_str, '%Y-%m-%dT%H:%M:%S.%fZ').date()
        except:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        if str(requested_date) < str(date.today()):
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['PAST_DATE']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        if service_queryset.exists():

            # Validating the 'requested_date' that date is not present in ServiceExclusion
            service_exclusion_queryset = ServiceExclusion.objects.filter(
                service__id=request.query_params.get('service'),
                exclusion_date=requested_date
            )

            # Validating the 'requested_date' that time is available in ServiceSlot
            service_slot_queryset = ServiceSlot.objects.filter(
                service__id=request.query_params.get('service'),
                day_of_week=requested_date.weekday() + 1
            ).order_by(
                'start_time'
            )

            if (not service_exclusion_queryset.exists()):

                if (service_slot_queryset.exists()):

                    serializer = ServiceSlotForBookingDisplaySerializer(service_slot_queryset, many=True)

                    return get_response_schema(serializer.data, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)

                else:
                    return_data = {
                        settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['NO_SLOTS']]
                    }
                    return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

            else:
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_REQUESTED_DATE']]
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class PayableAmountOfServiceRequest(GenericAPIView):
    """ View: Get Payable amount of Service Request """

    authentication_classes = [JWTAuthentication]

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('service', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('requested_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            openapi.Parameter('requested_slots', openapi.IN_QUERY, type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
        ]
    )
    def get(self, request, format=None):

        permission_role_list = [get_global_values()['RESIDENT_USERS_ROLE_ID']]

        permissions = does_permission_exist(permission_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        flat_obj = get_current_flat(request.user)

        if not flat_obj:
            return_data = {
                'no_current_flat': True
            }
            return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

        requested_slots = [int(i) for i in request.query_params.get('requested_slots').split(",")]

        if not (request.query_params.get('service')) or not (request.query_params.get('requested_slots')) or not (request.query_params.get('requested_date')):
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_RESPONSE']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        # Validating service ID
        service_queryset = Service.objects.filter(
            pk=request.query_params.get('service'),
            is_active=True,
        )

        requested_date_str = request.query_params.get('requested_date')

        try:
            requested_date = datetime.strptime(requested_date_str, '%Y-%m-%dT%H:%M:%S.%fZ').date()
        except:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        if str(requested_date) < str(date.today()):
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['PAST_DATE']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        if service_queryset.exists():

            # Validating selected_number_of_slots
            service_slot_queryset = ServiceSlot.objects.filter(
                service=service_queryset.first(),
                pk__in=requested_slots,
                day_of_week=requested_date.weekday() + 1,
                is_active=True
            )

            # Validating the 'requested_date' that date is not present in ServiceExclusion
            service_exclusion_queryset = ServiceExclusion.objects.filter(
                service__id=request.query_params.get('service'),
                exclusion_date=requested_date
            )

            if service_exclusion_queryset or not service_slot_queryset:
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_REQUESTED_DATE']]
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

            return_data = get_payable_service_request_amount(service_queryset.first(), int(len(service_slot_queryset)))

            # Manuplating response
            return_data['service'] = request.query_params.get('service')

            return_data['requested_slots'] = [i.pk for i in service_slot_queryset]

            return get_response_schema(return_data, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)

        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class ServiceRequestCreate(GenericAPIView):
    """ View: Create ServiceRequest booking for Resident User """

    authentication_classes = [JWTAuthentication]

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'service': openapi.Schema(type=openapi.TYPE_INTEGER),
                'requested_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'requested_service_slots': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                )
            },
        )
    )
    def post(self, request, format=None):

        permission_role_list = [get_global_values()['RESIDENT_USERS_ROLE_ID']]

        permissions = does_permission_exist(permission_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        flat_obj = get_current_flat(request.user)

        if not flat_obj:
            return_data = {
                'no_current_flat': True
            }
            return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

        if ('service' not in request.data.keys()) or ('requested_date' not in request.data.keys()) or ('requested_service_slots' not in request.data.keys()) or (len(request.data['requested_service_slots']) == 0):
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_RESPONSE']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        # Handling Date format from Front End
        requested_date_str = request.data['requested_date']

        try:
            requested_date = datetime.strptime(requested_date_str, '%Y-%m-%dT%H:%M:%S.%fZ').date()
        except:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        if str(requested_date) < str(date.today()):
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['PAST_DATE']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        # Validating service ID
        service_queryset = Service.objects.filter(
            pk=request.data['service'],
            is_active=True,
        )

        if service_queryset.exists():

            # Validating the 'requested_date' that date is not present in ServiceExclusion
            service_exclusion_queryset = ServiceExclusion.objects.filter(
                service__id=request.data['service'],
                exclusion_date=requested_date
            )

            # Validating the 'requested_service_slots' that time is available in ServiceSlot
            service_slot_queryset = ServiceSlot.objects.filter(
                service__id=request.data['service'],
                day_of_week=requested_date.weekday() + 1,
                is_active=True,
                pk__in=request.data['requested_service_slots']
            )

            if (not service_exclusion_queryset.exists()):

                if (service_slot_queryset.exists()):

                    amount_data = get_payable_service_request_amount(service_queryset.first(), int(len(service_slot_queryset)))

                    # Data manuplation for Service Request model
                    request.data['flat'] = flat_obj.id

                    request.data['requested_user'] = request.user.id

                    request.data['service_request_status'] = ServiceRequest.ServiceRequestStatus.PENDING

                    request.data['requested_date'] = requested_date

                    request.data['amount'] = int(amount_data['amount'])

                    # Validating if payable amount is 0 then is_active needs to be True
                    if int(amount_data['amount']) == 0:
                        request.data['is_active'] = True

                    del request.data['requested_service_slots']

                    service_request_create_serializer = ServiceRequestCreateSerializer(data=request.data)

                    if service_request_create_serializer.is_valid():

                        with transaction.atomic():

                            service_request_obj = service_request_create_serializer.save()

                            # Now saving the records in ServiceRequestServiceSlot
                            # preparing data for requested service slot

                            requested_service_slots_data = []

                            for i in service_slot_queryset:

                                temp_dict = {}

                                temp_dict['service_request'] = service_request_obj.pk
                                temp_dict['service_slot'] = i.pk
                                temp_dict['start_time'] = i.start_time
                                temp_dict['end_time'] = i.end_time

                                requested_service_slots_data.append(temp_dict)

                            service_request_service_slot_serializer = ServiceRequestServiceSlotForBookingCreateSerializer(data=requested_service_slots_data, many=True)

                            if service_request_service_slot_serializer.is_valid():

                                service_request_service_slot_serializer.save()

                                # Validating if payable amount is 0 then Payment related stuffs will not be executed
                                if int(amount_data['amount']) == 0:

                                    return_data = {
                                        'amenity_booking': service_request_create_serializer.data,
                                        'requested_amenity_slots': service_request_service_slot_serializer.data,
                                        'payment': None
                                    }

                                    return get_response_schema(return_data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

                                # Create order_id for the razorpay
                                client = razorpay.Client(auth=(env('PUBLIC_KEY'), env('SECRET_KEY')))

                                order_dictionary = {
                                    'amount': int(amount_data['amount']) * 100, # To convert amount into Ruppess
                                    'currency': get_global_values()['CURRENCY'],
                                    'notes': {
                                        get_global_values()['SERVICE_REQUEST_OBJECT_ID']: service_request_obj.pk
                                    }
                                }

                                payment = client.order.create(order_dictionary)

                                payment_data = {
                                    'order_id': payment['id'],
                                    'payment_id': '',
                                    'signature': '',
                                    'amount': int(amount_data['amount']),
                                    'payment_status': Payment.PaymentStatus.PENDING
                                }

                                payment_create_serialzier = PaymentForBookingCreateSerializer(data=payment_data)

                                if payment_create_serialzier.is_valid():

                                    payment_obj = payment_create_serialzier.save()

                                    # Update the service_request with Payment FK
                                    service_request_update_body = {
                                        'payment_info': payment_obj.pk
                                    }

                                    service_request_update_serializer = ServiceRequestCreateSerializer(service_request_obj, data=service_request_update_body, partial=True)

                                    if service_request_update_serializer.is_valid():

                                        service_request_update_serializer.save()

                                        # Sent notification to the respected Organization Administartor
                                        msg = "New Service request " + str(service_queryset.first().name) + " has been raised."

                                        oragnization_administrator_user_obj = service_queryset.first().owner_organization.owner_user

                                        send_notification(oragnization_administrator_user_obj,get_global_success_messages()['SERVICE_REQUEST'], msg)

                                        return_data = {
                                            'service_request': service_request_update_serializer.data,
                                            'requested_service_slots': service_request_service_slot_serializer.data,
                                            'payment': payment_create_serialzier.data
                                        }

                                        return get_response_schema(return_data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

                                    # ServiceRequestCreateSerializer serializer errors
                                    # Rollback the transaction
                                    transaction.set_rollback(True)

                                    return_data = {
                                        settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                                        get_global_values()['ERROR_KEY']: service_request_update_serializer.errors
                                    }
                                    return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

                                # PaymentForBookingCreateSerializer serializer errors
                                # Rollback the transaction
                                transaction.set_rollback(True)

                                return_data = {
                                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                                    get_global_values()['ERROR_KEY']: payment_create_serialzier.errors
                                }
                                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

                            # ServiceRequestServiceSlotForBookingCreateSerializer serializer errors
                            # Rollback the transaction
                            transaction.set_rollback(True)

                            return_data = {
                                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                                get_global_values()['ERROR_KEY']: service_request_service_slot_serializer.errors
                            }
                            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

                    else:
                        # ServiceRequestCreateSerializer serializer errors
                        return get_response_schema(service_request_create_serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

                else:
                    return_data = {
                        settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_REQUESTED_TIME']]
                    }
                    return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

            else:
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_REQUESTED_DATE']]
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class ServiceRequestCallback(GenericAPIView):
    """ View: ServiceRequest callback to confirm payment Resident User """

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'razorpay_order_id': openapi.Schema(type=openapi.TYPE_STRING),
                'razorpay_payment_id': openapi.Schema(type=openapi.TYPE_STRING),
                'razorpay_signature': openapi.Schema(type=openapi.TYPE_STRING),
            },
        )
    )
    def post(self, request, format=None):

        client = razorpay.Client(auth=(env('PUBLIC_KEY'), env('SECRET_KEY')))

        fetch_order_id = client.order.fetch(request.data['razorpay_order_id'])

        service_request_object_id = fetch_order_id['notes'][get_global_values()['SERVICE_REQUEST_OBJECT_ID']]

        service_request_queryset = ServiceRequest.objects.filter(
            pk=service_request_object_id,
            is_active=False
        )

        if request.data['razorpay_payment_id'] == '' and request.data['razorpay_signature'] == '':

            try:
                if service_request_queryset:

                    for i in service_request_queryset:

                        i.payment_info.delete()

                        i.delete()

                else:
                    return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

                return get_response_schema({}, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

            except:
                return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        else:

            try:
                check = client.utility.verify_payment_signature(request.data)

                if check:

                    payment_status = Payment.PaymentStatus.SUCCESS

                    is_active = True

                else:

                    payment_status = Payment.PaymentStatus.FAIL

                    is_active = False

            except Exception as e:

                payment_status = Payment.PaymentStatus.FAIL

                is_active = False

            try:
                if service_request_queryset:

                    payment_obj = service_request_queryset.first().payment_info

                    data={
                        'payment_status': payment_status,
                        'payment_id': request.data['razorpay_payment_id'],
                        'signature': request.data['razorpay_signature']
                    }

                    payment_update_serialzier = PaymentForBookingCreateSerializer(payment_obj, data=data, partial=True)

                    if payment_update_serialzier.is_valid():

                        with transaction.atomic():

                            payment_obj = payment_update_serialzier.save()

                            service_request_obj = service_request_queryset.first()

                            service_request_data = {
                                'is_active': is_active
                            }

                            service_request_update_serializer = ServiceRequestCreateSerializer(service_request_obj, data=service_request_data, partial=True)

                            if service_request_update_serializer.is_valid():

                                service_request_update_serializer.save()

                                return_data = {
                                    'payment': payment_update_serialzier.data,
                                    'service_request': service_request_update_serializer.data
                                }

                                return get_response_schema(return_data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

                            # ServiceRequestCreateSerializer serializer errors
                            # Rollback the transaction
                            transaction.set_rollback(True)

                            return_data = {
                                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                                get_global_values()['ERROR_KEY']: service_request_update_serializer.errors
                            }
                            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

                    else:
                        # PaymentForBookingCreateSerializer serializer errors
                        return_data = {
                            settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                            get_global_values()['ERROR_KEY']: payment_update_serialzier.errors
                        }
                        return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

                else:
                    return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)    

            except:
                return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)


class ServiceBookingHistoryListFilter(ListAPIView):
    """ View: Service booking history list for Resident User """

    serializer_class = ServiceRequestHistoryRecordsListSerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [get_global_values()['RESIDENT_USERS_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        flat_obj = get_current_flat(self.request.user)

        if not flat_obj:
            return []

        queryset = ServiceRequest.objects.select_related(
            'service',
            'service__subcategory',
            'service__subcategory__category',
            'service__owner_organization',
            'assigned_user'
        ).filter(
            is_active=True,
            flat=flat_obj,
            requested_user=self.request.user,
        ).order_by(
            '-requested_date',
        )

        if self.request.query_params.get('service_request_status'):
            queryset = queryset.filter(service_request_status=self.request.query_params.get('service_request_status'))

            if self.request.query_params.get('service_request_status') == ServiceRequest.ServiceRequestStatus.PENDING:
                queryset = queryset.order_by('requested_date')

        if self.request.query_params.get('rating'):
            queryset = queryset.filter(rating=self.request.query_params.get('rating'))

        if self.request.query_params.get('requested_date'):
            queryset = queryset.filter(requested_date=self.request.query_params.get('requested_date'))

        if self.request.query_params.get('search'):
            queryset = queryset.filter(Q(service__name__icontains=self.request.query_params.get('search')))

        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('service_request_status', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=[ServiceRequest.ServiceRequestStatus.PENDING, ServiceRequest.ServiceRequestStatus.APPROVED, ServiceRequest.ServiceRequestStatus.ASSIGNED, ServiceRequest.ServiceRequestStatus.COMPLETED, ServiceRequest.ServiceRequestStatus.REJECTED]),
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('rating', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('requested_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class AddRatingServiceRequest(GenericAPIView):
    """ View: Add rating to the Service Request Resident User """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'rating': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        )
    )
    def patch(self, request, pk):

        permission_role_list = [get_global_values()['RESIDENT_USERS_ROLE_ID']]

        permissions = does_permission_exist(permission_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        flat_obj = get_current_flat(request.user)

        if not flat_obj:
            return_data = {
                'no_current_flat': True
            }
            return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

        if ('rating' not in request.data.keys()):
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_RESPONSE']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        service_request_queryset = ServiceRequest.objects.filter(
            pk=pk,
            is_active=True,
            requested_user=request.user,
            flat=flat_obj,
            service_request_status=ServiceRequest.ServiceRequestStatus.COMPLETED
        )

        if service_request_queryset:

            service_request = service_request_queryset.first()

            serializer = ServiceRequestCompleteSerializer(service_request, data=request.data, partial=True)

            if serializer.is_valid():

                serializer.save()

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

            else:
                # ServiceRequestCompleteSerializer serializer errors
                return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)
# End Service Booking views for Resident User


# Start Service Booking views for Organization Administrator
class ServiceBookingsListFilterForOrganizationAdministrator(ListAPIView):
    """ View: Service booking history list for Organization Administrator """

    serializer_class = ServiceRequestAllRecordsListSerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        queryset = ServiceRequest.objects.select_related(
            'service',
            'service__subcategory',
            'service__subcategory__category',
            'service__owner_organization',
            'assigned_user',
            'requested_user',
        ).filter(
            is_active=True,
            service__owner_organization=self.request.user.user_details.organization
        ).order_by(
            '-requested_date',
        )

        if self.request.query_params.get('service_request_status'):
            queryset = queryset.filter(service_request_status=self.request.query_params.get('service_request_status'))

        if self.request.query_params.get('establishment'):
            queryset = queryset.filter(flat__building__establishment__id=self.request.query_params.get('establishment'))

        if self.request.query_params.get('requested_user'):
            queryset = queryset.filter(requested_user__id=self.request.query_params.get('requested_user'))

        if self.request.query_params.get('assigned_user'):
            queryset = queryset.filter(assigned_user__id=self.request.query_params.get('assigned_user'))

        if self.request.query_params.get('rating'):
            queryset = queryset.filter(rating=self.request.query_params.get('rating'))

        if self.request.query_params.get('requested_date'):
            queryset = queryset.filter(requested_date=self.request.query_params.get('requested_date'))

        if self.request.query_params.get('search'):
            queryset = queryset.filter(Q(service__name__icontains=self.request.query_params.get('search')))

        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('service_request_status', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=[ServiceRequest.ServiceRequestStatus.PENDING, ServiceRequest.ServiceRequestStatus.APPROVED, ServiceRequest.ServiceRequestStatus.ASSIGNED, ServiceRequest.ServiceRequestStatus.COMPLETED, ServiceRequest.ServiceRequestStatus.REJECTED]),
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('establishment', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('requested_user', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('assigned_user', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('rating', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('requested_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class EstablishmentDropdownForOrganizationAdministrator(GenericAPIView):
    """ View: List Establishment (dropdown) for Organization Admnistrator """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = Establishment.objects.select_related(
            'owner_organization'
        ).filter(
            is_active=True,
            building__flat__requested_service__is_active=True,
            building__flat__requested_service__service__owner_organization=self.request.user.user_details.organization
        ).order_by(
            'name',
            'owner_organization__name'
        ).distinct()

        establishment_display_serializer = EstablishmentDisplaySerializer(queryset, many=True)

        return Response(establishment_display_serializer.data, status=status.HTTP_200_OK)


class RequestedUserDropdownForOrganizationAdministrator(GenericAPIView):
    """ View: List Requested User (dropdown) for Organization Admnistrator """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = get_user_model().objects.filter(
            is_active=True,
            user_role__role__id__in=[get_global_values()['RESIDENT_USERS_ROLE_ID']],
            requested_user__is_active=True,
            requested_user__service__owner_organization=self.request.user.user_details.organization
        ).order_by(
            'first_name',
            'last_name',
        ).distinct()

        user_display_serializer = UserDisplaySerializer(queryset, many=True)

        return Response(user_display_serializer.data, status=status.HTTP_200_OK)


class AssignedUserDropdownForOrganizationAdministrator(GenericAPIView):
    """ View: List Assigned User (dropdown) for Organization Admnistrator """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = get_user_model().objects.filter(
            is_active=True,
            user_role__role__id__in=[get_global_values()['EMPLOYEE_ROLE_ID']],
            service_provider__is_active=True,
            service_provider__service_request_status=ServiceRequest.ServiceRequestStatus.ASSIGNED,
            service_provider__service__owner_organization=self.request.user.user_details.organization
        ).order_by(
            'first_name',
            'last_name',
        ).distinct()

        user_display_serializer = UserDisplaySerializer(queryset, many=True)

        return Response(user_display_serializer.data, status=status.HTTP_200_OK)


class UpdateServiceRequestStatusForOrganizationAdministrator(GenericAPIView):
    """ View: Update Status of Service Request for Organization Administrator """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'service_request_status': openapi.Schema(type='string', enum=[ServiceRequest.ServiceRequestStatus.APPROVED, ServiceRequest.ServiceRequestStatus.REJECTED]),
            },
        )
    )
    def patch(self, request, pk):

        permission_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(permission_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        service_request_queryset = ServiceRequest.objects.filter(
            pk=pk,
            is_active=True,
            service__owner_organization=self.request.user.user_details.organization,
            service_request_status=ServiceRequest.ServiceRequestStatus.PENDING,
            requested_date__gte = date.today()
        )

        if service_request_queryset:

            service_request = service_request_queryset.first()

            serializer = ServiceRequestCreateSerializer(service_request, data=request.data, partial=True)

            if serializer.is_valid():

                serializer.save()

                # Notification sending scenario

                msg = "Status has been updated for " + str(service_request.service.name) + " service."

                requested_user_obj = service_request.requested_user

                send_notification(requested_user_obj,get_global_success_messages()['STATUS_UPDATED'], msg)

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

            else:
                # ServiceRequestCreateSerializer serializer errors
                return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)


class AssignedUserToServiceRequestForOrganizationAdministrator(GenericAPIView):
    """ View: Assign an Employee to service Request for Organization Administrator """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'assigned_user': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        )
    )
    def patch(self, request, pk):

        permission_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(permission_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        service_request_queryset = ServiceRequest.objects.filter(
            pk=pk,
            is_active=True,
            service__owner_organization=self.request.user.user_details.organization,
            service_request_status=ServiceRequest.ServiceRequestStatus.APPROVED,
            requested_date__gte = date.today()
        )

        # Validating assigned user ID
        user_queryset = get_user_model().objects.filter(
            pk=request.data['assigned_user'],
            is_active=True,
            user_role__role__id__in=[get_global_values()['EMPLOYEE_ROLE_ID']],
            user_detail__organization=request.user.user_details.organization
        )

        if service_request_queryset:

            if user_queryset:

                service_request = service_request_queryset.first()

                # Adding Status directly to the "Assigned" automatically
                request.data['service_request_status'] = ServiceRequest.ServiceRequestStatus.ASSIGNED

                serializer = AssignedUserServiceRequestSerializer(service_request, data=request.data, partial=True)

                if serializer.is_valid():

                    serializer.save()

                    # Notification sending scenario

                    # To send notification to employee
                    msg = "New Service request has been assigned for " + str(service_request.service.name) + " service."

                    assigned_user_obj = service_request.assigned_user

                    send_notification(assigned_user_obj,get_global_success_messages()['REQUEST_ASSIGNED'], msg)

                    # To send notification to resident user
                    msg = "An employee has been assigned for " + str(service_request.service.name) + " service."

                    requested_user_obj = service_request.requested_user

                    send_notification(requested_user_obj,get_global_success_messages()['EMPLOYEE_ASSIGNED'], msg)

                    return get_response_schema(serializer.data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

                else:
                    # ServiceRequestCreateSerializer serializer errors
                    return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

            else:
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
        return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)


class AssignedUserToServiceRequestDropdownForOrganizationAdministrator(GenericAPIView):
    """ View: List Assigned User to service request (dropdown) for Organization Admnistrator """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = get_user_model().objects.filter(
            is_active=True,
            user_role__role__id__in=[get_global_values()['EMPLOYEE_ROLE_ID']],
            user_detail__organization=self.request.user.user_details.organization
        ).order_by(
            'first_name',
            'last_name',
        ).distinct()

        user_display_serializer = UserDisplaySerializer(queryset, many=True)

        return Response(user_display_serializer.data, status=status.HTTP_200_OK)
# End Service Booking views for Organization Administrator


# Start Service Booking views for Organization Administrator and Resident User
class CompleteServiceRequest(GenericAPIView):
    """ View: Update Status of Service Request to 'Completed' for Organization Administrator and Resident User """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'rating': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        )
    )
    def patch(self, request, pk):

        permission_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'], get_global_values()['RESIDENT_USERS_ROLE_ID']]

        permissions = does_permission_exist(permission_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        if permissions[str(get_global_values()['RESIDENT_USERS_ROLE_ID'])]:

            flat_obj = get_current_flat(request.user)

            if not flat_obj:
                return_data = {
                    'no_current_flat': True
                }
                return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

            service_request_queryset = ServiceRequest.objects.filter(
                pk=pk,
                is_active=True,
                requested_user=request.user,
                flat=flat_obj,
                service_request_status=ServiceRequest.ServiceRequestStatus.ASSIGNED,
                requested_date__gte = date.today()
            )

        if permissions[str(get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'])]:

            service_request_queryset = ServiceRequest.objects.filter(
                pk=pk,
                is_active=True,
                service__owner_organization=self.request.user.user_details.organization,
                service_request_status=ServiceRequest.ServiceRequestStatus.ASSIGNED,
                requested_date__gte = date.today()
            )

            if ('rating' in request.data.keys()):
                del request.data['rating']

        if service_request_queryset:

            service_request = service_request_queryset.first()

            # Adding Status directly to the "Completed" automatically
            request.data['service_request_status'] = ServiceRequest.ServiceRequestStatus.COMPLETED

            serializer = ServiceRequestCompleteSerializer(service_request, data=request.data, partial=True)

            if serializer.is_valid():

                serializer.save()

                # Notification sending scenario

                msg = "Status has been marked completed for " + str(service_request.service.name) + " service request."

                assigned_user_obj = service_request.assigned_user

                if permissions[str(get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'])]:

                    requested_user_obj = service_request.requested_user

                    send_notification(requested_user_obj,get_global_success_messages()['SERVICE_REQUEST_MARKED_COMPLETED'], msg)

                if permissions[str(get_global_values()['RESIDENT_USERS_ROLE_ID'])]:

                    oragnization_administrator_user_obj = service_request.service.owner_organization.owner_user

                    send_notification(oragnization_administrator_user_obj,get_global_success_messages()['SERVICE_REQUEST_MARKED_COMPLETED'], msg)

                send_notification(assigned_user_obj,get_global_success_messages()['SERVICE_REQUEST_MARKED_COMPLETED'], msg)

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

            else:
                # ServiceRequestCompleteSerializer serializer errors
                return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)
# End Service Booking views for Organization Administrator and Resident User


# Start Service Booking views for Employee
class ServiceBookingsForEmployeeListFilter(ListAPIView):
    """ View: Service booking history list for Employee """

    serializer_class = ServiceRequestAllRecordsListSerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [get_global_values()['EMPLOYEE_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        queryset = ServiceRequest.objects.select_related(
            'service',
            'service__subcategory',
            'service__subcategory__category',
            'service__owner_organization',
            'assigned_user',
            'requested_user',
        ).filter(
            Q(is_active=True) &
            Q(assigned_user=self.request.user) &
            Q(service__owner_organization=self.request.user.user_details.organization) &
            ~Q(service_request_status=ServiceRequest.ServiceRequestStatus.PENDING) &
            ~Q(service_request_status=ServiceRequest.ServiceRequestStatus.REJECTED) &
            ~Q(service_request_status=ServiceRequest.ServiceRequestStatus.APPROVED)
        ).order_by(
            '-requested_date',
        )

        if self.request.query_params.get('service_request_status'):
            queryset = queryset.filter(service_request_status=self.request.query_params.get('service_request_status'))

        if self.request.query_params.get('establishment'):
            queryset = queryset.filter(flat__building__establishment__id=self.request.query_params.get('establishment'))

        if self.request.query_params.get('requested_user'):
            queryset = queryset.filter(requested_user__id=self.request.query_params.get('requested_user'))

        if self.request.query_params.get('rating'):
            queryset = queryset.filter(rating=self.request.query_params.get('rating'))

        if self.request.query_params.get('requested_date'):
            queryset = queryset.filter(requested_date=self.request.query_params.get('requested_date'))

        if self.request.query_params.get('search'):
            queryset = queryset.filter(Q(service__name__icontains=self.request.query_params.get('search')))

        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('service_request_status', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=[ServiceRequest.ServiceRequestStatus.ASSIGNED, ServiceRequest.ServiceRequestStatus.COMPLETED]),
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('establishment', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('requested_user', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('rating', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('requested_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class EstablishmentDropdownForEmployee(GenericAPIView):
    """ View: List Establishment (dropdown) for Employee """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['EMPLOYEE_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = Establishment.objects.select_related(
            'owner_organization'
        ).filter(
            is_active=True,
            building__flat__requested_service__is_active=True,
            building__flat__requested_service__assigned_user=self.request.user,
            building__flat__requested_service__service__owner_organization=self.request.user.user_details.organization
        ).filter(
            Q(building__flat__requested_service__service_request_status=ServiceRequest.ServiceRequestStatus.ASSIGNED) |
            Q(building__flat__requested_service__service_request_status=ServiceRequest.ServiceRequestStatus.COMPLETED) 
        ).order_by(
            'name',
            'owner_organization__name'
        ).distinct()

        establishment_display_serializer = EstablishmentDisplaySerializer(queryset, many=True)

        return Response(establishment_display_serializer.data, status=status.HTTP_200_OK)


class RequestedUserDropdownForEmployee(GenericAPIView):
    """ View: List Requested User (dropdown) for Employee """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['EMPLOYEE_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = get_user_model().objects.filter(
            is_active=True,
            user_role__role__id__in=[get_global_values()['RESIDENT_USERS_ROLE_ID']],
            requested_user__is_active=True,
            requested_user__assigned_user=self.request.user,
            requested_user__service__owner_organization=self.request.user.user_details.organization,
        ).filter(
            Q(requested_user__service_request_status=ServiceRequest.ServiceRequestStatus.ASSIGNED) |
            Q(requested_user__service_request_status=ServiceRequest.ServiceRequestStatus.COMPLETED)
        ).order_by(
            'first_name',
            'last_name',
        ).distinct()

        user_display_serializer = UserDisplaySerializer(queryset, many=True)

        return Response(user_display_serializer.data, status=status.HTTP_200_OK)
# End Service Booking views for Employee


# Start Service Booking views for Employee, Resident User and Organization Administrator
class ServiceRequestDetail(GenericAPIView):
    """ View: GET Service Request for Employee, Resident User and Organization Administrator """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        permission_role_list = [get_global_values()['EMPLOYEE_ROLE_ID'], get_global_values()['RESIDENT_USERS_ROLE_ID'], get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(permission_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        if permissions[str(get_global_values()['EMPLOYEE_ROLE_ID'])]:

            service_request_queryset = ServiceRequest.objects.select_related(
                'service',
                'service__owner_organization',
                'service__subcategory',
                'service__subcategory__category',
                'flat',
                'flat__building',
                'flat__building__establishment',
                'requested_user',
                'assigned_user',
                'payment_info',
            ).filter(
                Q(pk=pk) &
                Q(is_active=True) &
                Q(assigned_user=self.request.user) &
                Q(service__owner_organization=self.request.user.user_details.organization) &
                ~Q(service_request_status=ServiceRequest.ServiceRequestStatus.PENDING) &
                ~Q(service_request_status=ServiceRequest.ServiceRequestStatus.REJECTED) &
                ~Q(service_request_status=ServiceRequest.ServiceRequestStatus.APPROVED)
            )

        if permissions[str(get_global_values()['RESIDENT_USERS_ROLE_ID'])]:

            flat_obj = get_current_flat(request.user)

            if not flat_obj:
                return_data = {
                    'no_current_flat': True
                }
                return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

            service_request_queryset = ServiceRequest.objects.select_related(
                'service',
                'service__owner_organization',
                'service__subcategory',
                'service__subcategory__category',
                'flat',
                'flat__building',
                'flat__building__establishment',
                'requested_user',
                'assigned_user',
                'payment_info',
            ).filter(
                pk=pk,
                is_active=True,
                requested_user=request.user,
                flat=flat_obj
            )

        if permissions[str(get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'])]:

            service_request_queryset = ServiceRequest.objects.select_related(
                'service',
                'service__owner_organization',
                'service__subcategory',
                'service__subcategory__category',
                'flat',
                'flat__building',
                'flat__building__establishment',
                'requested_user',
                'assigned_user',
                'payment_info',
            ).filter(
                pk=pk,
                is_active=True,
                service__owner_organization=self.request.user.user_details.organization
            )

        if service_request_queryset.exists():

            service_request_obj = service_request_queryset.first()

            serializer = ServiceRequestDisplaySerializer(service_request_obj, context={'permissions' : permissions})

            requested_service_slots_queryset = ServiceRequestServiceSlot.objects.select_related(
                'service_slot'
            ).filter(
                service_request=service_request_obj
            )

            requested_service_slots_serializer = ServiceRequestServiceSlotForBookingDisplaySerializer(requested_service_slots_queryset, many=True)

            return_data = serializer.data

            return_data['requested_service_slots'] = requested_service_slots_serializer.data

            return get_response_schema(return_data, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)

        return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)
# End Service Booking views for Employee, Resident User and Organization Administrator
