# Package imports
from rest_framework import serializers

# Model imports
from app.core.models import (
    Role,
)


class RoleDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Role Display """

    class Meta:
        model = Role
        fields = ('pk', 'name',)
