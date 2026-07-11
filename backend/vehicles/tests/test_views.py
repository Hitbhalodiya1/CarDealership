from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from vehicles.models import Vehicle

User = get_user_model()


def make_vehicle(**overrides):
    defaults = {
        "make": "Toyota",
        "model": "Corolla",
        "category": Vehicle.Category.SEDAN,
        "price": Decimal("22000.00"),
        "quantity": 3,
    }
    defaults.update(overrides)
    return Vehicle.objects.create(**defaults)


class VehicleListCreateTests(APITestCase):
    def setUp(self):
        self.url = reverse("vehicle-list-create")
        self.customer = User.objects.create_user(username="customer1", password="pw12345678")
        self.admin = User.objects.create_user(username="admin1", password="pw12345678", role=User.Role.ADMIN)

    def test_anonymous_user_cannot_list_vehicles(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_customer_can_list_vehicles(self):
        make_vehicle()
        self.client.force_authenticate(self.customer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_authenticated_user_can_create_vehicle(self):
        self.client.force_authenticate(self.customer)
        payload = {"make": "Mazda", "model": "CX-5", "category": "suv", "price": "28000.00", "quantity": 4}

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vehicle.objects.count(), 1)

    def test_create_vehicle_rejects_negative_price(self):
        self.client.force_authenticate(self.customer)
        payload = {"make": "Mazda", "model": "CX-5", "category": "suv", "price": "-100", "quantity": 4}

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class VehicleDetailTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="customer2", password="pw12345678")
        self.admin = User.objects.create_user(username="admin2", password="pw12345678", role=User.Role.ADMIN)
        self.vehicle = make_vehicle()
        self.url = reverse("vehicle-detail", args=[self.vehicle.id])

    def test_authenticated_user_can_update_vehicle(self):
        self.client.force_authenticate(self.customer)

        response = self.client.put(
            self.url,
            {"make": "Toyota", "model": "Corolla", "category": "sedan", "price": "23000.00", "quantity": 2},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.price, Decimal("23000.00"))

    def test_non_admin_cannot_delete_vehicle(self):
        self.client.force_authenticate(self.customer)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Vehicle.objects.filter(id=self.vehicle.id).exists())

    def test_admin_can_delete_vehicle(self):
        self.client.force_authenticate(self.admin)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vehicle.objects.filter(id=self.vehicle.id).exists())


class VehiclePurchaseTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="customer3", password="pw12345678")
        self.vehicle = make_vehicle(quantity=2)
        self.url = reverse("vehicle-purchase", args=[self.vehicle.id])

    def test_purchase_decreases_quantity_by_default_one(self):
        self.client.force_authenticate(self.customer)

        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.quantity, 1)

    def test_purchase_can_specify_quantity(self):
        self.client.force_authenticate(self.customer)

        response = self.client.post(self.url, {"quantity": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.quantity, 0)

    def test_purchase_fails_when_insufficient_stock(self):
        self.client.force_authenticate(self.customer)

        response = self.client.post(self.url, {"quantity": 99})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.quantity, 2)

    def test_purchase_requires_authentication(self):
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VehicleRestockTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="customer4", password="pw12345678")
        self.admin = User.objects.create_user(username="admin4", password="pw12345678", role=User.Role.ADMIN)
        self.vehicle = make_vehicle(quantity=1)
        self.url = reverse("vehicle-restock", args=[self.vehicle.id])

    def test_admin_can_restock(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(self.url, {"quantity": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.quantity, 6)

    def test_non_admin_cannot_restock(self):
        self.client.force_authenticate(self.customer)

        response = self.client.post(self.url, {"quantity": 5})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.quantity, 1)
