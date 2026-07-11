from rest_framework import serializers

from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id",
            "make",
            "model",
            "category",
            "price",
            "quantity",
            "in_stock",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "in_stock", "created_at", "updated_at"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value


class QuantityActionSerializer(serializers.Serializer):
    """Shared shape for /purchase and /restock: an optional quantity, defaulting to 1."""

    quantity = serializers.IntegerField(min_value=1, default=1)
