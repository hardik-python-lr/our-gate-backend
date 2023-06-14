# Package imports
from rest_framework import serializers

# Model imports
from app.core.models import (
    EmployeeCategory,
)


class EmployeeCategoryDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: EmployeeCategory Display """

    class Meta:
        model = EmployeeCategory
        fields = ('pk', 'name', 'organization', 'created', 'modified',)


class EmployeeCategoryCreateSerializer(serializers.ModelSerializer):
    """ Serializer: EmployeeCategory Create """

    class Meta:
        model = EmployeeCategory
        fields = ('pk', 'organization', 'name',)
