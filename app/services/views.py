# Package imports
from django.conf import settings
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response

# View imports
from app.core.views import (
    CustomPageNumberPagination,
)

# Serializer imports
from app.services.serializers import (
    # ServiceCategory
    ServiceCategoryCreateSerializer,
    ServiceCategoryDisplaySerializer,

    # ServiceSubCategory
    ServiceSubCategoryCreateSerializer,
    ServiceSubCategoryDisplaySerializer,

    # Service
    ServiceCreateSerializer,
    ServiceDisplaySerializer,

    # ServiceSlot serializers
    ServiceSlotDisplaySerializer,
    ServiceSlotCreateSerializer,

    # ServiceExclusion serializers
    ServiceExclusionDisplaySerializer,
    ServiceExclusionCreateSerializer,
)

# Model imports
from app.core.models import (
    ServiceCategory,
    ServiceSubCategory,
    Service,
    ServiceSlot,
    ServiceExclusion
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


# Start ServiceCategory views
class ServiceCategoryCreate(GenericAPIView):
    """ View: Create ServiceCategory """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type='string'),
            }
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        request.data['owner_organization'] = request.user.user_details.organization.id

        serializer = ServiceCategoryCreateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return get_response_schema(serializer.data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

        return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class ServiceCategoryDetail(GenericAPIView):
    """ View: Retrieve, update or delete an ServiceCategory """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        service_category_queryset = ServiceCategory.objects.filter(
            pk=pk,
            is_active=True,
            owner_organization_id=request.user.user_details.organization.id,
            owner_organization__is_active=True
        )

        if service_category_queryset:
            return service_category_queryset[0]
        return None

    def get(self, request, pk=None):

        service_category = self.get_object(pk, request)

        if service_category == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        serializer = ServiceCategoryDisplaySerializer(service_category)

        return get_response_schema(serializer.data, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type='string'),
            }
        )
    )
    def put(self, request, pk, format=None):

        service_category = self.get_object(pk, request)

        if service_category == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        request.data['owner_organization'] = request.user.user_details.organization.id

        serializer = ServiceCategoryCreateSerializer(service_category, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return get_response_schema(serializer.data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

        return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        service_category = self.get_object(pk, request)

        if service_category == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        service_category.is_active = False
        service_category.save()

        return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)


class ServiceCategoryList(GenericAPIView):
    """ View: List ServiceCategory (dropdown) """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = ServiceCategory.objects.filter(
            is_active=True,
            owner_organization_id=request.user.user_details.organization.id,
            owner_organization__is_active=True
        ).order_by(
            'name'
        )

        service_category_display_serializer = ServiceCategoryDisplaySerializer(queryset, many=True)

        return Response(service_category_display_serializer.data, status=status.HTTP_200_OK)


class ServiceCategoryListFilter(ListAPIView):
    """ View: List ServiceCategory """

    serializer_class = ServiceCategoryDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'],]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        queryset = ServiceCategory.objects.filter(
            is_active=True,
            owner_organization_id=self.request.user.user_details.organization.id,
            owner_organization__is_active=True
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
# End ServiceCategory views


# Start ServiceSubCategory views
class ServiceSubCategoryCreate(GenericAPIView):
    """ View: Create ServiceSubCategory """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type='string'),
                'category': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Checking for valid category ID
        service_category_queryset = ServiceCategory.objects.filter(
            pk = request.data['category'],
            is_active=True,
            owner_organization=request.user.user_details.organization,
            owner_organization__is_active=True
        )

        if service_category_queryset:

            request.data['owner_organization'] = request.user.user_details.organization.id

            serializer = ServiceSubCategoryCreateSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

            return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class ServiceSubCategoryDetail(GenericAPIView):
    """ View: Retrieve, update or delete an ServiceSubCategory """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        service_sub_category_queryset = ServiceSubCategory.objects.select_related(
            'category'
        ).filter(
            pk=pk,
            is_active=True,
            owner_organization_id=request.user.user_details.organization.id,
            owner_organization__is_active=True
        )

        if service_sub_category_queryset:
            return service_sub_category_queryset[0]
        return None

    def get(self, request, pk=None):

        service_sub_category = self.get_object(pk, request)

        if service_sub_category == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        serializer = ServiceSubCategoryDisplaySerializer(service_sub_category)

        return get_response_schema(serializer.data, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type='string'),
                'category': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        )
    )
    def put(self, request, pk, format=None):

        service_sub_category = self.get_object(pk, request)

        if service_sub_category == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        # Checking for valid category ID
        service_category_queryset = ServiceCategory.objects.filter(
            pk = request.data['category'],
            is_active=True,
            owner_organization=request.user.user_details.organization,
            owner_organization__is_active=True
        )

        if service_category_queryset:

            request.data['owner_organization'] = request.user.user_details.organization.id

            serializer = ServiceSubCategoryCreateSerializer(service_sub_category, data=request.data)

            if serializer.is_valid():
                serializer.save()

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

            return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        service_sub_category = self.get_object(pk, request)

        if service_sub_category == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        service_sub_category.is_active = False
        service_sub_category.save()

        return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)


