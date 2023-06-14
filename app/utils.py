# Package imports
from rest_framework.response import Response
import requests
import json
import environ
from datetime import date
from django.utils import timezone

# For distance calculation
from math import(
    radians,
    sin,
    cos,
    sqrt,
    atan2,
)

env = environ.Env()
environ.Env.read_env()

# Model imports 
from app.core.models import (
    PushNotificationToken,
    ManagementCommittee,
    EstablishmentGuard,
    EstablishmentGuardAttendanceRecord,
)


def get_global_success_messages():
    """ Utility: Get global success messages """

    data = {
        'CREDENTIALS_MATCHED': 'Login successful.',
        'CREDENTIALS_REMOVED': 'Logout successful.',
        'RECORD_RETRIEVED': 'The record was successfully retrieved.',
        'RECORD_CREATED': 'The record was successfully created.',
        'RECORD_UPDATED': 'The record was successfully updated.',
        'RECORD_DELETED': 'The record was successfully deleted.',
        'OTP_GENERATED': 'The otp has been sent to your phone successfully.',
        'CURRENT_FLAT_UPDATED': 'Your active flat has been successfully selected.',

        'USER_CHECKIN': 'The user was successfully checked-in.',
        'USER_CHECKOUT': 'The user was successfully checked-out.',

        'CHECKIN_NOT_DONE': 'Check-in has not been done for today.',
        'CHECKIN_DONE': 'Check-in has been done for today.',
        'CHECKOUT_DONE': 'Check-out has been done for today.',

        'SERVICE_REQUEST': 'Service Request.',
        'STATUS_UPDATED': 'Service Request status updated.',
        'REQUEST_ASSIGNED': 'Service Request assigned.',
        'EMPLOYEE_ASSIGNED': 'Employee assigned.',
        'SERVICE_REQUEST_MARKED_COMPLETED': 'Service request completed.',
    }   
    return data


def get_global_error_messages():
    """ Utility: Get global error messages """

    data = {
        'OTP_MISMATCH': 'OTP did not matched. Please try again.',
        'BAD_REQUEST': 'Bad request.',
        'NOT_FOUND': 'Resource not found.',
        'FORBIDDEN': 'Not authenticated.',
        'RATING_VALIDATION': 'The rating must be between 0 and 10.',
        'INVALID_END_DATE': 'The end date must be after the start date.',
        'INVALID_END_TIME': 'The end time must be after the start time.',
        'INVALID_ESTIMATED_CHECK_IN_DATE_TIME': 'The estimated check-in date time must not be in past.',
        'INVALID_DAY_OF_WEEK': 'The day of week must be less than 7.',
        'INVALID_ADDRESS': 'The address provided does not appear to be valid. Please try again.',
        'INVALID_LOCATION': 'The location provided does not appear to be valid. Please select another location and try again.',
        'INVALID_RESPONSE': 'The detail submitted does not appear to be valid. Please try again.',
        'INVALID_M2M_TRANSACTION': 'Something went wrong. Please try again.',
        'INVALID_ROLE_SELECTION': 'You have selected roles that are not permitted.',
        'INVALID_QUERY': 'Something went wrong. No data found. Please try again.',
        'PERMISSION_DENIED': 'You are not allowed to access this record.',
        'INVALID_VALUE_MSG': 'The value provided is not valid.',
        'DUPLICATE_RECORD': 'The record that you are attempting to create already exists.',
        'INVALID_DATE_TIME': 'Invalid date and time format.',
        'CURRENT_FLAT_NOT_FOUND': 'Current flat is not selected.',
        'NOT_VALID_ESTABLISHMENT_GUARD_RECORD': 'You are not an active establishment guard user.',
        'INVALID_LOCATION': 'The location provided does not appear to be valid. Please select another location and try again.',
        'INVALID_GEOMAPPING': 'You are not at the required establishment\'s location.',
        'INVALID_CHECKIN': 'Please check-out first before you check-in again.',
        'REPEATED_CHECKIN': 'You are not allowed to check-in again for the day.',
        'REPEATED_CHECKOUT': 'You are not allowed to check-out again for the day.',
        'CHECKIN_REQUIRED': 'Please do check-in to perform this operation.',
        'INVALID_EXCLUSION_DATE': 'The exclusion date must not be in past.',
        'INVALID_REQUESTED_DATE': 'The organization is not working on requested date.',
        'INVALID_REQUESTED_TIME': 'The organization is not available on requested time.',
        'NO_SLOTS': 'There is no slots for requested service.',
        'PAST_DATE': 'You can not request on the past date.',
        'INVALID_RATING': 'The rating must be between 1 and 5.',
        'INVALID_REQUESTED_ROLE': 'The requested role is not valid.',
        'SOMETHING_WENT_WRONG': 'Something went wrong. Please try again.',
    }
    return data


