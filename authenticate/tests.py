"""Testing."""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class AuthTests(APITestCase):
    """Testing Auth."""

    def test_register(self):
        """Register Testing."""
        data = {
            "email": "test@example.com",
            "password": "test123",
            "first_name": "test",
            "last_name": "user"
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Registered Successfully')

    def test_register_invalid(self):
        """Invalid email testing."""
        data = {
            "email": "invalidemail",
            "password": "testpass123",
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        """Login testing."""
        User.objects.create_user(
            email='testvoke@gmail.com',
            password='testing123',
            first_name='test',
            last_name='user'
        )
        data = {"email": "testvoke@gmail.com", "password": "testing123"}
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('email', response.data)
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)

    def test_login_wrong_password(self):
        """Wrong password testing."""
        User.objects.create_user(
            email='testvoke@gmail.com',
            password='testing123',
            first_name='test',
            last_name='user'
        )
        data = {"email": "testvoke@gmail.com", "password": "wrongpassword"}
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout(self):
        """Logout testing."""
        User.objects.create_user(
            email='testvoke@gmail.com',
            password='testing123',
            first_name='test',
            last_name='user'
        )
        login_response = self.client.post('/api/auth/login/', {
            'email': 'testvoke@gmail.com',
            'password': 'testing123'
        }, format='json')
        refresh_token = login_response.data['refresh']
        response = self.client.post('/api/auth/logout/', {
            'refresh': refresh_token
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Logged Out Successful')
