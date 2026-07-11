from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from vehicles.models import Vehicle


class VehicleModelTests(TestCase):
    def test_create_vehicle_with_valid_data(self):
        vehicle = Vehicle.objects.create(
            make="Toyota", model="Camry", category=Vehicle.Category.SEDAN, price=Decimal("24999.99"), quantity=5
        )

        self.assertEqual(vehicle.make, "Toyota")
        self.assertEqual(vehicle.quantity, 5)
        self.assertTrue(vehicle.in_stock)

    def test_vehicle_out_of_stock_when_quantity_zero(self):
        vehicle = Vehicle.objects.create(
            make="Honda", model="Civic", category=Vehicle.Category.SEDAN, price=Decimal("21000"), quantity=0
        )

        self.assertFalse(vehicle.in_stock)

    def test_string_representation_includes_make_model_and_category(self):
        vehicle = Vehicle.objects.create(
            make="Ford", model="F-150", category=Vehicle.Category.TRUCK, price=Decimal("35000"), quantity=2
        )

        self.assertEqual(str(vehicle), "Ford F-150 (Truck)")

    def test_price_must_be_positive(self):
        vehicle = Vehicle(make="Kia", model="Rio", category=Vehicle.Category.SEDAN, price=Decimal("0"), quantity=1)

        with self.assertRaises(ValidationError):
            vehicle.full_clean()

    def test_default_ordering_is_by_make_then_model(self):
        Vehicle.objects.create(make="Toyota", model="Camry", price=Decimal("25000"), quantity=1)
        Vehicle.objects.create(make="Audi", model="A4", price=Decimal("40000"), quantity=1)

        makes_in_order = list(Vehicle.objects.values_list("make", flat=True))

        self.assertEqual(makes_in_order, ["Audi", "Toyota"])
