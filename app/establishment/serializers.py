# Package imports
from rest_framework import serializers

# Model imports
from app.core.models  import (
    Establishment,
    ManagementCommittee,
    EstablishmentGuard,
    FlatMember
)

# Serializer imports
from app.users.serializers import (
    UserDisplaySerializer,
)
from app.location.serializers import (
    LocationDisplaySerializer,
)
from app.address.serializers import (
    AddressDisplaySerializer,
)

# Utility imports
from app.utils import (
    get_global_error_messages,
)


# Start Establishment serializers
class EstablishmentDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Establishment Display """

    establishment_admin = UserDisplaySerializer()
    location = LocationDisplaySerializer()
    address = AddressDisplaySerializer()

    class Meta:
        model = Establishment
        fields = ('pk', 'owner_organization', 'establishment_admin', 'location', 'address', 'name', 'start_date', 'end_date', 'water_bill_link', 'pipe_gas_bill_link', 'electricity_bill_link', 'created', 'modified',)


class EstablishmentCreateSerializer(serializers.ModelSerializer):
    """ Serializer: Establishment Create """

    class Meta:
        model = Establishment
        fields = ('pk', 'owner_organization', 'location', 'address', 'name', 'start_date', 'end_date', 'water_bill_link', 'pipe_gas_bill_link', 'electricity_bill_link',)


    def validate_end_date(self, value):
        """ Validating if end_date is less than start_date """

        request = self.context.get('request')

        if not 'start_date' in request.data['establishment'] or str(value) < request.data['establishment']['start_date']:
            raise serializers.ValidationError(get_global_error_messages()['INVALID_END_DATE'])

        return value
# End Establishment serializers


# Start EstablishmentAdmin serializers
class EstablishmentAdminCreateSeializer(serializers.ModelSerializer):
    """ Serializer: EstablishmentAdmin Create """

    class Meta:
        model = Establishment
        fields = ('pk', 'establishment_admin',)
# End EstablishmentAdmin serializers


# Start ManagementCommittee serializers
class ManagementCommitteeCreateSeializer(serializers.ModelSerializer):
    """ Serializer: ManagementCommittee Create """

    class Meta:
        model = ManagementCommittee
        fields = ('pk', 'establishment', 'user', 'committee_role',)
# End ManagementCommittee serializers


# Start EstablishmentGuard serializers
class EstablishmentGuardCreateSeializer(serializers.ModelSerializer):
    """ Serializer: EstablishmentGuard Create """

    class Meta:
        model = EstablishmentGuard
        fields = ('pk', 'establishment', 'user',)
# End EstablishmentGuard serializers


# Start FlatMember serializers
class FlatMemberCreateSeializer(serializers.ModelSerializer):
    """ Serializer: FlatMember Create """

    class Meta:
        model = FlatMember
        fields = ('pk', 'flat', 'user', 'member_role',)
# End FlatMember serializers
