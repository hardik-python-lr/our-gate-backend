# Package imports
from rest_framework import serializers

# Model imports
from app.core.models import (
    Location,
)


class LocationDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Location Display """

    class Meta:
        model = Location
        fields = ('pk', 'latitude', 'longitude', 'address', 'created',)


class LocationCreateSerializer(serializers.ModelSerializer):
    """ Serializer: Location Create """

    class Meta:
        model = Location
        fields = ('pk', 'latitude', 'longitude', 'address',)
