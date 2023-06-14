from django.urls import path
from app.users.views import (
    # Authentication Flow
    GenerateOTPLoginView,
    VerifyOTPLoginView,
    CustomLogoutView,

    # Create initial super admin user
    SuperAdminUserSetup,

    # User management Flow
    UserCreate,
    UserDetails,
    UserList,
    UserListFilter,

    # UserEmployeeCategory
    UserEmployeeCategoryCreate,
    UserEmployeeCategoryDetail,

    # Organization Administrator
    OrganizationAdministratorLinkingCreate,
    OrganizationAdministratorLinkingDetail,

    # Employee
    EmployeeLinkingCreate,
    EmployeeLinkingDetail,

    # Establishment Admin
    EstablishmentAdminLinkingCreate,
    EstablishmentAdminLinkingDetail,

    # Resident
    ResidentUserLinking,

    # EstablishmentGuard
    EstablishmentGuardLinkingCreate,
    EstablishmentGuardLinkingDetail,

    # Management Committee
    ManagementCommitteeLinking
)

urlpatterns = [
    # Authentication Flow
    path('generate-otp/', GenerateOTPLoginView.as_view(), name='generate-otp'),
    path('verify-otp/', VerifyOTPLoginView.as_view(), name='verify-otp'),
    path('custom-logout/', CustomLogoutView.as_view(), name='custom-logout'),

    # Create initial super admin user
    path('super-admin-user-setup/', SuperAdminUserSetup.as_view(), name='super-admin-user-setup'),

    # User management Flow
    path('', UserCreate.as_view(), name='user-create'),
    path('<int:pk>', UserDetails.as_view(), name='user-details'),
    path('list/', UserList.as_view(), name='user-list'),
    path('list-filter/', UserListFilter.as_view(), name='user-list-filter'),

    # UserEmployeeCategory
    path('user-employee-category/', UserEmployeeCategoryCreate.as_view(), name='user-create-employee-category'),
    path('user-employee-category/<int:pk>', UserEmployeeCategoryDetail.as_view(), name='user-delete-employee-category'),

    # Organization Administrator
    path('organization-administrator-linking/', OrganizationAdministratorLinkingCreate().as_view(), name='organization-administrator-linking'),
    path('organization-administrator-linking/<int:pk>', OrganizationAdministratorLinkingDetail.as_view(), name='organization-administrator-linking-detail'),

    # Employee
    path('employee-linking/', EmployeeLinkingCreate.as_view(), name='employee-linking'),
    path('employee-linking/<int:pk>', EmployeeLinkingDetail.as_view(), name='employee-linking-detail'),

    # Establishment Admin
    path('establishment-admin-linking/', EstablishmentAdminLinkingCreate.as_view(), name='establishment-admin-linking'),
    path('establishment-admin-linking/<int:pk>', EstablishmentAdminLinkingDetail.as_view(), name='establishment-admin-linking-detail'),

    # Resident
    path('resident-user-linking/', ResidentUserLinking.as_view(), name='resident-user-linking'),

    # Establishment Guard
    path('establishment-guard-linking/', EstablishmentGuardLinkingCreate.as_view(), name='establishment-guard-linking'),
    path('establishment-guard-linking/<int:pk>', EstablishmentGuardLinkingDetail.as_view(), name='establishment-guard-linking-detail'),

    # Management Committee
    path('management-committee-linking/', ManagementCommitteeLinking.as_view(), name='management-committee-linking'),
]
