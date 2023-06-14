# Package imports
from rest_framework import serializers

# Model imports
from app.core.models import (
    Address,
)


class AddressDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Address Display """

    class Meta:
        model = Address
        fields = ('pk', 'address_line_1', 'address_line_2', 'pincode', 'city', 'state', 'created', 'modified',)


class AddressCreateSerializer(serializers.ModelSerializer):
    """ Serializer: Address Create """

    class Meta:
        model = Address
        fields = ('pk', 'address_line_1', 'address_line_2', 'pincode', 'city', 'state',)
        extra_kwargs = {
            'address_line_2': {'required': False},
            'pincode': {'required': False},
            'city': {'required': False},
            'state': {'required': False},
        }