class ServiceSubCategoryList(GenericAPIView):
    """ View: List ServiceSubCategory (dropdown) """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = ServiceSubCategory.objects.select_related(
            'category'
        ).filter(
            is_active=True,
            owner_organization_id=request.user.user_details.organization.id,
            owner_organization__is_active=True
        ).order_by(
            'name'
        )

        service_sub_category_display_serializer = ServiceSubCategoryDisplaySerializer(queryset, many=True)

        return Response(service_sub_category_display_serializer.data, status=status.HTTP_200_OK)


class ServiceSubCategoryListFilter(ListAPIView):
    """ View: List ServiceSubCategory """

    serializer_class = ServiceSubCategoryDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'],]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        queryset = ServiceSubCategory.objects.select_related(
            'category'
        ).filter(
            is_active=True,
            owner_organization_id=self.request.user.user_details.organization.id,
            owner_organization__is_active=True
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
# End ServiceSubCategory views


# Start Service views
class ServiceCreate(GenericAPIView):
    """ View: Create Service """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type='string'),
                'subcategory': openapi.Schema(type=openapi.TYPE_INTEGER),
                'image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64),
                'price': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Checking for valid category ID
        service_sub_category_queryset = ServiceSubCategory.objects.filter(
            pk = request.data['subcategory'],
            is_active=True,
            owner_organization=request.user.user_details.organization,
            owner_organization__is_active=True
        )

        if service_sub_category_queryset:

            request.data['owner_organization'] = request.user.user_details.organization.id

            serializer = ServiceCreateSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

            return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class ServiceDetail(GenericAPIView):
    """ View: Retrieve, update or delete an Service """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        service_queryset = Service.objects.select_related(
            'subcategory',
            'subcategory__category',
        ).filter(
            pk=pk,
            is_active=True,
            owner_organization_id=request.user.user_details.organization.id,
            owner_organization__is_active=True
        )

        if service_queryset:
            return service_queryset[0]
        return None

    def get(self, request, pk=None):

        service = self.get_object(pk, request)

        if service == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        serializer = ServiceDisplaySerializer(service)

        return get_response_schema(serializer.data, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type='string'),
                'subcategory': openapi.Schema(type=openapi.TYPE_INTEGER),
                'image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BASE64),
                'price': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )
    def put(self, request, pk, format=None):

        service = self.get_object(pk, request)

        if service == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        # Checking for valid category ID
        service_sub_category_queryset = ServiceSubCategory.objects.filter(
            pk = request.data['subcategory'],
            is_active=True,
            owner_organization=request.user.user_details.organization,
            owner_organization__is_active=True
        )

        if service_sub_category_queryset:

            request.data['owner_organization'] = request.user.user_details.organization.id

            serializer = ServiceCreateSerializer(service, data=request.data)

            if serializer.is_valid():
                serializer.save()

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

            return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)
        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        service = self.get_object(pk, request)

        if service == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        service.is_active = False
        service.save()

        return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)


