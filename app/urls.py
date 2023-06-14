# Package and Swagger imports
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
   openapi.Info(
       title="VMS API",
       default_version='v1',
       description="VMS API Documentation",
       terms_of_service="https://www.google.com/policies/terms/",
       contact=openapi.Contact(email="contact@snippets.local"),
       license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # App URLs
    path('api/users/', include('app.users.urls')),
    path('api/employeecategory/', include('app.employeecategory.urls')),
    path('api/organization/', include('app.organization.urls')),
    path('api/establishment/', include('app.establishment.urls')),
    path('api/services/', include('app.services.urls')),
    path('api/building/', include('app.building.urls')),
    path('api/flat/', include('app.flat.urls')),
    path('api/announcement/', include('app.announcement.urls')),
    path('api/amenity/', include('app.amenity.urls')),
    path('api/visitor/', include('app.visitor.urls')),
    path('api/mobile/', include('app.mobile.urls')),
    path('api/attendance/', include('app.attendance.urls')),
    path('api/service-booking/', include('app.service_booking.urls')),
    path('api/amenity-booking/', include('app.amenity_booking.urls')),
    path('api/vehicle/', include('app.vehicle.urls')),
    path('api/role/', include('app.role.urls')),
    path('api/bill_payment/', include('app.bill_payment.urls')),

    # Debugging
    path('debuger/', include(debug_toolbar.urls)),

    # Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
