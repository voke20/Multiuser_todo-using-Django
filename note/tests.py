from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Note

# Create your tests here.
class NoteTests(APITestCase):
    
    # Authorization and Token Generation Testing
    def setUp(self):
        self.user = User.objects.create_user(username='testvoke', password='testing123')
        response = self.client.post('/api/auth/login/', {"username": "testvoke", "password": "testing123"}, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    # creating note testing
    def test_create_note(self):
        data = {"title": "Test Note", "content": "Test content", "content_type": "plain_text"}
        response = self.client.post('/api/notes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # Get notes
    def test_get_notes(self):
        response = self.client.get('/api/notes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthorized_access(self):
        self.client.credentials()
        response = self.client.get('/api/notes/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionTests(APITestCase):
    # set ups two users 
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')
        
        # login as user1
        response = self.client.post('/api/auth/login/', {"username": "user1", "password": "testpass123"}, format='json')
        self.token1 = response.data['access']
        
        # login as user2
        response = self.client.post('/api/auth/login/', {"username": "user2", "password": "testpass123"}, format='json')
        self.token2 = response.data['access']

    # checks if user 1 can access user 2 token
    def testuser_cannot_access_others_notes(self):
        # create note as user1
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token1)
        response = self.client.post('/api/notes/', {"title": "User1 Note", "content": "content", "content_type": "plain_text"}, format='json')
        note_id = response.data['id']
        
        # trying to access as user2
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token2)
        response = self.client.get(f'/api/notes/{note_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class SharingTests(APITestCase):
    # sets up two users and user1 creates a note
    def setUp(self):
        self.user1 = User.objects.create_user(username='shareuser1', password='testpass123')
        self.user2 = User.objects.create_user(username='shareuser2', password='testpass123')
        
        response = self.client.post('/api/auth/login/', {"username": "shareuser1", "password": "testpass123"}, format='json')
        self.token1 = response.data['access']
        
        response = self.client.post('/api/auth/login/', {"username": "shareuser2", "password": "testpass123"}, format='json')
        self.token2 = response.data['access']
        
        # create a note as user1
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token1)
        response = self.client.post('/api/notes/', {"title": "Shared Note", "content": "content", "content_type": "plain_text"}, format='json')
        self.note_id = response.data['id']

    # sharing user1 notes with user2
    def test_share_note(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token1)
        response = self.client.post(f'/api/notes/{self.note_id}/share/', {"target": self.user2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # getting user2 to view user1 note
    def test_shared_user_can_view_note(self):
        # share note
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token1)
        self.client.post(f'/api/notes/{self.note_id}/share/', {"target": self.user2.id}, format='json')
        
        # user2 views shared notes
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token2)
        response = self.client.get('/api/notes/shared/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_revoke_sharing(self):
        # user1 share a note with user2
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token1)
        self.client.post(f'/api/notes/{self.note_id}/share/', {"target":self.user2.id}, format='json')

        target_id= self.user2.id
        # user1 deletes shared note 
        response = self.client.delete(f'/api/notes/{self.note_id}/share/{target_id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)