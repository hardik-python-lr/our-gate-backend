from django.urls import path
from app.services.views import (
    # ServiceCategory
    ServiceCategoryCreate,
    ServiceCategoryDetail,
    ServiceCategoryList,
    ServiceCategoryListFilter,

    # ServiceSubCategory
    ServiceSubCategoryCreate,
    ServiceSubCategoryDetail,
    ServiceSubCategoryList,
    ServiceSubCategoryListFilter,

    # Service
    ServiceCreate,
    ServiceDetail,
    ServiceList,
    ServiceListFilter,

    # ServiceSlot
    ServiceSlotCreate,
    ServiceSlotDetail,
    ServiceSlotList,
    ServiceSlotListFilter,

    # ServiceExclusion views
    ServiceExclusionCreate,
    ServiceExclusionDetail,
    ServiceExclusionList,
    ServiceExclusionListFilter,
)


urlpatterns = [
    # ServiceCategory
    path('service-category/', ServiceCategoryCreate.as_view(), name='service-category-create'),
    path('service-category/<int:pk>', ServiceCategoryDetail.as_view(), name='service-category-detail'),
    path('service-category-list/', ServiceCategoryList.as_view(), name='service-category-list'),
    path('service-category-list-filter/', ServiceCategoryListFilter.as_view(), name='service-category-list-filter'),

    # ServiceSubCategory
    path('service-sub-category/', ServiceSubCategoryCreate.as_view(), name='service-sub-category-create'),
    path('service-sub-category/<int:pk>', ServiceSubCategoryDetail.as_view(), name='service-sub-category-detail'),
    path('service-sub-category-list/', ServiceSubCategoryList.as_view(), name='service-sub-category-list'),
    path('service-sub-category-list-filter/', ServiceSubCategoryListFilter.as_view(), name='service-sub-category-list-filter'),

    # Service
    path('', ServiceCreate.as_view(), name='service-create'),
    path('<int:pk>', ServiceDetail.as_view(), name='service-detail'),
    path('service-list/', ServiceList.as_view(), name='service-list'),
    path('service-list-filter/', ServiceListFilter.as_view(), name='service-list-filter'),

    # ServiceSlot
    path('service-slot/', ServiceSlotCreate.as_view(), name='service-slot-create'),
    path('service-slot/<int:pk>', ServiceSlotDetail.as_view(), name='service-slot-detail'),
    path('service-slot-list/', ServiceSlotList.as_view(), name='service-slot-list'),
    path('service-slot-list-filter/', ServiceSlotListFilter.as_view(), name='service-slot-list-filter'),

    # ServiceExclusion
    path('service-exclusion/', ServiceExclusionCreate.as_view(), name='service-exclusion-create'),
    path('service-exclusion/<int:pk>', ServiceExclusionDetail.as_view(), name='service-exclusion-detail'),
    path('service-exclusion/list/', ServiceExclusionList.as_view(), name='service-exclusion-list'),
    path('service-exclusion/list-filter/', ServiceExclusionListFilter.as_view(), name='service-exclusion-list-filter'),
]
