# Package imports
from django.conf import settings
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Prefetch

# View imports
from app.core.views import (
    CustomPageNumberPagination,
)

# Serializer imports
from app.establishment.serializers import (
    EstablishmentCreateSerializer,
    EstablishmentDisplaySerializer,
)
from app.location.serializers import (
    LocationCreateSerializer
)
from app.address.serializers import (
    AddressCreateSerializer
)

# Model imports
from app.core.models import (
    Establishment,
    UserRole,
    UserEmployeeCategory,
)   

# Utility imports
from app.utils import (
    get_response_schema,
    get_global_success_messages,
    get_global_error_messages,
    get_global_values
)
from app.permissions import (
    does_permission_exist
)

# Swagger imports
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# Start Establishment views
class EstablishmentCreate(GenericAPIView):
    """ View: Create Establishment """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'location': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'latitude': openapi.Schema(type=openapi.TYPE_STRING),
                        'longitude': openapi.Schema(type=openapi.TYPE_STRING),
                        'address': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
                'address': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'address_line_1': openapi.Schema(type=openapi.TYPE_STRING),
                        'address_line_2': openapi.Schema(type=openapi.TYPE_STRING),
                        'pincode': openapi.Schema(type=openapi.TYPE_STRING),
                        'city': openapi.Schema(type=openapi.TYPE_STRING),
                        'state': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
                'establishment': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'start_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                        'end_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                        'water_bill_link': openapi.Schema(type=openapi.TYPE_STRING),
                        'pipe_gas_bill_link': openapi.Schema(type=openapi.TYPE_STRING),
                        'electricity_bill_link': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            }
        )
    )
    def post(self, request):

        with transaction.atomic():

            # Check role permissions
            required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

            permissions = does_permission_exist(required_role_list, request.user.id)

            if not permissions['allowed']:
                return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

            if ('location' not in request.data.keys()) or ('address' not in request.data.keys()) or ('establishment' not in request.data.keys()):
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_RESPONSE']]
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

            # Save location
            location_create_serializer = LocationCreateSerializer(data=request.data['location'])
            if location_create_serializer.is_valid():

                location_obj = location_create_serializer.save()

                # Save address
                address_create_serializer = AddressCreateSerializer(data=request.data['address'])

                if address_create_serializer.is_valid():

                    address_obj = address_create_serializer.save()

                    # Register owner_organization, location and address request
                    request.data['establishment']['owner_organization'] = request.user.user_details.organization.id
                    request.data['establishment']['location'] = location_obj.id
                    request.data['establishment']['address'] = address_obj.id

                    establishment_create_serializer = EstablishmentCreateSerializer(data=request.data['establishment'], context={'request': request})

                    if establishment_create_serializer.is_valid():

                        establishment_create_serializer.save()

                        return_data = {
                            'location': location_create_serializer.data,
                            'address': address_create_serializer.data,
                            'establishment': establishment_create_serializer.data
                        }
                        return get_response_schema(return_data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)
                    # Establishment serializer errors
                    # Rollback the transaction
                    transaction.set_rollback(True)
                    return_data = {
                        settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                        get_global_values()['ERROR_KEY']: establishment_create_serializer.errors
                    }
                    return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

                # Rollback the transaction
                transaction.set_rollback(True)
                # Address error
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_ADDRESS']]
                }

                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)    
            # Location global error
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_LOCATION']]
            }

            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class EstablishmentDetail(GenericAPIView):
    """ View: Retrieve, update or delete an Establishment """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        establishment_queryset = Establishment.objects.select_related(
            'establishment_admin',
            'location',
            'address',
        ).prefetch_related(
            Prefetch('establishment_admin__user_roles', queryset=UserRole.objects.select_related('role')),
            Prefetch('establishment_admin__user_details__employee_categories', queryset=UserEmployeeCategory.objects.select_related('employee_category')),
        ).filter(
            pk=pk,
            is_active=True,
            owner_organization=request.user.user_details.organization
        )

        if establishment_queryset:
            return establishment_queryset[0]
        return None

    def get(self, request, pk=None):

        establishment = self.get_object(pk, request)

        if establishment == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        serializer = EstablishmentDisplaySerializer(establishment)

        return get_response_schema(serializer.data, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'location': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'latitude': openapi.Schema(type=openapi.TYPE_STRING),
                        'longitude': openapi.Schema(type=openapi.TYPE_STRING),
                        'address': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
                'address': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'address_line_1': openapi.Schema(type=openapi.TYPE_STRING),
                        'address_line_2': openapi.Schema(type=openapi.TYPE_STRING),
                        'pincode': openapi.Schema(type=openapi.TYPE_STRING),
                        'city': openapi.Schema(type=openapi.TYPE_STRING),
                        'state': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
                'establishment': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'start_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                        'end_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                        'water_bill_link': openapi.Schema(type=openapi.TYPE_STRING),
                        'pipe_gas_bill_link': openapi.Schema(type=openapi.TYPE_STRING),
                        'electricity_bill_link': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            }
        )
    )
    def put(self, request, pk, format=None):

        establishment = self.get_object(pk, request)

        if establishment == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        # Check if the location has been updated
        location_create_serializer = None

        if request.data['location'] != None:

            location_create_serializer = LocationCreateSerializer(establishment.location, data=request.data['location'])

            if location_create_serializer.is_valid():
                location_create_serializer.save()
            else:
                # Location global error
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_LOCATION']]
                }

                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        # Check if the address has been updated
        address_create_serializer = None

        if request.data['address'] != None:

            address_create_serializer = AddressCreateSerializer(establishment.address, data=request.data['address'])

            if address_create_serializer.is_valid():
                address_create_serializer.save()
            else:
                # Location global error
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_ADDRESS']]
                }

                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        # Handle establishment
        request.data['establishment']['owner_organization'] = request.user.user_details.organization.id

        establishment_create_serializer = EstablishmentCreateSerializer(establishment, data=request.data['establishment'], context={'request': request})

        if establishment_create_serializer.is_valid():
            establishment_create_serializer.save()

            return_data = {
                'location': location_create_serializer.data if location_create_serializer != None else None,
                'address': address_create_serializer.data if address_create_serializer != None else None,
                'establishment': establishment_create_serializer.data
            }

            return get_response_schema(return_data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)
        return_data = {
            settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
            get_global_values()['ERROR_KEY']: establishment_create_serializer.errors
        }
        return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        establishment = self.get_object(pk, request)

        if establishment == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        establishment.is_active = False
        establishment.save()

        return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)


