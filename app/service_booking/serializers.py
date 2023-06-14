# Package imports
from rest_framework import serializers


# Model imports
from app.core.models  import (
    Service,
    ServiceCategory,
    ServiceSubCategory,
    ServiceRequest,
    Establishment,
    ServiceSlot,
    ServiceRequestServiceSlot,
    Payment,
    Flat
)
from django.contrib.auth import get_user_model

# Utility imports
from app.utils import (
    get_global_error_messages, 
    get_global_values
)


# Start Service booking serializers for Resident User
class ServiceForBookingDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Service Display for Resident User """

    organization_name = serializers.CharField(source ='owner_organization.name')
    category = serializers.CharField(source ='subcategory.name')
    subcategory = serializers.CharField(source ='subcategory.category.name')

    class Meta:
        model = Service
        fields = ('pk', 'organization_name', 'category', 'subcategory', 'name', 'image', 'price',)


class ServiceCategoryForBookingDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: ServiceCategory Display (Dropdown) for Resident User """

    organization_name = serializers.CharField(source ='owner_organization.name')
    
    class Meta:
        model = ServiceCategory
        fields = ('pk', 'organization_name', 'name',)


class ServiceSubCategoryForBookingDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: ServiceSubCategory Display (Dropdown) for Resident User """

    organization_name = serializers.CharField(source ='owner_organization.name')

    class Meta:
        model = ServiceSubCategory
        fields = ('pk', 'organization_name', 'name',)


class ServiceRequestHistoryRecordsListSerializer(serializers.ModelSerializer):
    """ Serializer: ServiceRequest List filter for Resident User """

    service_name = serializers.CharField(source ='service.name')
    service_image = serializers.ImageField(source ='service.image')
    subcategory_name = serializers.CharField(source ='service.subcategory.name')
    category_name = serializers.CharField(source ='service.subcategory.category.name')
    organization_name = serializers.CharField(source ='service.owner_organization.name')

    class Meta:
        model = ServiceRequest
        fields = ('pk', 'service_name', 'service_image', 'subcategory_name', 'category_name', 'organization_name', 'requested_date', 'amount', 'service_request_status', 'rating',)    


class ServiceSlotForBookingDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: ServiceSlot Display for Resident User """

    class Meta:
        model = ServiceSlot
        fields = ('pk', 'start_time', 'end_time', 'day_of_week',)


class ServiceRequestServiceSlotForBookingCreateSerializer(serializers.ModelSerializer):
    """ Serializer: ServiceRequestServiceSlot for booking Create for Resident User """

    class Meta:
        model = ServiceRequestServiceSlot
        fields = ('pk', 'service_request', 'service_slot', 'start_time', 'end_time',)


class PaymentForBookingCreateSerializer(serializers.ModelSerializer):
    """ Serializer: Payment for booking Create for Resident User """

    class Meta:
        model = Payment
        fields = ('pk', 'order_id', 'payment_id', 'signature', 'amount', 'payment_status',)
# End Service booking serializers for Resident User


# Start Service booking serializers for Organization Administrator
class AssignedUserServiceRequestSerializer(serializers.ModelSerializer):
    """ Serializer: Assigned User to ServiceRequest for Organization Administrator """

    class Meta:
        model = ServiceRequest
        fields = ('pk', 'assigned_user', 'requested_date', 'service_request_status',)
# End Service booking serializers for Organization Administrator


# Start Service booking serializers for Organization Administrator and Employee
class ServiceRequestAllRecordsListSerializer(serializers.ModelSerializer):
    """ Serializer: ServiceRequest List Filter for Organization Administrator """

    service_name = serializers.CharField(source ='service.name')
    service_image = serializers.CharField(source ='service.image')
    subcategory_name = serializers.CharField(source ='service.subcategory.name')
    category_name = serializers.CharField(source ='service.subcategory.category.name')
    organization_name = serializers.CharField(source ='service.owner_organization.name')
    assigned_user_pk = serializers.SerializerMethodField()
    assigned_user_first_name = serializers.SerializerMethodField()
    assigned_user_last_name = serializers.SerializerMethodField()
    assigned_user_phone = serializers.SerializerMethodField()
    requested_user_pk = serializers.SerializerMethodField()
    requested_user_first_name = serializers.SerializerMethodField()
    requested_user_last_name = serializers.SerializerMethodField()
    requested_user_phone = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = ('pk', 'service_name', 'service_image', 'requested_user_pk', 'requested_user_first_name', 'requested_user_last_name', 'requested_user_phone', 'subcategory_name', 'category_name', 'organization_name', 'assigned_user_pk', 'assigned_user_first_name', 'assigned_user_last_name', 'assigned_user_phone', 
        'requested_date', 'service_request_status', 'flat', 'rating',)

    def get_assigned_user_pk(self, obj):
        try:
            return obj.assigned_user.pk
        except:
            return None

    def get_assigned_user_first_name(self, obj):
        try:
            return obj.assigned_user.first_name
        except:
            return None

    def get_assigned_user_last_name(self, obj):
        try:
            return obj.assigned_user.last_name
        except:
            return None

    def get_assigned_user_phone(self, obj):
        try:
            return obj.assigned_user.phone
        except:
            return None

    def get_requested_user_pk(self, obj):
        try:
            return obj.requested_user.pk
        except:
            return None

    def get_requested_user_first_name(self, obj):
        try:
            return obj.requested_user.first_name
        except:
            return None

    def get_requested_user_last_name(self, obj):
        try:
            return obj.requested_user.last_name
        except:
            return None

    def get_requested_user_phone(self, obj):
        try:
            return obj.requested_user.phone
        except:
            return None


class EstablishmentDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Establishment Display (Dropdown) for Organization Administrator """

    organization_name = serializers.CharField(source ='owner_organization.name')

    class Meta:
        model = Establishment
        fields = ('pk', 'organization_name', 'name',)


class UserDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: User Display (Dropdown) for Organization Administrator """

    class Meta:
        model = get_user_model()
        fields = ('pk', 'first_name', 'last_name', 'phone', 'profile_image',)
        ref_name = "abc"
# End Service booking serializers for Organization Administrator and Employee


# Start Service booking serializers for Organization Administrator and Resident User
class ServiceRequestCompleteSerializer(serializers.ModelSerializer):
    """ Serializer: Complete Service Request for Organization Administrator """

    class Meta:
        model = ServiceRequest
        fields = ('pk', 'rating', 'service_request_status',)

    def validate_rating(self, value):
        """ Validating rating must be between 1 to 5 """

        if value <= 0 or value > 5:
            raise serializers.ValidationError(get_global_error_messages()['INVALID_RATING'])

        return value


class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    """ Serializer: ServiceRequest create for Resident User """

    class Meta:
        model = ServiceRequest
        fields = ('pk', 'flat', 'requested_user', 'service', 'requested_date', 'amount', 'service_request_status', 'is_active', 'payment_info',)
# End Service booking serializers for Organization Administrator and Resident User


# Start Service booking serializers for Employee, Resident User and Organization Administrator
class PaymentForBookingDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Payment for booking Display serializer """

    class Meta:
        model = Payment
        fields = ('pk', 'order_id', 'payment_id', 'amount', 'payment_status',)


class ServiceRequestServiceSlotForBookingDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: ServiceRequestServiceSlot for booking Display serializer """

    service_slot = ServiceSlotForBookingDisplaySerializer()

    class Meta:
        model = ServiceRequestServiceSlot
        fields = ('pk', 'service_slot', 'start_time', 'end_time',)


class ServiceDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Service Display serializer """

    category_name = serializers.CharField(source ='subcategory.category.name')
    sub_category_name = serializers.CharField(source ='subcategory.name')
    organization_name = serializers.CharField(source ='owner_organization.name')

    class Meta:
        model = Service
        fields = ('pk', 'category_name', 'sub_category_name', 'organization_name', 'name', 'image', 'price',)


class FlatDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Flat Display serializer """

    establishment_name = serializers.CharField(source ='building.establishment.name')
    building_name = serializers.CharField(source ='building.name')

    class Meta:
        model = Flat
        fields = ('pk', 'establishment_name', 'building_name', 'number', 'floor_number',)


class ServiceRequestDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: ServiceRequest Display serializer """

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(ServiceRequestDisplaySerializer, self).__init__(*args, **kwargs)

        if (self.context['permissions'][str(get_global_values()['RESIDENT_USERS_ROLE_ID'])]):

            self.fields.pop('flat')
            self.fields.pop('requested_user')

        if (self.context['permissions'][str(get_global_values()['EMPLOYEE_ROLE_ID'])]):

            self.fields.pop('assigned_user')

    service = ServiceDisplaySerializer()
    flat = FlatDisplaySerializer()
    requested_user = UserDisplaySerializer()
    assigned_user = UserDisplaySerializer()
    payment_info = PaymentForBookingDisplaySerializer()

    class Meta:
        model = ServiceRequest
        fields = ('pk', 'service', 'flat', 'requested_user', 'assigned_user', 'payment_info', 'requested_date', 'amount', 'service_request_status', 'rating',)
# End Service booking serializers for Employee, Resident User and Organization Administrator
