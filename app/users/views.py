# Package imports
from django.conf import settings
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView, ListAPIView
from django.contrib.auth import (
    login, 
    get_user_model,
)
from rest_framework_simplejwt.tokens import RefreshToken
import base64
import pyotp
import os
from django.db import transaction
from rest_framework.response import Response

# View imports
from app.core.views import (
    CustomPageNumberPagination,
)

# Serializer imports
from app.users.serializers import (
    UserDisplayLoginSerializer,
    UserDisplaySerializer,
    UserCreateSerializer,
    UserDetailCreateSeializer,
    UserUpdateSerializer,
)
from app.establishment.serializers import (
    EstablishmentAdminCreateSeializer,
    ManagementCommitteeCreateSeializer,
    EstablishmentGuardCreateSeializer,
    FlatMemberCreateSeializer
)

# Model imports
from app.core.models import (
    Organization,
    UserDetail,
    Establishment,
    FlatMember,
    Flat,
    EstablishmentGuard,
    ManagementCommittee,
    EmployeeCategory
)

# Utility imports
from app.utils import (
    GenerateKey,
    get_response_schema,
    get_global_error_messages,
    get_global_success_messages,
    save_current_token,
    get_global_values,
    get_allowed_user_roles_for_create_user,
    get_list_intersection,
    get_current_flat,
    check_valid_management_committee_record
)
from app.permissions import (
    does_permission_exist
)

# Custom schema in swagger
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# Start authorization views
class GenerateOTPLoginView(GenericAPIView):
    """ View: Generate OTP Login View """

    def get_object(self, phone, request):
        user_queryset = get_user_model().objects.filter(
            phone=phone,
            is_active=True
        ).only(
            'otp_counter'
        )
        if user_queryset:
            return user_queryset[0]
        return None

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    )
    def post(self, request):

        phone = request.data['phone']

        user = self.get_object(phone, request)

        if user == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        try:
            user.otp_counter += 1

            user.save()

            otp_counter = user.otp_counter

            key_generation = GenerateKey()

            # Encoded string that will be used to create TOTP model
            # Used otp_counter based logic so each time new OTP will be generated eventhough previous one was not expired.
            key = base64.b32encode(key_generation.returnBaseString(phone, otp_counter).encode())
            print("➡ otp_counter :", otp_counter)

            OTP = pyotp.TOTP(key, digits = 6, interval = float(os.environ.get('OTP_EXPIRY_TIME')))
            print("➡ OTP :", float(os.environ.get('OTP_EXPIRY_TIME')))
            print("➡ OTP :", key)

            return_data = {
                'otp': str(OTP.now())
            }

            return get_response_schema(return_data, get_global_success_messages()['OTP_GENERATED'], status.HTTP_200_OK)
        except Exception as e:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class VerifyOTPLoginView(GenericAPIView):
    """ View: Verify OTP Login View """

    def get_object(self, phone, request):
        user_queryset = get_user_model().objects.prefetch_related(
            'user_details__user_employee_categories'
        ).filter(
            phone=phone,
            is_active=True
        )
        if user_queryset:
            return user_queryset[0]
        return None

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone': openapi.Schema(type=openapi.TYPE_STRING),
                'otp': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    )
    def post(self, request):

        phone = request.data['phone']

        user = self.get_object(phone, request)

        if user == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        try:
            otp_counter = user.otp_counter

            key_generation = GenerateKey()

            # Encoded string that will be used to create TOTP model
            # Used otp_counter based logic so each time new OTP will be generated eventhough previous one was not expired.
            key = base64.b32encode(key_generation.returnBaseString(phone, otp_counter).encode())
            print("➡ key :", key)
            print("➡ otp_counter :", otp_counter)

            OTP = pyotp.TOTP(key, digits = 6, interval = float(os.environ.get('OTP_EXPIRY_TIME')))

            print(str(OTP.now()))
            print("➡ request.data :", request.data)
            if OTP.verify(request.data['otp']):
                login(request, user)

                # Save the Device Token for Push Notification
                try:
                    push_notification_token_obj = save_current_token(user, request.data['current_token'])

                    current_token = push_notification_token_obj.current_token
                except:
                    current_token = None

                # Get token details
                refresh = RefreshToken.for_user(user)

                # Get user details
                user_data = UserDisplayLoginSerializer(user)

                return_data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': user_data.data,
                    'current_token': current_token
                }

                return get_response_schema(return_data, get_global_success_messages()['CREDENTIALS_MATCHED'], status.HTTP_200_OK)
            
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['OTP_MISMATCH']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class CustomLogoutView(GenericAPIView):
    """ View: Custom User Logout """

    authentication_classes = [JWTAuthentication,]
    permission_classes = [IsAuthenticated,]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type='object',
            properties={
                'refresh_token': openapi.Schema(type='string')
            }
        )
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return get_response_schema({}, get_global_success_messages()['CREDENTIALS_REMOVED'], status.HTTP_200_OK)
        except:
            return get_response_schema({}, get_global_success_messages()['CREDENTIALS_REMOVED'], status.HTTP_200_OK)
