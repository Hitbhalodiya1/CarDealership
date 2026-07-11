from django.urls import path

from .views import (
    VehicleDetailView,
    VehicleListCreateView,
    VehiclePurchaseView,
    VehicleRestockView,
    VehicleSearchView,
)

urlpatterns = [
    # NOTE: /search/ is registered before /<id>/ so "search" is never
    # swallowed by the <int:pk> converter.
    path("search/", VehicleSearchView.as_view(), name="vehicle-search"),
    path("", VehicleListCreateView.as_view(), name="vehicle-list-create"),
    path("<int:pk>/", VehicleDetailView.as_view(), name="vehicle-detail"),
    path("<int:pk>/purchase/", VehiclePurchaseView.as_view(), name="vehicle-purchase"),
    path("<int:pk>/restock/", VehicleRestockView.as_view(), name="vehicle-restock"),
]