class EstablishmentList(GenericAPIView):
    """ View: List Establishment (dropdown) """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema([], get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = Establishment.objects.select_related(
            'establishment_admin',
            'establishment_admin__user_detail',
            'location',
            'address',
        ).prefetch_related(
            'establishment_admin__role',
            'establishment_admin__user_details__employee_categories'
        ).filter(
            is_active=True,
            owner_organization=self.request.user.user_details.organization
        ).order_by(
            '-start_date'
        )

        establishment_display_serializer = EstablishmentDisplaySerializer(queryset, many=True)

        return Response(establishment_display_serializer.data, status=status.HTTP_200_OK)


class EstablishmentListFilter(ListAPIView):
    """ View: List Establishment Filter """

    serializer_class = EstablishmentDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        queryset = Establishment.objects.select_related(
            'establishment_admin',
            'establishment_admin__user_detail',
            'location',
            'address',
        ).prefetch_related(
            'establishment_admin__role',
            'establishment_admin__user_details__employee_categories'
        ).filter(
            is_active=True,
            owner_organization=self.request.user.user_details.organization
        ).order_by(
            '-start_date'
        )

        if self.request.query_params.get('name'):
            queryset = queryset.filter(name__icontains=self.request.query_params.get('name'))

        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_QUERY, type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
# End Establishment views
