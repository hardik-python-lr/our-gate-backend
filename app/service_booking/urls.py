from django.urls import path
from app.service_booking.views import (
    # Service booking views for Resident User
    ServiceForBookingListFilter,
    ServiceCategoryForBookingDropdown,
    ServiceSubCategoryForBookingDropdown,
    ServiceSlotFromDate,
    PayableAmountOfServiceRequest,
    ServiceRequestCreate,
    ServiceRequestCallback,
    ServiceBookingHistoryListFilter,
    AddRatingServiceRequest,

    # Service booking views for Organization Administrator
    ServiceBookingsListFilterForOrganizationAdministrator,
    EstablishmentDropdownForOrganizationAdministrator,
    RequestedUserDropdownForOrganizationAdministrator,
    AssignedUserDropdownForOrganizationAdministrator,
    UpdateServiceRequestStatusForOrganizationAdministrator,
    AssignedUserToServiceRequestForOrganizationAdministrator,
    AssignedUserToServiceRequestDropdownForOrganizationAdministrator,

    # Service booking common views for both Resident User and Organization Administrator
    CompleteServiceRequest,

    # Service booking views for Employee
    ServiceBookingsForEmployeeListFilter,
    EstablishmentDropdownForEmployee,
    RequestedUserDropdownForEmployee,

    # Service booking views for Employee, Resident User and Organization Administrator
    ServiceRequestDetail
)


urlpatterns = [
    # Service booking for Resident User
    path('service-for-booking-list-filter/', ServiceForBookingListFilter.as_view(), name='service-for-booking-list-filter'),

    path('service-category-for-booking-dropdown/', ServiceCategoryForBookingDropdown.as_view(), name='service-category-for-booking-dropdown'),

    path('service-sub-category-for-booking-dropdown/<int:pk>', ServiceSubCategoryForBookingDropdown.as_view(), name='service-sub-category-for-booking-dropdown'),

    path('service-slot-from-date', ServiceSlotFromDate.as_view(), name='service-slot-from-date'),

    path('payable-amount-of-service-request', PayableAmountOfServiceRequest.as_view(), name='payable-amount-of-service-request'),

    path('service-request-create', ServiceRequestCreate.as_view(), name='service-request-create'),

    path('service-request-callback', ServiceRequestCallback.as_view(), name='service-request-callback'),

    path('service-booking-history-list-filter', ServiceBookingHistoryListFilter.as_view(), name='service-booking-history-list-filter'),

    path('add-rating-service-request/<int:pk>', AddRatingServiceRequest.as_view(), name='add-rating-service-request'),

    # Service booking for Organization Administrator
    path('service-bookings-list-filter-for-organization-administrator', ServiceBookingsListFilterForOrganizationAdministrator.as_view(), name='service-bookings-list-filter-for-organization-administrator'),

    path('establishment-dropdown-for-organization-administrator', EstablishmentDropdownForOrganizationAdministrator.as_view(), name='establishment-dropdown-for-organization-administrator'),

    path('requested-users-dropdown-for-organization-administrator', RequestedUserDropdownForOrganizationAdministrator.as_view(), name='requested-users-dropdown-for-organization-administrator'),

    path('assigned-users-dropdown-for-organization-administrator', AssignedUserDropdownForOrganizationAdministrator.as_view(), name='assigned-users-dropdown-for-organization-administrator'),

    path('update-service-request-status-for-organization-administrator/<int:pk>', UpdateServiceRequestStatusForOrganizationAdministrator.as_view(), name='update-service-request-status-for-organization-administrator'),

    path('assigned-user-to-service-request-for-organization-administrator/<int:pk>', AssignedUserToServiceRequestForOrganizationAdministrator.as_view(), name='assigned-user-to-service-request-for-organization-administrator'),

    path('assigned-users-to-service-request-dropdown-for-organization-administrator', AssignedUserToServiceRequestDropdownForOrganizationAdministrator.as_view(), name='assigned-users-to-service-request-dropdown-for-organization-administrator'),

    # Service booking common views for both Resident User and Organization Administrator
    path('complete-service-request/<int:pk>', CompleteServiceRequest.as_view(), name='complete-service-request'),

    # Service booking for Organization Administrator
    path('service-bookings-for-employee-list-filter', ServiceBookingsForEmployeeListFilter.as_view(), name='service-bookings-for-employee-list-filter'),

    path('establishment-dropdown-for-employee', EstablishmentDropdownForEmployee.as_view(), name='establishment-dropdown-for-employee'),

    path('requested-users-dropdown-for-employee', RequestedUserDropdownForEmployee.as_view(), name='requested-users-dropdown-for-employee'),

    # Service booking for Employee, Resident User and Organization Administrator
    path('service-request-detail/<int:pk>', ServiceRequestDetail.as_view(), name='service-request-detail'),
]