class ServiceList(GenericAPIView):
    """ View: List Service (dropdown) """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = Service.objects.select_related(
            'subcategory',
            'subcategory__category',
        ).filter(
            is_active=True,
            owner_organization_id=request.user.user_details.organization.id,
            owner_organization__is_active=True
        ).order_by(
            'name'
        )

        service_display_serializer = ServiceDisplaySerializer(queryset, many=True)

        return Response(service_display_serializer.data, status=status.HTTP_200_OK)


class ServiceListFilter(ListAPIView):
    """ View: List Service """

    serializer_class = ServiceDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'],]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        queryset = Service.objects.select_related(
            'subcategory',
            'subcategory__category',
        ).filter(
            is_active=True,
            owner_organization_id=self.request.user.user_details.organization.id,
            owner_organization__is_active=True
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
# End Service views


# Start ServiceSlot views
class ServiceSlotCreate(GenericAPIView):
    """ View: Create ServiceSlot """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'service': openapi.Schema(type=openapi.TYPE_INTEGER),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, format='time'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, format='time'),
                'day_of_week': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating service ID
        service_queryset = Service.objects.filter(
            pk=request.data['service'],
            is_active=True,
            owner_organization=request.user.user_details.organization
        )

        if service_queryset:

            serializer = ServiceSlotCreateSerializer(data=request.data, context={'request': request})

            if serializer.is_valid():

                serializer.save()

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

            else:
                # ServiceSlotCreateSerializer serializer errors
                return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class ServiceSlotDetail(GenericAPIView):
    """ View: Retrieve, update or delete ServiceSlot """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):

        service_slot_queryset = ServiceSlot.objects.select_related(
            'service',
            'service__subcategory',
            'service__subcategory__category',
        ).filter(
            pk=pk,
            is_active=True,
            service__owner_organization=request.user.user_details.organization
        )

        if service_slot_queryset:
            return service_slot_queryset[0]
        return None

    def get(self, request, pk=None):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        service_slot = self.get_object(pk, request)

        if service_slot == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        serializer = ServiceSlotDisplaySerializer(service_slot)

        return get_response_schema(serializer.data, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'service': openapi.Schema(type=openapi.TYPE_INTEGER),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, format='time'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, format='time'),
                'day_of_week': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )
    def put(self, request, pk, format=None):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        service_slot = self.get_object(pk, request)

        if service_slot == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        # Validating service ID
        service_queryset = Service.objects.filter(
            pk=request.data['service'],
            is_active=True,
            owner_organization=request.user.user_details.organization
        )

        if service_queryset:

            serializer = ServiceSlotCreateSerializer(service_slot, data=request.data, context={'request': request})

            if serializer.is_valid():

                serializer.save()

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

            else:
                # ServiceSlotCreateSerializer serializer errors
                return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        service_slot = self.get_object(pk, request)

        if service_slot == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        service_slot.is_active = False

        service_slot.save()

        return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)


class ServiceSlotList(GenericAPIView):
    """ View: List ServiceSlot (dropdown) """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = ServiceSlot.objects.select_related(
            'service',
            'service__subcategory',
            'service__subcategory__category',
        ).filter(
            is_active=True,
            service__owner_organization=request.user.user_details.organization
        ).order_by(
            'day_of_week',
            'service__name',
            '-created'
        )

        service_slot_display_serializer = ServiceSlotDisplaySerializer(queryset, many=True)

        return Response(service_slot_display_serializer.data, status=status.HTTP_200_OK)


