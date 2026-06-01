from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

# Create your tests here.
class AuthTests(APITestCase):
    
    # Register Testing
    def test_register(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "test123"
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # Login testing
    def test_login(self):
        User.objects.create_user(username='testvoke', password='testing123')
        data = {"username": "testvoke", "password": "testing123"}
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

