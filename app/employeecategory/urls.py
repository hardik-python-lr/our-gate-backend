from django.urls import path
from app.employeecategory.views import (
    EmployeeCategoryCreate,
    EmployeeCategoryDetail,
    EmployeeCategoryList,
    EmployeeCategoryListFilter,
)

urlpatterns = [
    path('', EmployeeCategoryCreate.as_view(), name='employee-category-create'),
    path('<int:pk>', EmployeeCategoryDetail.as_view(), name='employee-category-detail'),
    path('list/', EmployeeCategoryList.as_view(), name='employee-category-list'),
    path('list-filter/', EmployeeCategoryListFilter.as_view(), name='employee-category-list-filter'),
]
