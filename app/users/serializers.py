# Package imports
from rest_framework import serializers
from django.contrib.auth import get_user_model
import re
from drf_extra_fields.fields import Base64ImageField

# Model imports
from app.core.models import (
    Role,
    UserDetail,
)

# Serializer imports
from app.role.serializers import (
    RoleDisplaySerializer,
)
from app.employeecategory.serializers import (
    EmployeeCategoryDisplaySerializer
)
from app.organization.serializers import (
    OrganizationDisplaySerializer
)

# Utility imports
from app.utils import get_global_error_messages


# Start validation helper functions
def validate_phone_helper(value, pk):
    """ Validate phone """

    if value:
        valid_phone = re.search('^[0-9]{10}$', value)
        if not valid_phone:
            raise serializers.ValidationError(get_global_error_messages()['INVALID_VALUE_MSG'])
        if pk == None:
            if get_user_model().objects.filter(phone=value, is_active=True).exists():
                raise serializers.ValidationError('user with this phone already exists.')
        else:
            if get_user_model().objects.filter(phone=value, is_active=True).exclude(pk=pk).exists():
                raise serializers.ValidationError('user with this phone already exists.')
        return value


def validate_email_helper(value, pk):
    """ Validate email """

    if value:
        updated_value = value.lower()
        if pk == None:
            if get_user_model().objects.filter(email=updated_value, is_active=True).exists():
                raise serializers.ValidationError('user with this email already exists.')
        else:
            if get_user_model().objects.filter(email=updated_value, is_active=True).exclude(pk=pk).exists():
                raise serializers.ValidationError('user with this email already exists.')
        return updated_value
    return None
# End validation helper functions


class UserDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: User Display """

    role = RoleDisplaySerializer(many=True)
    user_employee_categories = EmployeeCategoryDisplaySerializer(source='user_details.user_employee_categories', many=True)

    class Meta:
        model = get_user_model()
        fields = ('pk', 'phone', 'first_name', 'last_name', 'email', 'profile_image', 'otp_counter', 'created', 'modified', 'role', 'user_employee_categories',)


class UserDisplayLoginSerializer(serializers.ModelSerializer):
    """ Serializer: User Display For Login """

    role = RoleDisplaySerializer(many=True)
    user_employee_categories = EmployeeCategoryDisplaySerializer(source='user_details.user_employee_categories', many=True)
    organization = OrganizationDisplaySerializer(source='user_details.organization')

    class Meta:
        model = get_user_model()
        fields = ('pk', 'phone', 'first_name', 'last_name', 'email', 'profile_image', 'otp_counter', 'created', 'modified', 'role', 'user_employee_categories', 'organization',)


class UserCreateSerializer(serializers.ModelSerializer):
    """ Serializer: User Create """

    role = serializers.PrimaryKeyRelatedField(many=True, queryset=Role.objects.all())
    profile_image = Base64ImageField(required=False)

    class Meta:
        model = get_user_model()
        fields = ('pk', 'first_name', 'last_name', 'phone', 'email', 'profile_image', 'role',)

    def validate_phone(self, value):
        return validate_phone_helper(value, pk=None)

    def validate_email(self, value):
        return validate_email_helper(value, pk=None)

    def create(self, validated_data):

        role = validated_data.pop('role', [])

        user = get_user_model().objects.create_user(**validated_data)

        if role:
            user.role.set(role)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """ Serializer: User Update """

    profile_image = Base64ImageField()

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(UserUpdateSerializer, self).__init__(*args, **kwargs)

        if (self.context['is_self_requested_user']):

            self.fields.get('phone').read_only = True

    class Meta:
        model = get_user_model()
        fields = ('pk', 'first_name', 'last_name', 'phone', 'email', 'profile_image', 'role',)

    def validate_phone(self, value):
        pk = self.context.get('pk')

        return validate_phone_helper(value, pk)

    def validate_email(self, value):
        pk = self.context.get('pk')

        return validate_email_helper(value, pk)


    def update(self, instance, validated_data):

        final_user_role_list = self.context.get('final_user_role_list', [])

        if final_user_role_list:
            instance.role.set(final_user_role_list)

        super().update(instance=instance, validated_data=validated_data)

        return instance


# Start UserDetail serializers
class UserDetailCreateSeializer(serializers.ModelSerializer):
    """ Serializer: UserDetail Create """

    class Meta:
        model = UserDetail
        fields = ('pk', 'user', 'organization',)
# End UserDetail serializers
