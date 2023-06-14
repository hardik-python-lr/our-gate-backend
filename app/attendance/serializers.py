# Package imports
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

# Model imports
from app.core.models import (
    EstablishmentGuardAttendanceRecord,
    DeviceId
)


# Start Check-In serializer
class EstablishmentGuardAttendanceRecordSerializer(serializers.ModelSerializer):
    """ Serializer: EstablishmentGuardAttendanceRecord CheckIn and CheckOut """

    sign_in_image = Base64ImageField()
    sign_out_image = Base64ImageField(required=False)

    class Meta:
        model = EstablishmentGuardAttendanceRecord
        fields = ('pk', 'establishment_guard', 'sign_in_location', 'sign_in_device_id', 'sign_out_location', 'sign_out_device_id', 'sign_in_image', 'sign_out_image', 'sign_in_time', 'sign_out_time',)


class DeviceIdSerializer(serializers.ModelSerializer):
    """ Serializer: DeviceId """

    class Meta:
        model = DeviceId
        fields = ('pk', 'device_id', 'created', 'modified',)

    def create(self, validated_data):
        instance, _ = DeviceId.objects.get_or_create(**validated_data)
        return instance
# End Check-In serializer