def get_global_values():
    """ Utility: Get global values """

    data = {
        'SUPER_ADMIN_ROLE_ID': 1,
        'ORGANIZATION_ADMINISTRATOR_ROLE_ID': 2,
        'ESTABLISHMENT_ADMIN_ROLE_ID': 3,
        'MANAGEMENT_COMMITTEE_ROLE_ID': 4,
        'SECURITY_GUARD_ROLE_ID': 5,
        'RESIDENT_USERS_ROLE_ID': 6,
        'EMPLOYEE_ROLE_ID': 7,

        'M2M_ERRORS_KEY': 'M2M_errors',
        'ERROR_KEY': 'errors',

        'REQUEST_TAB': 'request',
        'UPCOMING_TAB': 'upcoming',
        'PAST_TAB': 'past',
        'ATTENDANCE_ADDRESS': 'attendance address',

        'CURRENCY': 'INR',
        'SERVICE_REQUEST_OBJECT_ID': 'service_request_obj_id',

        # Tabs filter in Amenity Booking List Records
        'UPCOMING': 'Upcoming',
        'PAST': 'Past',
        'REJECTED': 'Rejected',

        # Tabs filter in Bill Payment List Records
        'OVERDUE': 'Overdue',
    }   
    return data


def get_allowed_user_roles_for_create_user():
    """ Utility: User roles that are allowed to while creating a user """

    data = {
        'SUPER_ADMIN_ALLOWED_ROLE_IDS': [2],
        'ORGANIZATION_ADMINISTRATOR_ALLOWED_ROLE_IDS': [3, 7],
        'ESTABLISHMENT_ADMIN_ALLOWED_ROLE_IDS': [4, 5, 6],
        'MANAGEMENT_COMMITTEE_ALLOWED_ROLE_IDS': [6],
        'SECURITY_GUARD_ALLOWED_ROLE_IDS': [],
        'RESIDENT_USERS_ALLOWED_ROLE_IDS': [],
        'EMPLOYEE_ROLE_ALLOWED_ROLE_IDS': [],
    }   
    return data


def get_response_schema(schema, message, status_code):
    """ Utility: Standard response structure """
    
    return Response({
        'message': message,
        'status': status_code,
        'results': schema,
    }, status=status_code)


def get_list_difference(list1, list2):
    """ Utility: Get elements which are in list1 but not in list2 """
    
    return list(set(list1) - set(list2))


def get_list_intersection(list1, list2):
    return list(set(list1).intersection(list2))


def save_current_token(user,current_token):
    """ Utility: Save device Token in its respective model """
    
    currentToken = current_token
    
    deviceId = 'device_id'
    
    push_notification_token_obj, _ = PushNotificationToken.objects.get_or_create(user=user)
    
    push_notification_token_obj.device_id = deviceId
    
    push_notification_token_obj.current_token = currentToken
    
    push_notification_token_obj.save()

    return push_notification_token_obj


def send_notification(user,message_title,message_desc):
    """ Utility: Send Notification to the User """

    fcm_api = env('FCM_TOKEN')
    url = "https://fcm.googleapis.com/fcm/send"
    
    headers = {
        "Content-Type":"application/json",
        "Authorization": 'key='+fcm_api
    }
    
    try:
        user_token = PushNotificationToken.objects.get(user=user).current_token
    except Exception as e:
        return None
    
    registratred_device = [user_token]
    
    payload = {
        "registration_ids" :registratred_device,
        "priority" : "high",
        "notification" : {
            "body" : message_desc,
            "title" : message_title,
            "image" : "",
            "icon": "https://static.vecteezy.com/system/resources/previews/010/366/202/original/bell-icon-transparent-notification-free-png.png",
        }
    }

    result = requests.post(url,  data=json.dumps(payload), headers=headers )

    return result