# End authorization views


# Start temporary views
class SuperAdminUserSetup(GenericAPIView):
    """ View: Create the initial super admin user. Comment out after initial usage. """

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'phone': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'profile_image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64)
            },
        )
    )
    def post(self, request):

        request.data['role'] = [get_global_values()['SUPER_ADMIN_ROLE_ID']]

        serializer = UserCreateSerializer(data=request.data)

        if serializer.is_valid():

            serializer.save()

            return get_response_schema(serializer.data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

        return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
# End temporary views


# Start user management views
class UserCreate(GenericAPIView):
    """ View: Create User """

    authentication_classes = [JWTAuthentication,]
    permission_classes = [IsAuthenticated,]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'phone': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'profile_image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64),
                'role': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                ),
            },
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['SUPER_ADMIN_ROLE_ID'], get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'], get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'], get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        final_user_role_list = []

        if permissions[str(get_global_values()['SUPER_ADMIN_ROLE_ID'])]:
            allowed_roles = get_allowed_user_roles_for_create_user()['SUPER_ADMIN_ALLOWED_ROLE_IDS']

        if permissions[str(get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'])]:
            allowed_roles = get_allowed_user_roles_for_create_user()['ORGANIZATION_ADMINISTRATOR_ALLOWED_ROLE_IDS']

        if permissions[str(get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'])]:
            allowed_roles = get_allowed_user_roles_for_create_user()['ESTABLISHMENT_ADMIN_ALLOWED_ROLE_IDS']

            """ NOTE: - Management Committee can't be created directly in User Create Flow, first Resident User will be created then user will be linked with one of the valid Flat then user can be linked as Management Committee at that time their role will be updated as Management Commiittee """ 

            allowed_roles.remove(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])

        if permissions[str(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])]:

            # Validating 'is_active' is True or not for Management Committee
            flat_obj = get_current_flat(request.user)

            if not flat_obj:
                return_data = {
                    'no_current_flat': True
                }
                return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

            valid_record_status = check_valid_management_committee_record(request.user, flat_obj.building.establishment.id)

            if not valid_record_status['allowed']:
                return_data = {
                    'no_valid_record': True
                }
                return get_response_schema(return_data, get_global_error_messages()['NOT_VALID_MANAGEMENT_COMMITTEE_RECORD'], status.HTTP_200_OK)

            allowed_roles = get_allowed_user_roles_for_create_user()['MANAGEMENT_COMMITTEE_ALLOWED_ROLE_IDS']

        initial_roles = request.data['role']

        final_user_role_list = get_list_intersection(initial_roles, allowed_roles)

        # Check if the final organization type role list has elements in it
        if len(final_user_role_list) == 0:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: ['You must select atleast one valid role for this user.']
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        request.data['role'] = final_user_role_list

        serializer = UserCreateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return get_response_schema(serializer.data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

        return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class UserDetails(GenericAPIView):
    """ View: Retrieve, update or delete a User """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request, required_role_list):

        # Check role permissions
        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        user_queryset = get_user_model().objects.prefetch_related(
            'user_details__user_employee_categories',
            'user_roles'
        ).filter(
            pk=pk,
            is_active=True
        )

        is_self_requested_user=False

        # When User request them self
        if str(pk) == str(request.user.id):
            user_queryset = get_user_model().objects.select_related(
                'user_detail'
            ).prefetch_related(
                'user_details__employee_categories',
                'role'
            ).filter(
                pk=pk,
                is_active=True
            )

            is_self_requested_user=True

        # Query when Super Admin request for Organization Administrator role user
        elif (permissions[str(get_global_values()['SUPER_ADMIN_ROLE_ID'])]):

            user_queryset = user_queryset.filter(
                user_role__role__id__in=get_allowed_user_roles_for_create_user()['SUPER_ADMIN_ALLOWED_ROLE_IDS'],
                user_detail__organization__id__in=list(request.user.owned_organizations.all().values_list('id', flat=True))
            )

        # Query when Organization Administrator request for Employee role user
        elif (permissions[str(get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'])]):

            user_queryset = user_queryset.filter(user_role__role__id__in=get_allowed_user_roles_for_create_user()['ORGANIZATION_ADMINISTRATOR_ALLOWED_ROLE_IDS'])

        # Query when Establishment Admin request for Management Committee role user
        elif (permissions[str(get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'])]):

            user_queryset = user_queryset.filter(user_role__role__id__in=get_allowed_user_roles_for_create_user()['ESTABLISHMENT_ADMIN_ALLOWED_ROLE_IDS'])

        # Query when Management Committee request for Resident role user
        elif (permissions[str(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])]):

            user_queryset = user_queryset.filter(user_role__role__id__in=get_allowed_user_roles_for_create_user()['MANAGEMENT_COMMITTEE_ALLOWED_ROLE_IDS'])

        if user_queryset != None and user_queryset:
            permissions['model'] = user_queryset[0]
            permissions['is_self_requested_user'] = is_self_requested_user
            return permissions

        return None

    def get(self, request, pk=None):

        required_role_list = [ 
            get_global_values()['SUPER_ADMIN_ROLE_ID'], 
            get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'], 
            get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'], 
            get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'],  
            get_global_values()['SECURITY_GUARD_ROLE_ID'],  
            get_global_values()['RESIDENT_USERS_ROLE_ID'],  
            get_global_values()['EMPLOYEE_ROLE_ID'],  
        ]

        permissions = self.get_object(pk, request, required_role_list)

        if permissions == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        # Validating 'is_active' is True or not for Management Committee
        if permissions[str(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])]:

            flat_obj = get_current_flat(request.user)

            if not flat_obj:
                return_data = {
                    'no_current_flat': True
                }
                return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

            valid_record_status = check_valid_management_committee_record(request.user, flat_obj.building.establishment.id)

            if not valid_record_status['allowed']:
                return_data = {
                    'no_valid_record': True
                }
                return get_response_schema(return_data, get_global_error_messages()['NOT_VALID_MANAGEMENT_COMMITTEE_RECORD'], status.HTTP_200_OK)

        serializer = UserDisplaySerializer(permissions['model'])
        return get_response_schema(serializer.data, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'phone': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'profile_image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64),
                'role': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                ),
            },
        )
    )
    def patch(self, request, pk, format=None):

        with transaction.atomic():

            required_role_list = [ 
                get_global_values()['SUPER_ADMIN_ROLE_ID'], 
                get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'], 
                get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'], 
                get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'],  
                get_global_values()['SECURITY_GUARD_ROLE_ID'],  
                get_global_values()['RESIDENT_USERS_ROLE_ID'],  
                get_global_values()['EMPLOYEE_ROLE_ID'],  
            ]

            permissions = self.get_object(pk, request, required_role_list)

            if permissions == None:    
                return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

            # Validating 'is_active' is True or not for Management Committee
            if permissions[str(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])]:

                flat_obj = get_current_flat(request.user)

                if not flat_obj:
                    return_data = {
                        'no_current_flat': True
                    }
                    return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

                valid_record_status = check_valid_management_committee_record(request.user, flat_obj.building.establishment.id)

                if not valid_record_status['allowed']:
                    return_data = {
                        'no_valid_record': True
                    }
                    return get_response_schema(return_data, get_global_error_messages()['NOT_VALID_MANAGEMENT_COMMITTEE_RECORD'], status.HTTP_200_OK)

                allowed_roles = get_allowed_user_roles_for_create_user()['MANAGEMENT_COMMITTEE_ALLOWED_ROLE_IDS']

            # Retrive the model
            user = permissions['model']

            if str(pk) == str(request.user.id):
                allowed_roles = list(user.role.all().values_list('id', flat=True))

            elif permissions[str(get_global_values()['SUPER_ADMIN_ROLE_ID'])]:
                allowed_roles = get_allowed_user_roles_for_create_user()['SUPER_ADMIN_ALLOWED_ROLE_IDS']

            elif permissions[str(get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'])]:
                allowed_roles = get_allowed_user_roles_for_create_user()['ORGANIZATION_ADMINISTRATOR_ALLOWED_ROLE_IDS']

            elif permissions[str(get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'])]:
                allowed_roles = get_allowed_user_roles_for_create_user()['ESTABLISHMENT_ADMIN_ALLOWED_ROLE_IDS']

                """ NOTE: - Management Committee can't be created directly in User Create Flow, first Resident User will be created then user will be linked with one of the valid Flat then user can be linked as Management Committee at that time their role will be updated as Management Commiittee """ 

                allowed_roles.remove(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])

            try:
                initial_roles = request.data['role']

                final_user_role_list = get_list_intersection(initial_roles, allowed_roles)

                # Check if the final organization type role list has elements in it
                if len(final_user_role_list) == 0:
                    return_data = {
                        settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: ['You must select atleast one valid role for this user.']
                    }
                    return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
            except:
                final_user_role_list = []

            serializer = UserUpdateSerializer(user, data=request.data, context={'pk': pk, 'final_user_role_list': final_user_role_list, 'is_self_requested_user':permissions['is_self_requested_user']}, partial=True)

            if serializer.is_valid():
                serializer.save()

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

            return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        required_role_list = [ 
            get_global_values()['SUPER_ADMIN_ROLE_ID'], 
            get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'], 
            get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'],
        ]

        permissions = self.get_object(pk, request, required_role_list)

        if permissions == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        # Retrive the model
        user = permissions['model']

        user.is_active = False

        # Custom logic for preventing data loose
        # UserID + - + Old Email
        user.email = str(user.id) + "-" + user.email

        # UserID + add 0 for remaining places till phone number's length is 10
        user.phone = str(user.id) + "0"*(10 - len(str(user.id)))

        user.save()

        return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)


class UserList(GenericAPIView):
    """ View: List User (dropdown) """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('role', openapi.IN_QUERY, type=openapi.TYPE_INTEGER)
        ]
    )
    def get(self, request):

        # Check role permissions
        required_role_list = [ 
            get_global_values()['SUPER_ADMIN_ROLE_ID'],
            get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'],
            get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'],
            get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'],
        ]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        if not (request.query_params.get('role')):
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_RESPONSE']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        if permissions[str(get_global_values()['SUPER_ADMIN_ROLE_ID'])]:
            allowed_roles = get_allowed_user_roles_for_create_user()['SUPER_ADMIN_ALLOWED_ROLE_IDS']

        elif permissions[str(get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'])]:
            allowed_roles = get_allowed_user_roles_for_create_user()['ORGANIZATION_ADMINISTRATOR_ALLOWED_ROLE_IDS']

        elif permissions[str(get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'])]:
            allowed_roles = get_allowed_user_roles_for_create_user()['ESTABLISHMENT_ADMIN_ALLOWED_ROLE_IDS']

        elif permissions[str(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])]:

            flat_obj = get_current_flat(request.user)

            if not flat_obj:
                return_data = {
                    'no_current_flat': True
                }
                return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

            valid_record_status = check_valid_management_committee_record(request.user, flat_obj.building.establishment.id)

            if not valid_record_status['allowed']:
                return_data = {
                    'no_valid_record': True
                }
                return get_response_schema(return_data, get_global_error_messages()['NOT_VALID_MANAGEMENT_COMMITTEE_RECORD'], status.HTTP_200_OK)

            allowed_roles = get_allowed_user_roles_for_create_user()['MANAGEMENT_COMMITTEE_ALLOWED_ROLE_IDS']

        if int(request.query_params.get('role')) not in allowed_roles:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_REQUESTED_ROLE']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        queryset = get_user_model().objects.select_related(
            'user_detail'
        ).prefetch_related(
            'user_details__employee_categories',
            'role'
        ).filter(
            is_active=True,
            user_role__role__id__in=[int(request.query_params.get('role'))]
        ).order_by(
            'first_name',
            'last_name'
        )

        user_display_serializer = UserDisplaySerializer(queryset, many=True)

        return Response(user_display_serializer.data, status=status.HTTP_200_OK)


class UserListFilter(ListAPIView):
    """ View: List User Filter """

    serializer_class = UserDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [ 
            get_global_values()['SUPER_ADMIN_ROLE_ID'],
            get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'],
            get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'],
            get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'],
        ]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        if permissions[str(get_global_values()['SUPER_ADMIN_ROLE_ID'])]:
            allowed_roles = get_allowed_user_roles_for_create_user()['SUPER_ADMIN_ALLOWED_ROLE_IDS']

        elif permissions[str(get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'])]:
            allowed_roles = get_allowed_user_roles_for_create_user()['ORGANIZATION_ADMINISTRATOR_ALLOWED_ROLE_IDS']

        elif permissions[str(get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'])]:
            allowed_roles = get_allowed_user_roles_for_create_user()['ESTABLISHMENT_ADMIN_ALLOWED_ROLE_IDS']

        elif permissions[str(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])]:

            flat_obj = get_current_flat(self.request.user)

            if not flat_obj:
                return []

            valid_record_status = check_valid_management_committee_record(self.request.user, flat_obj.building.establishment.id)

            if not valid_record_status['allowed']:
                return []

            allowed_roles = get_allowed_user_roles_for_create_user()['MANAGEMENT_COMMITTEE_ALLOWED_ROLE_IDS']

        queryset = get_user_model().objects.select_related(
            'user_detail'
        ).prefetch_related(
            'user_details__employee_categories',
            'role'
        ).filter(
            is_active=True,
            user_role__role__id__in=allowed_roles
        ).order_by(
            'first_name',
            'last_name'
        )

        if self.request.query_params.get('role'):
            if int(self.request.query_params.get('role')) not in allowed_roles:
                return []
            queryset = queryset.filter(user_role__role__id__in=[self.request.query_params.get('role')])

        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('role', openapi.IN_QUERY, type=openapi.TYPE_INTEGER)
        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
# End user management views


# Start Organization Administrator linking views
class OrganizationAdministratorLinkingCreate(GenericAPIView):
    """ View: Create OrganizationAdministratorLinking """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                'organization': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['SUPER_ADMIN_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating Organization ID
        organization_queryset = Organization.objects.filter(
            pk=request.data['organization'],
            owner_user=request.user,
            is_active=True
        )

        # Validating User ID
        user_queryset = get_user_model().objects.filter(
            pk=request.data['user'],
            is_active=True,
            user_role__role__id__in=[get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]
        )

        if organization_queryset and user_queryset:

            serializer = UserDetailCreateSeializer(data=request.data)

            if serializer.is_valid():
                serializer.save()

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

            else:
                # UserDetailCreateSeializer serializer errors
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                    get_global_values()['ERROR_KEY']: serializer.errors
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class OrganizationAdministratorLinkingDetail(GenericAPIView):
    """ View: Delete a Organization Administrator linking """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        # Check role permissions
        required_role_list = [get_global_values()['SUPER_ADMIN_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating User ID with direct Linking model
        user_details_queryset = UserDetail.objects.filter(
            user__id=pk,
            organization__owner_user=request.user,
            organization__is_active=True,
        )

        if user_details_queryset:

            user_details_queryset.first().delete()

            return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)
        else:
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)
# End Organization Administrator linking views


# Start Employee linking views
class EmployeeLinkingCreate(GenericAPIView):
    """ View: Create EmployeeLinking """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating User ID
        user_queryset = get_user_model().objects.filter(
            pk=request.data['user'],
            is_active=True,
            user_role__role__id__in=[get_global_values()['EMPLOYEE_ROLE_ID']]
        )

        if user_queryset:

            request.data['organization'] = request.user.user_details.organization.id

            serializer = UserDetailCreateSeializer(data=request.data)

            if serializer.is_valid():
                serializer.save()

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

            else:
                # UserDetailCreateSeializer serializer errors
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                    get_global_values()['ERROR_KEY']: serializer.errors
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class EmployeeLinkingDetail(GenericAPIView):
    """ View: Delete a Employee linking """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating User ID with direct Linking model
        user_details_queryset = UserDetail.objects.filter(
            user__id=pk,
            organization=request.user.user_details.organization,
            organization__is_active=True,
        )

        if user_details_queryset:

            user_details_queryset.first().delete()

            return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)
        else:
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)
# End Employee linking views


# Start Establishment Admin linking views
class EstablishmentAdminLinkingCreate(GenericAPIView):
    """ View: Create EstablishmentAdminLinking """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                'establishment': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating User ID
        user_queryset = get_user_model().objects.filter(
            pk=request.data['user'],
            is_active=True,
            user_role__role__id__in=[get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID']]
        )

        # Validating Establishment ID
        establishment_queryset = Establishment.objects.filter(
            pk=request.data['establishment'],
            is_active=True,
            owner_organization=request.user.user_details.organization
        )

        if user_queryset and establishment_queryset:

            request_data = {
                'establishment_admin': request.data['user']
            }

            serializer = EstablishmentAdminCreateSeializer(establishment_queryset.first(), data=request_data)

            if serializer.is_valid():

                serializer.save()

                return_data = request.data

                return get_response_schema(return_data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

            else:
                # EstablishmentAdminCreateSeializer serializer errors
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                    get_global_values()['ERROR_KEY']: serializer.errors
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class EstablishmentAdminLinkingDetail(GenericAPIView):
    """ View: Delete a EstablishmentAdmin linking """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating Establishment ID
        establishment_queryset = Establishment.objects.filter(
            pk=pk,
            is_active=True,
            owner_organization=request.user.user_details.organization
        )

        if establishment_queryset:

            establishment = establishment_queryset.first()

            establishment.establishment_admin = None

            establishment.save()

            return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)
        else:
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)
# End Establishment Admin linking views


# Start Resident User linking views
class ResidentUserLinking(GenericAPIView):
    """ View: Create and Remove ResidentUserLinking """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                'flat': openapi.Schema(type=openapi.TYPE_INTEGER),
                'member_role': openapi.Schema(type='string', enum=[FlatMember.MemberRole.OWNER_ROLE, FlatMember.MemberRole.TENANT_ROLE, FlatMember.MemberRole.FAMILY_MEMBER_ROLE]),
            }
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'], get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating 'is_active' is True or not for Management Committee
        if permissions[str(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])]:

            flat_obj = get_current_flat(request.user)

            if not flat_obj:
                return_data = {
                    'no_current_flat': True
                }
                return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

            valid_record_status = check_valid_management_committee_record(request.user, flat_obj.building.establishment.id)

            if not valid_record_status['allowed']:
                return_data = {
                    'no_valid_record': True
                }
                return get_response_schema(return_data, get_global_error_messages()['NOT_VALID_MANAGEMENT_COMMITTEE_RECORD'], status.HTTP_200_OK)

        # Validating User ID
        user_queryset = get_user_model().objects.filter(
            pk=request.data['user'],
            is_active=True,
            user_role__role__id__in=[get_global_values()['RESIDENT_USERS_ROLE_ID']]
        )

        # Validating Flat ID
        if permissions[str(get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'])]:

            flat_queryset = Flat.objects.filter(
                pk=request.data['flat'],
                is_active=True,
                building__establishment__establishment_admin=request.user
            )

        elif permissions[str(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])]:

            flat_queryset = Flat.objects.filter(
                pk=request.data['flat'],
                is_active=True,
                building__establishment=flat_obj.building.establishment
            )

        if user_queryset and flat_queryset:

            serializer = FlatMemberCreateSeializer(data=request.data)

            if serializer.is_valid():

                serializer.save()

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

            else:
                # FlatMemberCreateSeializer serializer errors
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                    get_global_values()['ERROR_KEY']: serializer.errors
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                'flat': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )
    def delete(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'], get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating 'is_active' is True or not for Management Committee
        if permissions[str(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])]:

            flat_obj = get_current_flat(request.user)

            if not flat_obj:
                return_data = {
                    'no_current_flat': True
                }
                return get_response_schema(return_data, get_global_error_messages()['CURRENT_FLAT_NOT_FOUND'], status.HTTP_200_OK)

            valid_record_status = check_valid_management_committee_record(request.user, flat_obj.building.establishment.id)

            if not valid_record_status['allowed']:
                return_data = {
                    'no_valid_record': True
                }
                return get_response_schema(return_data, get_global_error_messages()['NOT_VALID_MANAGEMENT_COMMITTEE_RECORD'], status.HTTP_200_OK)

        # Validating Flat member ID
        if permissions[str(get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID'])]:

            flat_member_queryset = FlatMember.objects.filter(
                is_active=True,
                flat__id=request.data['flat'],
                flat__is_active=True,
                flat__building__establishment__establishment_admin=request.user,
                user__id=request.data['user']
            )

        elif permissions[str(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])]:

            flat_member_queryset = FlatMember.objects.filter(
                is_active=True,
                flat__id=request.data['flat'],
                flat__is_active=True,
                flat__building__establishment=flat_obj.building.establishment,
                user__id=request.data['user']
            )

        if flat_member_queryset:

            flat_member = flat_member_queryset.first()

            flat_member.is_active=False

            flat_member.save()

            return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)
        else:
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)
# End Establishment Admin linking views


# Start Establishment Guard linking views
class EstablishmentGuardLinkingCreate(GenericAPIView):
    """ View: Create EstablishmentGuardLinking """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                'establishment': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating User ID
        user_queryset = get_user_model().objects.filter(
            pk=request.data['user'],
            is_active=True,
            user_role__role__id__in=[get_global_values()['SECURITY_GUARD_ROLE_ID']]
        )

        # Validating Establishment ID
        establishment_queryset = Establishment.objects.filter(
            pk=request.data['establishment'],
            is_active=True,
            establishment_admin=request.user
        )

        # Checking if user was linked with requested establishment previsously or not if yes then simply make is_acitve=True

        establishment_guard_queryset = EstablishmentGuard.objects.filter(
            user__id=request.data['user'],
            establishment__id=request.data['establishment'],
            is_active=False
        )

        if establishment_guard_queryset:

            establishment_guard = establishment_guard_queryset.first()

            establishment_guard.is_active = True

            establishment_guard.save()

            return_data = request.data

            return get_response_schema(return_data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

        # Validating if same user is linked in another Establishment with is_active
        establishment_guard_queryset = EstablishmentGuard.objects.filter(
            user__id=request.data['user'],
            is_active=True
        )

        if (user_queryset) and (establishment_queryset) and (not establishment_guard_queryset):

            serializer = EstablishmentGuardCreateSeializer(data=request.data)

            if serializer.is_valid():

                serializer.save()

                return_data = request.data

                return get_response_schema(return_data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

            else:
                # EstablishmentGuardCreateSeializer serializer errors
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                    get_global_values()['ERROR_KEY']: serializer.errors
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class EstablishmentGuardLinkingDetail(GenericAPIView):
    """ View: Delete a EstablishmentAdmin linking """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        # Check role permissions
        required_role_list = [get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating User ID
        establishment_guard_queryset = EstablishmentGuard.objects.filter(
            user__id=pk,
            establishment__establishment_admin=request.user,
            is_active=True
        )

        if establishment_guard_queryset:

            establishment_guard = establishment_guard_queryset.first()

            establishment_guard.is_active = False

            establishment_guard.save()

            return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)
        else:
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)
# End Establishment Guard linking views


# Start Management Committee linking views
class ManagementCommitteeLinking(GenericAPIView):
    """ View: Create and Remove ManagementCommitteeLinking """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                'establishment': openapi.Schema(type=openapi.TYPE_INTEGER),
                'committee_role': openapi.Schema(type='string', enum=[ManagementCommittee.ManagementRole.CHAIRMAN_ROLE, ManagementCommittee.ManagementRole.SECRETARY_ROLE, ManagementCommittee.ManagementRole.TREASURER_ROLE]),
            }
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating User ID
        user_queryset = get_user_model().objects.filter(
            pk=request.data['user'],
            is_active=True,
            user_role__role__id__in=[get_global_values()['RESIDENT_USERS_ROLE_ID']],
            flat__flat__building__establishment__id=request.data['establishment']
        )

        # Validating Establishment ID
        establishment_queryset = Establishment.objects.filter(
            pk=request.data['establishment'],
            is_active=True,
            building__establishment__establishment_admin=request.user
        )

        # Validating if same user is linked with same Establishment or not

        if (user_queryset) and (establishment_queryset):

            serializer = ManagementCommitteeCreateSeializer(data=request.data)

            if serializer.is_valid():

                with transaction.atomic():

                    serializer.save()

                    user_obj = user_queryset.first()

                    user_role_list = list(user_obj.role.all().values_list('id', flat=True))

                    user_role_list.append(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])

                    try:
                        user_obj.role.set(user_role_list)
                    except:
                        # Rollback the transaction
                        transaction.set_rollback(True)

                        return_data = {
                            settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
                        }

                        return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

                    return get_response_schema(serializer.data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

            else:
                # ManagementCommitteeCreateSeializer serializer errors
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                    get_global_values()['ERROR_KEY']: serializer.errors
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                'establishment': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )
    def delete(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ESTABLISHMENT_ADMIN_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating Management Committee ID
        management_committee_queryset = ManagementCommittee.objects.filter(
            is_active=True,
            user__id=request.data['user'],
            user__user_role__role__id__in=[get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID']],
            user__flat__flat__building__establishment__id=request.data['establishment'],
            establishment__id=request.data['establishment'],
            establishment__establishment_admin=request.user
        )

        if management_committee_queryset:

            with transaction.atomic():

                management_committee = management_committee_queryset.first()

                management_committee.is_active=False

                management_committee.save()

                user_obj = management_committee.user

                user_role_list = list(user_obj.role.all().values_list('id', flat=True))

                user_role_list.remove(get_global_values()['MANAGEMENT_COMMITTEE_ROLE_ID'])

                try:
                    user_obj.role.set(user_role_list)
                except:
                    # Rollback the transaction
                    transaction.set_rollback(True)

                    return_data = {
                        settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
                    }

                    return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

                return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)
        else:
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)
# End Management Committee linking views


# Start UserEmployeeCategory views
class UserEmployeeCategoryCreate(GenericAPIView):
    """ View: Create UserEmployeeCategory """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                'employee_categories': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                )
            }
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Check if all records are valid
        selected_employee_categories = request.data['employee_categories']

        employee_category_queryset = EmployeeCategory.objects.filter(
            organization=request.user.user_details.organization,
            organization__is_active=True,
            pk__in=selected_employee_categories
        )

        latest_employee_categories = [employee_category.pk for employee_category in employee_category_queryset]

        user_detail_queryset = UserDetail.objects.filter(
            user__id=request.data['user'],
            user__is_active=True,
            user__user_role__role__id__in=[get_global_values()['EMPLOYEE_ROLE_ID']],
            organization=request.user.user_details.organization,
            organization__is_active=True
        )

        if user_detail_queryset:

            user_detail_queryset[0].user_employee_categories.set(latest_employee_categories)

            return_data = {
                'user' : user_detail_queryset[0].user.id,
                'employee_categories' : latest_employee_categories
            }
            return get_response_schema(return_data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_M2M_TRANSACTION']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class UserEmployeeCategoryDetail(GenericAPIView):
    """ View: Retrieve UserEmployeeCategory """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):

        user_detail_queryset = UserDetail.objects.prefetch_related(
            'user__role',
            'user_employee_categories'
        ).filter(
            user__id=pk,
            user__is_active=True,
            user__user_role__role__id__in=[get_global_values()['EMPLOYEE_ROLE_ID']],
            organization=request.user.user_details.organization,
            organization__is_active=True
        )

        if user_detail_queryset:
            return user_detail_queryset[0]
        return None

    def get(self, request, pk=None):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        user_detail = self.get_object(pk, request)

        if user_detail == None:
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        return_data = {
            'user' : UserDisplaySerializer(user_detail.user).data,
            'employee_categories' : list(user_detail.user_employee_categories.all().values_list('id', flat=True))
        }

        return get_response_schema(return_data, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)
# End UserEmployeeCategory views
