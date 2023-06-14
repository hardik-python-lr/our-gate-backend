# Package imports
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
from app.employeecategory.serializers import (
    EmployeeCategoryDisplaySerializer,
    EmployeeCategoryCreateSerializer,
)

# Model imports
from app.core.models import (
    EmployeeCategory,
)   

# Utility imports
from app.utils import (
    get_response_schema,
    get_global_success_messages,
    get_global_error_messages,
    get_global_values,
)
from app.permissions import (
    does_permission_exist
)

# Swagger imports
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class EmployeeCategoryCreate(GenericAPIView):
    """ View: Create EmployeeCategory """

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

        request.data['organization'] = request.user.user_details.organization.id

        serializer = EmployeeCategoryCreateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return get_response_schema(serializer.data, get_global_success_messages()['RECORD_CREATED'], status.HTTP_201_CREATED)

        return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)


class EmployeeCategoryDetail(GenericAPIView):
    """ View: Retrieve, update or delete an EmployeeCategory """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        employee_category_queryset = EmployeeCategory.objects.filter(
            pk=pk,
            organization_id=request.user.user_details.organization.id,
            organization__is_active=True
        )

        if employee_category_queryset:
            return employee_category_queryset[0]
        return None

    def get(self, request, pk=None):

        employee_category = self.get_object(pk, request)

        if employee_category == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        serializer = EmployeeCategoryDisplaySerializer(employee_category)

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

        employee_category = self.get_object(pk, request)

        if employee_category == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        request.data['organization'] = request.user.user_details.organization.id

        serializer = EmployeeCategoryCreateSerializer(employee_category, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return get_response_schema(serializer.data, get_global_success_messages()['RECORD_UPDATED'], status.HTTP_200_OK)

        return get_response_schema(serializer.errors, get_global_error_messages()['BAD_REQUEST'], status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        employee_category = self.get_object(pk, request)

        if employee_category == None:    
            return get_response_schema({}, get_global_error_messages()['NOT_FOUND'], status.HTTP_404_NOT_FOUND)

        employee_category.delete()

        return get_response_schema({}, get_global_success_messages()['RECORD_DELETED'], status.HTTP_204_NO_CONTENT)


class EmployeeCategoryList(GenericAPIView):
    """ View: List EmployeeCategory (dropdown) """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID']]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return get_response_schema({}, get_global_error_messages()['FORBIDDEN'], status.HTTP_403_FORBIDDEN)

        queryset = EmployeeCategory.objects.filter(
            organization_id=request.user.user_details.organization.id
        ).order_by(
            'name'
        )

        employee_category_display_serializer = EmployeeCategoryDisplaySerializer(queryset, many=True)

        return Response(employee_category_display_serializer.data, status=status.HTTP_200_OK)


class EmployeeCategoryListFilter(ListAPIView):
    """ View: List EmployeeCategory """

    serializer_class = EmployeeCategoryDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Check role permissions
        required_role_list = [get_global_values()['ORGANIZATION_ADMINISTRATOR_ROLE_ID'],]

        permissions = does_permission_exist(required_role_list, self.request.user.id)

        if not permissions['allowed']:
            return []

        queryset = EmployeeCategory.objects.filter(
            organization_id=self.request.user.user_details.organization_id
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
