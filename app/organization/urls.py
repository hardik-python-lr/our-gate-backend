from django.urls import path
from app.organization.views import (
    OrganizationCreate,
    OrganizationDetail,
    OrganizationList,
    OrganizationListFilter,
)


urlpatterns = [
    path('', OrganizationCreate.as_view(), name='organization-create'),
    path('<int:pk>', OrganizationDetail.as_view(), name='organization-detail'),
    path('list/', OrganizationList.as_view(), name='organization-list'),
    path('list-filter/', OrganizationListFilter.as_view(), name='organization-list-filter'),
]
