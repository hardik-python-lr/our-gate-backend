from django.urls import path
from app.role.views import (
    RoleList,
)

urlpatterns = [
    path('list/', RoleList.as_view(), name='role-list'),
]
