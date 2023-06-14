# Package imports
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

# Serializer imports
from app.role.serializers import (
    RoleDisplaySerializer,
)

# Model imports
from app.core.models import (
    Role
)

# Utility imports
from app.utils import (
    get_response_schema,
    get_global_error_messages,
    get_global_values,
    get_allowed_user_roles_for_create_user,
    get_current_flat,
    check_valid_management_committee_record
)
from app.permissions import (
    does_permission_exist
)


class RoleList(GenericAPIView):
    """ View: List Role (dropdown) """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

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

        queryset = Role.objects.filter(
            pk__in=allowed_roles
        ).order_by(
            'pk'
        )

        role_display_serializer = RoleDisplaySerializer(queryset, many=True)

        return Response(role_display_serializer.data, status=status.HTTP_200_OK)
