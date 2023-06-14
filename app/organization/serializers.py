# Package imports
from rest_framework import serializers

# Model imports
from app.core.models  import (
    Organization,
)

# Serializer imports
from app.address.serializers import (
    AddressDisplaySerializer,
)


# Start Organization serializers
class OrganizationDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Organization Display """

    address = AddressDisplaySerializer()

    class Meta:
        model = Organization
        fields = ('pk', 'address', 'name', 'created', 'modified',)


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """ Serializer: Organization Create """

    class Meta:
        model = Organization
        fields = ('pk', 'owner_user', 'address', 'name',)
# End Organization serializers
