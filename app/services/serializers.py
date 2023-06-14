# Package imports
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from datetime import date

# Model imports
from app.core.models  import (
    ServiceCategory,
    ServiceSubCategory,
    Service,
    ServiceSlot,
    ServiceExclusion
)

# Utility imports
from app.utils import (
    get_global_error_messages,
)


# Start ServiceCategory serializers
class ServiceCategoryDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: ServiceCategory Display """

    class Meta:
        model = ServiceCategory
        fields = ('pk', 'owner_organization', 'name', 'created', 'modified',)


class ServiceCategoryCreateSerializer(serializers.ModelSerializer):
    """ Serializer: ServiceCategory Create """

    class Meta:
        model = ServiceCategory
        fields = ('pk', 'owner_organization', 'name',)
# End ServiceCategory serializers


# Start ServiceSubCategory serializers
class ServiceSubCategoryDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: ServiceSubCategory Display """

    category = ServiceCategoryDisplaySerializer()

    class Meta:
        model = ServiceSubCategory
        fields = ('pk', 'owner_organization', 'category', 'name', 'created', 'modified',)


class ServiceSubCategoryCreateSerializer(serializers.ModelSerializer):
    """ Serializer: ServiceSubCategory Create """

    class Meta:
        model = ServiceSubCategory
        fields = ('pk', 'owner_organization', 'category', 'name',)


# Start Service serializers
class ServiceDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Service Display """

    subcategory = ServiceSubCategoryDisplaySerializer()

    class Meta:
        model = Service

        fields = ('pk', 'owner_organization', 'subcategory', 'name', 'image', 'price', 'created', 'modified',)


class ServiceCreateSerializer(serializers.ModelSerializer):
    """ Serializer: Service Create """

    image = Base64ImageField()

    class Meta:
        model = Service
        fields = ('pk', 'owner_organization', 'subcategory', 'name', 'image', 'price',)
# End Service serializers


# Start ServiceSlot serializers
class ServiceSlotDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: ServiceSlot Display """

    service = ServiceDisplaySerializer()

    class Meta:
        model = ServiceSlot
        fields = ('pk', 'service', 'start_time', 'end_time', 'day_of_week', 'created', 'modified',)


class ServiceSlotCreateSerializer(serializers.ModelSerializer):
    """ Serializer: ServiceSlot Create """

    class Meta:
        model = ServiceSlot
        fields = ('pk', 'service', 'start_time', 'end_time', 'day_of_week',)


    def validate_end_time(self, value):
        """ Validating if end_time is less than start_time """

        request = self.context.get('request')

        if not 'start_time' in request.data or str(value) < request.data['start_time']:
            raise serializers.ValidationError(get_global_error_messages()['INVALID_END_TIME'])

        return value


    def validate_day_of_week(self, value):
        """ Validating if day_of_week is greater than 7 """

        request = self.context.get('request')

        if not 'day_of_week' in request.data or str(value) > str(7):
            raise serializers.ValidationError(get_global_error_messages()['INVALID_DAY_OF_WEEK'])

        return value
# End ServiceSlot serializers


# Start ServiceExclusion serializers
class ServiceExclusionDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: ServiceExclusion Display """

    service = ServiceDisplaySerializer()

    class Meta:
        model = ServiceExclusion
        fields = ('pk', 'service', 'exclusion_date', 'created', 'modified',)


class ServiceExclusionCreateSerializer(serializers.ModelSerializer):
    """ Serializer: ServiceExclusion Create """

    class Meta:
        model = ServiceExclusion
        fields = ('pk', 'service', 'exclusion_date',)

    def validate_exclusion_date(self, value):
        """ Validating if exclusion_date is in the past """

        request = self.context.get('request')

        if not 'exclusion_date' in request.data or str(value) < str(date.today()):
            raise serializers.ValidationError(get_global_error_messages()['INVALID_EXCLUSION_DATE'])

        return value
# End ServiceExclusion serializers
