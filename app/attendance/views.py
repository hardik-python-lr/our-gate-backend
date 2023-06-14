# Package imports
from django.conf import settings
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView
from datetime import datetime, date
from django.db import transaction

# Serializer imports
from app.attendance.serializers import (
    EstablishmentGuardAttendanceRecordSerializer,
    DeviceIdSerializer
)
from app.location.serializers import (
    LocationCreateSerializer,
)

# Model imports
from app.core.models import (
    EstablishmentGuardAttendanceRecord,
)

# Utility imports
from app.utils import (
    get_global_values,
    get_response_schema,
    get_global_success_messages,
    get_global_error_messages,
    distance_in_meter,
    attendance_marked_status,
    check_valid_establishment_guard_record,
)

# Custom permissions
from app.permissions import (
    does_permission_exist,
)

# Custom schema in swagger
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


# Start AttendanceRecord CheckIn view
class AttendanceRecordCheckInView(GenericAPIView):
    """ View: AttendanceRecord CheckIn """

    authentication_classes = [JWTAuthentication]

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'location': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'latitude': openapi.Schema(type='string'),
                        'longitude': openapi.Schema(type='string'),
                    }
                ),
                'sign_in_image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64),
                'device_id': openapi.Schema(type='string'),
            }
        )
    )
    def post(self, request):

        permission_role_list = [get_global_values()['SECURITY_GUARD_ROLE_ID']]

        permissions = does_permission_exist(permission_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating 'is_active' is True or not for Establishment Guard
        if permissions[str(get_global_values()['SECURITY_GUARD_ROLE_ID'])]:
            valid_record_status = check_valid_establishment_guard_record(request.user)

            if not valid_record_status['allowed']:
                return_data = {
                    'no_valid_record': True
                }
                return get_response_schema(return_data, get_global_error_messages()['NOT_VALID_ESTABLISHMENT_GUARD_RECORD'], status.HTTP_200_OK)

        if ('location' not in request.data.keys()) or ('sign_in_image' not in request.data.keys()) or ('device_id' not in request.data.keys()):

            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_RESPONSE']]
            }

            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        establishment_guard = valid_record_status['establishment_guard']

        # Fetching Establishment's latitude and longitude for Geo-Mapping
        establishmentlatitude = establishment_guard.establishment.location.latitude

        establishmentlongitude = establishment_guard.establishment.location.longitude

        # Establishment's Radius
        establishmentattendanceradius = establishment_guard.establishment.attendance_radius

        # Distance between user's location and project's location
        distance = distance_in_meter(float(request.data['location']['latitude']), float(request.data['location']['longitude']), establishmentlatitude, establishmentlongitude)

        # Validating Geo-Mapping
        if distance > establishmentattendanceradius:

            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_GEOMAPPING']]
            }

            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        # All the validations before the EstablishmentGuardAttendanceRecord Check-In create
        try:
            attendancerecord = EstablishmentGuardAttendanceRecord.objects.filter(
                establishment_guard=establishment_guard,
                sign_in_time__date=date.today()
            )

            if attendancerecord:
                # If Check-Out is done or not
                if (not attendancerecord.first().sign_out_location) and (not attendancerecord.first().sign_out_time) and (not attendancerecord.first().sign_out_device_id) and (not attendancerecord.first().sign_out_image):

                    return_data = {
                        settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_CHECKIN']]
                    }

                    return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

                # If user is trying to Check-In again on the same date
                if ((attendancerecord.first().sign_out_location) or (attendancerecord.first().sign_out_time) or (attendancerecord.first().sign_out_device_id) or (attendancerecord.first().sign_out_image)) and (attendancerecord.first().sign_in_time.date() == date.today()):

                    return_data = {
                        settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['REPEATED_CHECKIN']]
                    }

                    return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
            else:
                pass

        except EstablishmentGuardAttendanceRecord.DoesNotExist:
            pass

        # Save location

        # manually add 'address' key data as Attendance Address as that key is defined as mendatory in model
        request.data['location']['address'] = get_global_values()['ATTENDANCE_ADDRESS']

        location_create_serializer = LocationCreateSerializer(data=request.data['location'])

        if location_create_serializer.is_valid():

            with transaction.atomic():

                location_obj = location_create_serializer.save()

                # Handling Device ID section

                # Preparing body of the DeviceID
                device_id_body = {
                    'device_id': request.data['device_id']
                }

                device_id_create_serializer = DeviceIdSerializer(data=device_id_body)

                if device_id_create_serializer.is_valid():

                    device_id_obj = device_id_create_serializer.save()

                    # Actual creation of the AttendanceRecord record, once all validation pass 

                    # Preparing the request_body 
                    request_body = {
                        'establishment_guard': establishment_guard.id,
                        'sign_in_location': location_obj.id,
                        'sign_in_image': request.data['sign_in_image'],
                        'sign_in_device_id': device_id_obj.id,
                        'sign_in_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }

                    attendance_record_serializer = EstablishmentGuardAttendanceRecordSerializer(data=request_body)

                    if attendance_record_serializer.is_valid():

                        attendance_record_serializer.save()

                        return_data = {
                            'location': location_create_serializer.data,
                            'device': device_id_create_serializer.data,
                            'attendance': attendance_record_serializer.data,
                            'attendance_status': get_global_success_messages()['CHECKIN_DONE'],
                            'is_checkin' : True,
                            'is_checkout' : False
                        }

                        return get_response_schema(return_data, get_global_success_messages()['USER_CHECKIN'], status.HTTP_201_CREATED)

                    # EstablishmentGuardAttendanceRecordSerializer serializer errors
                    # Rollback the transaction
                    transaction.set_rollback(True)

                    return_data = {
                        settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                        get_global_values()['ERROR_KEY']: attendance_record_serializer.errors
                    }
                    return get_response_schema(attendance_record_serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

                # DeviceIdSerializer serialzer erros
                # Rollback the transaction
                transaction.set_rollback(True)
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                    get_global_values()['ERROR_KEY']: device_id_create_serializer.errors
                }

                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        # LocationCreateSerializer serialzer erros
        return_data = {
            settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_LOCATION']],
            get_global_values()['ERROR_KEY']: location_create_serializer.errors
        }

        return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
# End AttendanceRecord CheckIn view


# Start AttendanceRecord CheckOut view
class AttendanceRecordCheckOutView(GenericAPIView):
    """ View: AttendanceRecord CheckOut """

    authentication_classes = [JWTAuthentication]

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'location': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'latitude': openapi.Schema(type='string'),
                        'longitude': openapi.Schema(type='string'),
                    }
                ),
                'sign_out_image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64),
                'device_id': openapi.Schema(type='string'),
            }
        )
    )
    def patch(self, request, format=None):

        permission_role_list = [get_global_values()['SECURITY_GUARD_ROLE_ID']]

        permissions = does_permission_exist(permission_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating 'is_active' is True or not for Establishment Guard
        if permissions[str(get_global_values()['SECURITY_GUARD_ROLE_ID'])]:
            valid_record_status = check_valid_establishment_guard_record(request.user)

            if not valid_record_status['allowed']:
                return_data = {
                    'no_valid_record': True
                }
                return get_response_schema(return_data, get_global_error_messages()['NOT_VALID_ESTABLISHMENT_GUARD_RECORD'], status.HTTP_200_OK)

        if ('location' not in request.data.keys()) or ('sign_out_image' not in request.data.keys()) or ('device_id' not in request.data.keys()):

            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_RESPONSE']]
            }

            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        establishment_guard = valid_record_status['establishment_guard']

        # Fetching Establishment's latitude and longitude for Geo-Mapping
        establishmentlatitude = establishment_guard.establishment.location.latitude

        establishmentlongitude = establishment_guard.establishment.location.longitude

        # Establishment's Radius
        establishmentattendanceradius = establishment_guard.establishment.attendance_radius

        # Distance between user's location and project's location
        distance = distance_in_meter(float(request.data['location']['latitude']), float(request.data['location']['longitude']), establishmentlatitude, establishmentlongitude)

        # Validating Geo-Mapping
        if distance > establishmentattendanceradius:

            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_GEOMAPPING']]
            }

            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        try:
            attendancerecord = EstablishmentGuardAttendanceRecord.objects.filter(
                establishment_guard=establishment_guard,
                sign_in_time__date=date.today()
            ).order_by(
                '-sign_in_time__date'
            )
        except EstablishmentGuardAttendanceRecord.DoesNotExist:
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        else:
            # All the validation before the Check-Out

            # If user is trying to Check-Out again
            if (attendancerecord.first().sign_out_location) and (attendancerecord.first().sign_out_time) and (attendancerecord.first().sign_out_device_id) and (attendancerecord.first().sign_out_image):

                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['REPEATED_CHECKOUT']]
                }

                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

            # Save location

            # manually add 'address' key data as Attendance Address as that key is defined as mendatory in model
            request.data['location']['address'] = get_global_values()['ATTENDANCE_ADDRESS']

            location_create_serializer = LocationCreateSerializer(data=request.data['location'])

            if location_create_serializer.is_valid():

                with transaction.atomic():

                    location_obj = location_create_serializer.save()

                    # Handling Device ID section

                    # Preparing body of the DeviceID
                    device_id_body = {
                        'device_id': request.data['device_id']
                    }

                    device_id_create_serializer = DeviceIdSerializer(data=device_id_body)

                    if device_id_create_serializer.is_valid():

                        device_id_obj = device_id_create_serializer.save()

                        # Actual updating the AttendanceRecord record, once all validation pass

                        # Preparing the request_body
                        request_body = {
                            'sign_out_location': location_obj.id,
                            'sign_out_device_id': device_id_obj
                            .id,
                            'sign_out_image': request.data['sign_out_image'],
                            'sign_out_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }

                        attendance_record_checkout_serializer = EstablishmentGuardAttendanceRecordSerializer(attendancerecord.first(), data=request_body, partial=True)

                        if attendance_record_checkout_serializer.is_valid():

                            attendance_record_checkout_serializer.save()

                            return_data = {
                                'location': location_create_serializer.data,
                                'device': device_id_create_serializer.data,
                                'attendance': attendance_record_checkout_serializer.data,
                                'attendance_status': get_global_success_messages()['CHECKOUT_DONE'],
                                'is_checkin' : False,
                                'is_checkout' : True
                            }

                            return get_response_schema(return_data, get_global_success_messages()['USER_CHECKOUT'], status.HTTP_200_OK)

                        # AttendanceRecordCheckOut serializer errors
                        # Rollback the transaction
                        transaction.set_rollback(True)
                        return_data = {
                            settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                            get_global_values()['ERROR_KEY']: attendance_record_checkout_serializer.errors
                        }

                        return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

                    # DeviceIdSerializer serialzer erros
                    # Rollback the transaction
                    transaction.set_rollback(True)
                    return_data = {
                        settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                        get_global_values()['ERROR_KEY']: device_id_create_serializer.errors
                    }

                    return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

            # LocationCreateSerializer serialzer erros
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_LOCATION']],
                get_global_values()['ERROR_KEY']: location_create_serializer.errors
            }

            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
# End AttendanceRecord CheckOut view


# Start Check Attendance Status view
class AttendanceCurrentStatus(GenericAPIView):
    """ View: Current status of the Attendance """

    authentication_classes = [JWTAuthentication]

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):

        permission_role_list = [get_global_values()['SECURITY_GUARD_ROLE_ID']]

        permissions = does_permission_exist(permission_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating 'is_active' is True or not for Establishment Guard
        if permissions[str(get_global_values()['SECURITY_GUARD_ROLE_ID'])]:
            valid_record_status = check_valid_establishment_guard_record(request.user)

            if not valid_record_status['allowed']:
                return_data = {
                    'no_valid_record': True
                }
                return get_response_schema(return_data, get_global_error_messages()['NOT_VALID_ESTABLISHMENT_GUARD_RECORD'], status.HTTP_200_OK)

        establishment_guard = valid_record_status['establishment_guard']

        attendance_status = attendance_marked_status(establishment_guard)

        return get_response_schema(attendance_status, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)
# End Check Attendance Status view