class GenerateKey:
    """ Utility: For generating dynamic OTP """

    @staticmethod
    def returnBaseString(phone, counter):
        """ Generating a symmetric string using phone, otp_counter and other things to use in OTP generation logic """
        return str(phone) + str(date.today()) + "SeccdzeKey" + str(counter)


def get_current_flat(user_obj):
    """ Utility: Give current selected flat object """

    flat_member_queryset = user_obj.flats.filter(
        is_active=True,
        is_current_flat=True
    ).select_related(
        'flat__building',
        'flat__building__establishment'
    )

    if flat_member_queryset.exists():
        return flat_member_queryset.first().flat
    return None


def check_valid_management_committee_record(user_obj, establishment_id):
    """ Utility: Check valid entry for the Management Committee """

    management_committee_queryset = ManagementCommittee.objects.filter(
        user=user_obj,
        establishment__id=establishment_id,
        is_active=True
    )

    status = {
        'allowed': False
    }

    if management_committee_queryset:
        status['allowed'] = True

        status['management_committee'] = management_committee_queryset.first()
        return status
    return status


def check_valid_establishment_guard_record(user_obj):
    """ Utility: Check valid entry for the Establishment Guard """

    establishment_guard_queryset = EstablishmentGuard.objects.select_related(
        'establishment'
    ).filter(
        user=user_obj,
        is_active=True
    )

    status = {
        'allowed': False
    }

    if establishment_guard_queryset.exists():
        status['allowed'] = True

        status['establishment_guard'] = establishment_guard_queryset.first()

        return status

    return status


def distance_in_meter(lat1, lon1, lat2, lon2):
    """ Utility: Find the distance between 2 points """

    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1

    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2

    c = 2 * atan2(sqrt(a), sqrt(1-a))

    R = 6371  # Radius of the Earth in kilometers

    distance = R * c

    # To return the output in meters
    return distance * 1000


def attendance_marked_status(establishment_guard):
    """ Utility: Check if user has done checked in or not """

    attendancerecord = EstablishmentGuardAttendanceRecord.objects.filter(
        establishment_guard=establishment_guard,
        sign_in_time__date=date.today()
    )

    if attendancerecord.exists():

        attendance = attendancerecord.first()

        if (not attendance.sign_out_location) and (not attendance.sign_out_time) and (not attendance.sign_out_device_id) and (not attendance.sign_out_image):

            attendance_status = get_global_success_messages()['CHECKIN_DONE']

            is_checkout = False

            is_checkin = True

            sign_in_time = attendance.sign_in_time

            sign_out_time = attendance.sign_out_time

        elif (attendance.sign_out_location) and (attendance.sign_out_time) and (attendance.sign_out_device_id) and (attendance.sign_out_image):

            attendance_status = get_global_success_messages()['CHECKOUT_DONE']

            is_checkout = True

            is_checkin = False

            sign_in_time = attendance.sign_in_time

            sign_out_time = attendance.sign_out_time

    else:

        attendance_status = get_global_success_messages()['CHECKIN_NOT_DONE']

        is_checkout = False

        is_checkin = False

        sign_in_time = None

        sign_out_time = None

    return_data = {
        'attendance_status_msg' : attendance_status,
        'sign_in_time' : timezone.template_localtime(sign_in_time),
        'sign_out_time' : timezone.template_localtime(sign_out_time),
        'is_checkin' : is_checkin,
        'is_checkout' : is_checkout,
    }

    return return_data

def get_payable_service_request_amount(service, number_of_slots):
    """ Utility: Calculate amount for the service request """

    amount = int(service.price) * int(number_of_slots)

    return_data = {
        'amount': str(amount)
    }

    return return_data
