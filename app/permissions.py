# Model imports
from app.core.models import (
    UserRole,
)


def does_permission_exist(required_role_list, user_id):
    """ To check Role based permisison of the user """

    # Setup the return structure
    permissions = {
        'allowed': False
    }

    # Dynamically add the required permissions to the return structure
    for role in required_role_list:
        permissions['' + str(role)] = False

    # Run query to find user roles
    user_role_queryset = UserRole.objects.filter(
        user_id=user_id
    ).values(
        'role_id'
    )

    if user_role_queryset:

        user_role_list = [i['role_id'] for i in user_role_queryset]

        # Check for common roles
        common_roles = set(user_role_list).intersection(required_role_list)

        if len(common_roles) > 0:
            permissions['allowed'] = True

            for common_role in common_roles:
                permissions['' + str(common_role)] = True
    
    return permissions
