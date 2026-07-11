from django.db import transaction
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Vehicle
from .permissions import IsAdmin
from .serializers import QuantityActionSerializer, VehicleSerializer


class VehicleListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/vehicles/  -> list all vehicles (any authenticated user)
    POST /api/vehicles/  -> add a new vehicle (any authenticated user)
    """

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/vehicles/<id>/ -> retrieve a single vehicle
    PUT    /api/vehicles/<id>/ -> update a vehicle
    PATCH  /api/vehicles/<id>/ -> partial update
    DELETE /api/vehicles/<id>/ -> admin only
    """

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated()]


class VehicleSearchView(generics.ListAPIView):
    """
    GET /api/vehicles/search/?make=&model=&category=&min_price=&max_price=

    All filters are optional and can be combined. `make`/`model` do a
    case-insensitive partial match; `category` is an exact match against
    the Vehicle.Category choices.
    """

    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Vehicle.objects.all()
        params = self.request.query_params

        make = params.get("make")
        model = params.get("model")
        category = params.get("category")
        min_price = params.get("min_price")
        max_price = params.get("max_price")

        if make:
            queryset = queryset.filter(make__icontains=make)
        if model:
            queryset = queryset.filter(model__icontains=model)
        if category:
            queryset = queryset.filter(category__iexact=category)
        if min_price is not None:
            queryset = queryset.filter(price__gte=self._parse_decimal("min_price", min_price))
        if max_price is not None:
            queryset = queryset.filter(price__lte=self._parse_decimal("max_price", max_price))

        return queryset

    @staticmethod
    def _parse_decimal(field_name, raw_value):
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            raise ValidationError({field_name: "Must be a number."})


class VehiclePurchaseView(APIView):
    """POST /api/vehicles/<id>/purchase/ — decreases quantity (any authenticated user)."""

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        vehicle = generics.get_object_or_404(Vehicle, pk=pk)
        action = QuantityActionSerializer(data=request.data)
        action.is_valid(raise_exception=True)
        amount = action.validated_data["quantity"]

        if vehicle.quantity < amount:
            return Response(
                {"detail": "Not enough stock to complete this purchase."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        vehicle.quantity -= amount
        vehicle.save(update_fields=["quantity", "updated_at"])
        return Response(VehicleSerializer(vehicle).data, status=status.HTTP_200_OK)


class VehicleRestockView(APIView):
    """POST /api/vehicles/<id>/restock/ — increases quantity (admin only)."""

    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    @transaction.atomic
    def post(self, request, pk):
        vehicle = generics.get_object_or_404(Vehicle, pk=pk)
        action = QuantityActionSerializer(data=request.data)
        action.is_valid(raise_exception=True)
        amount = action.validated_data["quantity"]

        vehicle.quantity += amount
        vehicle.save(update_fields=["quantity", "updated_at"])
        return Response(VehicleSerializer(vehicle).data, status=status.HTTP_200_OK)
