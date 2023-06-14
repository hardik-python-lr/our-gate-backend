# Package imports
from django.conf import settings
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from django.db import transaction

# View imports
from app.core.views import (
    CustomPageNumberPagination,
)

# Serializer imports
from app.organization.serializers import (
    OrganizationDisplaySerializer,
    OrganizationCreateSerializer,
)
from app.address.serializers import (
    AddressCreateSerializer
)

# Model imports
from app.core.models import (
    Organization,
)   

# Utility imports
from app.utils import (
    get_response_schema,
    get_global_success_messages,
    get_global_error_messages,
    get_global_values
)
from app.permissions import (
    does_permission_exist
)

# Swagger imports
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# Start Organization views
class OrganizationCreate(GenericAPIView):
    """ View: Create Organization """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'address': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'address_line_1': openapi.Schema(type=openapi.TYPE_STRING),
                        'address_line_2': openapi.Schema(type=openapi.TYPE_STRING),
                        'pincode': openapi.Schema(type=openapi.TYPE_STRING),
                        'city': openapi.Schema(type=openapi.TYPE_STRING),
                        'state': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
                'organization': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'name': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
            }
        )
    )
    def post(self, request):

        with transaction.atomic():

            # Check role permissions
            required_role_list = [get_global_values()['SUPER_ADMIN_ROLE_ID']]

            permissions = does_permission_exist(required_role_list, request.user.id)

            if not permissions['allowed']:
                return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

            if ('address' not in request.data.keys()) or ('organization' not in request.data.keys()):
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_RESPONSE']]
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

            # Save address
            address_create_serializer = AddressCreateSerializer(data=request.data['address'])

            if address_create_serializer.is_valid():

                address_obj = address_create_serializer.save()

                # Register address and owner_user in request
                request.data['organization']['address'] = address_obj.id
                request.data['organization']['owner_user'] = request.user.id

                organization_create_serializer = OrganizationCreateSerializer(data=request.data['organization'])

                if organization_create_serializer.is_valid():

                    organization_create_serializer.save()

                    return_data = {
                        'address': address_create_serializer.data,
                        'organization': organization_create_serializer.data
                    }
                    return get_response_schema(return_data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)
                # Organization serializer errors
                # Rollback the transaction
                transaction.set_rollback(True)
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
                    get_global_values()['ERROR_KEY']: organization_create_serializer.errors
                }
                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
            # Address global error
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_ADDRESS']]
            }

            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class OrganizationDetail(GenericAPIView):
    """ View: Retrieve, update or delete an Organization """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):

        # Check role permissions
        required_role_list = [get_global_values()['SUPER_ADMIN_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        organization_queryset = Organization.objects.select_related(
            'address'
        ).filter(
            pk=pk,
            is_active=True,
            owner_user=request.user
        )

        if organization_queryset:
            return organization_queryset[0]
        return None

    def get(self, request, pk=None):

        organization = self.get_object(pk, request)

        if organization == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)
        
        serializer = OrganizationDisplaySerializer(organization)

        return get_response_schema(serializer.data, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'address': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'address_line_1': openapi.Schema(type=openapi.TYPE_STRING),
                        'address_line_2': openapi.Schema(type=openapi.TYPE_STRING),
                        'pincode': openapi.Schema(type=openapi.TYPE_STRING),
                        'city': openapi.Schema(type=openapi.TYPE_STRING),
                        'state': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
                'organization': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'name': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
            }
        )
    )
    def put(self, request, pk, format=None):

        organization = self.get_object(pk, request)

        if organization == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        # Check if the address has been updated
        address_create_serializer = None

        if request.data['address'] != None:

            address_create_serializer = AddressCreateSerializer(organization.address, data=request.data['address'])

            if address_create_serializer.is_valid():
                address_create_serializer.save()
            else:
                # Address global error
                return_data = {
                    settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['INVALID_ADDRESS']]
                }

                return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        # Handle organization
        request.data['organization']['owner_user'] = request.user.id

        organization_create_serializer = OrganizationCreateSerializer(organization, data=request.data['organization'])

        if organization_create_serializer.is_valid():
            organization_create_serializer.save()

            return_data = {
                'address': address_create_serializer.data if address_create_serializer != None else None,
                'organization': organization_create_serializer.data
            }

            return get_response_schema(return_data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)
        return_data = {
            settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']],
            get_global_values()['ERROR_KEY']: organization_create_serializer.errors
        }
        return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        organization = self.get_object(pk, request)

        if organization == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        organization.is_active = False
        organization.save()

        return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)


class OrganizationList(GenericAPIView):
    """ View: List Organization (dropdown) """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['SUPER_ADMIN_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema([], get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = Organization.objects.select_related(
            'address'
        ).filter(
            is_active=True,
            owner_user=self.request.user
        ).order_by(
            'name'
        )

        organization_display_serializer = OrganizationDisplaySerializer(queryset, many=True)

        return Response(organization_display_serializer.data, status=status.HTTP_200_OK)


class OrganizationListFilter(ListAPIView):
    """ View: List Organization Filter """

    serializer_class = OrganizationDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [get_global_values()['SUPER_ADMIN_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        queryset = Organization.objects.select_related(
            'address'
        ).filter(
            is_active=True,
            owner_user=self.request.user
        ).order_by(
            'name'
        )

        if self.request.query_params.get('name'):
            queryset = queryset.filter(name__icontains=self.request.query_params.get('name'))

        return queryset
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_QUERY, type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
# End Organization views
