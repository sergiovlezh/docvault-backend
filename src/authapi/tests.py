from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class AuthApiTests(APITestCase):
    def setUp(self):
        self.username = "TestUser"
        self.password = "TestPass123"
        self.user = User.objects.create_user(
            username=self.username, password=self.password
        )
        self.client = APIClient()

    def test_login_success(self):
        # --- Arrange
        url = reverse("auth-login")

        # --- Act
        response = self.client.post(
            url, {"username": self.username, "password": self.password}
        )

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("login", response.json()["message"].lower())

        # Verify session cookie was set
        self.assertIn("sessionid", response.cookies)

    def test_login_invalid_credentials(self):
        # --- Arrange
        url = reverse("auth-login")

        # --- Act
        response = self.client.post(
            url, {"username": self.username, "password": "wrongpass"}
        )

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.json())

    def test_whoami_requires_authentication(self):
        # --- Arrange
        url = reverse("auth-whoami")

        # --- Act
        response = self.client.get(url)

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.json())

    def test_whoami_authenticated(self):
        # --- Arrange
        self.client.login(username=self.username, password=self.password)
        url = reverse("auth-whoami")

        # --- Act
        response = self.client.get(url)

        # --- Assert
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["username"], self.username)

    def test_logout(self):
        # --- Arrange
        self.client.login(username=self.username, password=self.password)
        url = reverse("auth-logout")

        # --- Act
        response = self.client.post(url)

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("logged out", response.json()["message"].lower())
