from django.urls import path
from app.establishment.views import (
    EstablishmentCreate,
    EstablishmentDetail,
    EstablishmentList,
    EstablishmentListFilter,
)


urlpatterns = [
    path('', EstablishmentCreate.as_view(), name='establishment-create'),
    path('<int:pk>', EstablishmentDetail.as_view(), name='establishment-detail'),
    path('list/', EstablishmentList.as_view(), name='establishment-list'),
    path('list-filter/', EstablishmentListFilter.as_view(), name='establishment-list-filter'),
]