class ServiceSlotListFilter(ListAPIView):
    """ View: List ServiceSlot Filter """

    serializer_class = ServiceSlotDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        queryset = ServiceSlot.objects.select_related(
            'service',
            'service__subcategory',
            'service__subcategory__category',
        ).filter(
            is_active=True,
            service__owner_organization=self.request.user.user_details.organization
        ).order_by(
            'day_of_week',
            'service__name',
            '-created'
        )

        if self.request.query_params.get('day_of_week'):
            queryset = queryset.filter(day_of_week=self.request.query_params.get('day_of_week'))

        if self.request.query_params.get('service_name'):
            queryset = queryset.filter(service__name__icontains=self.request.query_params.get('service_name'))

        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('day_of_week', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('service_name', openapi.IN_QUERY, type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
# End ServiceSlot views


# Start ServiceExclusion views
class ServiceExclusionCreate(GenericAPIView):
    """ View: Create ServiceExclusion """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'service': openapi.Schema(type=openapi.TYPE_INTEGER),
                'exclusion_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
            }
        )
    )
    def post(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        # Validating service ID
        service_queryset = Service.objects.filter(
            pk=request.data['service'],
            is_active=True,
            owner_organization=request.user.user_details.organization
        )

        if service_queryset:

            serializer = ServiceExclusionCreateSerializer(data=request.data, context={'request': request})

            if serializer.is_valid():

                serializer.save()

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

            else:
                # ServiceExclusionCreateSerializer serializer errors
                return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class ServiceExclusionDetail(GenericAPIView):
    """ View: Retrieve, update or delete ServiceExclusion """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):

        service_exclusion_queryset = ServiceExclusion.objects.select_related(
            'service',
            'service__subcategory',
            'service__subcategory__category',
        ).filter(
            pk=pk,
            service__owner_organization=request.user.user_details.organization
        )

        if service_exclusion_queryset:
            return service_exclusion_queryset[0]
        return None

    def get(self, request, pk=None):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        service_exclusion = self.get_object(pk, request)

        if service_exclusion == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        serializer = ServiceExclusionDisplaySerializer(service_exclusion)

        return get_response_schema(serializer.data, get_global_success_messages()['RECORD_RETRIEVED'], status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'service': openapi.Schema(type=openapi.TYPE_INTEGER),
                'exclusion_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
            }
        )
    )
    def put(self, request, pk, format=None):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        service_exclusion = self.get_object(pk, request)

        if service_exclusion == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        # Validating service ID
        service_queryset = Service.objects.filter(
            pk=request.data['service'],
            is_active=True,
            owner_organization=request.user.user_details.organization
        )

        if service_queryset:

            serializer = ServiceExclusionCreateSerializer(service_exclusion, data=request.data, context={'request': request})

            if serializer.is_valid():

                serializer.save()

                return get_response_schema(serializer.data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

            else:
                # ServiceExclusionCreateSerializer serializer errors
                return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

        else:
            return_data = {
                settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [get_global_error_messages()['SOMETHING_WENT_WRONG']]
            }
            return get_response_schema(return_data, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        service_exclusion = self.get_object(pk, request)

        if service_exclusion == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        service_exclusion.delete()

        return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)


class ServiceExclusionList(GenericAPIView):
    """ View: List ServiceExclusion (dropdown) """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = ServiceExclusion.objects.select_related(
            'service',
            'service__subcategory',
            'service__subcategory__category',
        ).filter(
            service__owner_organization=request.user.user_details.organization
        ).order_by(
            '-exclusion_date',
            'service__name',
            '-created'
        )

        service_exclusion_display_serializer = ServiceExclusionDisplaySerializer(queryset, many=True)

        return Response(service_exclusion_display_serializer.data, status=status.HTTP_200_OK)


class ServiceExclusionListFilter(ListAPIView):
    """ View: List ServiceExclusion Filter """

    serializer_class = ServiceExclusionDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        queryset = ServiceExclusion.objects.select_related(
            'service',
            'service__subcategory',
            'service__subcategory__category',
        ).filter(
            service__owner_organization=self.request.user.user_details.organization
        ).order_by(
            '-exclusion_date',
            'service__name',
            '-created'
        )

        if self.request.query_params.get('exclusion_date'):
            queryset = queryset.filter(exclusion_date=self.request.query_params.get('exclusion_date'))

        if self.request.query_params.get('service_name'):
            queryset = queryset.filter(service__name__icontains=self.request.query_params.get('service_name'))

        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('exclusion_date', openapi.IN_QUERY, type='date'),
            openapi.Parameter('service_name', openapi.IN_QUERY, type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
# End ServiceExclusion views
