from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Note, Category, Rating, NoteSharedHistory
from django.urls import reverse


User = get_user_model()
# Create your tests here.


class NoteTests(APITestCase):
    """Testing Notes."""

    def setUp(self):
        """Get Token Generation Testing."""
        self.user = User.objects.create_user(
            email="testvoke@gmail.com",
            password="testing123",
            first_name="Test",
            last_name="user",
        )
        response = self.client.post(
            "/api/auth/login/",
            {"email": "testvoke@gmail.com", "password": "testing123"},
            format="json",
        )
        self.token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

        self.category = Category.objects.create(
            name='Work',
            owner=self.user,
        )

    # creating note testing
    def test_create_note(self):
        """Test create note."""
        data = {
            "title": "Test Note",
            "content": "Test content",
            "content_type": "plain_text",
            "is_pinned": False,
        }
        response = self.client.post("/api/notes/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Test Note")
        self.assertEqual(response.data["content"], "Test content")
        self.assertEqual(response.data["owner"], "testvoke@gmail.com")

    def test_create_note_by_category(self):
        """Test create note with category."""
        data = {
            "title": "Test Note",
            "content": "Test content",
            "content_type": "plain_text",
            "is_pinned": False,
            "category": self.category.id,
        }
        response = self.client.post("/api/notes/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Test Note")
        self.assertEqual(response.data['category'], self.category.id)

    def test_filter_notes_by_category(self):
        """Get notes by category."""
        Note.objects.create(
            title="Work Note",
            content="Content",
            content_type="plain_text",
            owner=self.user,
            category=self.category,
        )
        Note.objects.create(
            title="Personal Note",
            content="Content",
            content_type="plain_text",
            owner=self.user,
        )
        response = self.client.post(
            f"/api/notes/?category={self.category.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_notes(self):
        """Get notes."""
        response = self.client.get("/api/notes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("total_pages", response.data)
        self.assertIn("current_page", response.data)

    def test_get_notes_by_id(self):
        """Get notes by id."""
        note = Note.objects.create(
            title="Test Note",
            content="Test content",
            content_type="plain_text",
            owner=self.user,
        )
        response = self.client.get(f"/api/notes/{note.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test Note")
        self.assertEqual(response.data["id"], note.id)

    def test_update_note(self):
        """Update note."""
        note = Note.objects.create(
            title="Old Title",
            content="Old Content",
            content_type="plain_text",
            owner=self.user,
        )
        data = {"title": "New Title"}
        response = self.client.patch(
            f"/api/notes/{note.id}/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "New Title")

    def test_delete_note(self):
        """Delete note."""
        note = Note.objects.create(
            title="Test Note",
            content="Test content",
            content_type="plain_text",
            owner=self.user,
        )
        response = self.client.delete(f"/api/notes/{note.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_unauthorized_access(self):
        """Test Unauthorized access."""
        self.client.credentials()
        response = self.client.get("/api/notes/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_google_drive_upload_url_resolves(self):
        """Google Drive upload route should resolve correctly."""
        url = reverse("google-drive-upload", kwargs={"id": 1})
        self.assertEqual(url, "/api/notes/1/drive/")

    def test_google_drive_upload_requires_google_connection(self):
        """Drive upload should explain when Google Drive is not connected."""
        note = Note.objects.create(
            title="Drive Note",
            content="Content",
            content_type="plain_text",
            owner=self.user,
        )
        response = self.client.post(f"/api/notes/{note.id}/drive/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Please connect Google Drive first", response.data["error"])
        self.assertIn("auth_url", response.data)
        self.assertTrue(response.data["auth_url"].startswith("https://accounts.google.com/o/oauth2/auth"))

    def test_onedrive_upload_url_resolves(self):
        """OneDrive upload route should resolve correctly."""
        url = reverse("onedrive-upload", kwargs={"id": 1})
        self.assertEqual(url, "/api/notes/1/onedrive/")

    def test_onedrive_upload_requires_onedrive_connection(self):
        """OneDrive upload should explain when OneDrive is not connected."""
        note = Note.objects.create(
            title="OneDrive Note",
            content="Content",
            content_type="plain_text",
            owner=self.user,
        )
        response = self.client.post(f"/api/notes/{note.id}/onedrive/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Please connect OneDrive first", response.data["error"])
        self.assertIn("auth_url", response.data)
        self.assertTrue(
            response.data["auth_url"].startswith(
                "https://login.microsoftonline.com/"
            )
        )

    def test_pinned_notes(self):
        """Get pinned notes."""
        Note.objects.create(
            title="Pinned Note",
            content="Content",
            content_type="plain_type",
            owner=self.user,
            is_pinned=True,
        )
        Note.objects.create(
            title="Normal Note",
            content="Content",
            content_type="plain_text",
            owner=self.user,
            is_pinned=False,
        )
        response = self.client.get("/api/notes/?is_pinned=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Pinned Note")

    def test_shared_history_endpoint_returns_list(self):
        """The shared-history route should resolve to the history view."""
        response = self.client.get("/api/notes/shared-history/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_sharing_note_creates_history_entry(self):
        """Sharing a note should appear in the shared-history endpoint."""
        target_user = User.objects.create_user(
            email="target@example.com",
            password="secret123",
        )
        note = Note.objects.create(
            title="Share Me",
            content="Content",
            content_type="plain_text",
            owner=self.user,
        )

        response = self.client.post(
            f"/api/notes/{note.id}/share/",
            {"target": target_user.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            NoteSharedHistory.objects.filter(note=note).exists()
        )

        history_response = self.client.get("/api/notes/shared-history/")
        self.assertEqual(history_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(history_response.data), 1)
        self.assertEqual(history_response.data[0]["note"], note.id)


class CategoryTest(APITestCase):
    """Category Testing."""

    def setUp(self):
        """Get users token."""
        self.user = User.objects.create_user(
            email="testvoke@gmail.com",
            password="testpass123",
        )
        response = self.client.post(
            "/api/auth/login/",
            {"email": "testvoke@gmail.com", "password": "testpass123"},
            format="json",
        )
        self.token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

    def test_create_category(self):
        """Create category."""
        data = {"name": "Work"}
        response = self.client.post(
            "/api/notes/categories/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Work")

    def test_get_categories(self):
        """Get Category."""
        response = self.client.get("/api/notes/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_category(self):
        """Delete Category."""
        category = Category.objects.create(
            name="Work",
            owner=self.user,
        )
        response = self.client.delete(f"/api/notes/categories/{category.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class PermissionTests(APITestCase):
    """Get ups two users."""

    def setUp(self):
        """Get users token."""
        self.user1 = User.objects.create_user(
            "user1@gmail.com", "testpass123"
        )
        self.user2 = User.objects.create_user(
            "user2@gmail.com", "testpass123"
        )

        # login as user1
        response = self.client.post(
            "/api/auth/login/",
            {"email": "user1@gmail.com", "password": "testpass123"},
            format="json",
        )
        self.token1 = response.data['access']

        # login as user2
        response = self.client.post(
            "/api/auth/login/",
            {"email": "user2@gmail.com", "password": "testpass123"},
            format="json",
        )
        self.token2 = response.data['access']

    # checks if user 1 can access user 2 token
    def testuser_cannot_access_others_notes(self):
        """Create note as user1."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token1)
        note = Note.objects.create(
            title="User1 Note",
            content="Content",
            content_type="plain_text",
            owner=self.user1,
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token2)
        response = self.client.get(f"/api/notes/{note.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def testuser_cannot_delete_others_notes(self):
        """Create note as user1."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token1)
        note = Note.objects.create(
            title="User1 Note",
            content="Content",
            content_type="plain_text",
            owner=self.user1,
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token2)
        response = self.client.delete(f"/api/notes/{note.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SharingTests(APITestCase):
    """Gets up two users and user1 creates a note."""

    def setUp(self):
        """Get user token."""
        self.user1 = User.objects.create_user(
            "user1@gmail.com", "testpass123"
        )
        self.user2 = User.objects.create_user(
            "user2@gmail.com", "testpass123"
        )

        # login as user1
        response = self.client.post(
            "/api/auth/login/",
            {"email": "user1@gmail.com", "password": "testpass123"},
            format="json",
        )
        self.token1 = response.data['access']

        # login as user2
        response = self.client.post(
            "/api/auth/login/",
            {"email": "user2@gmail.com", "password": "testpass123"},
            format="json",
        )
        self.token2 = response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token1)
        self.note = Note.objects.create(
            title="Shared Note",
            content="Content",
            content_type="plain_text",
            owner=self.user1,
        )
        self.note_id = self.note.id

    def test_share_note(self):
        """Share user1 notes with user2."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token1)
        response = self.client.post(
            f"/api/notes/{self.note.id}/share/",
            {"target": self.user2.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "Note shared successfully")

    def test_shared_user_can_view_note(self):
        """Share note."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token1)
        self.client.post(
            f"/api/notes/{self.note.id}/share/",
            {"target": self.user2.id},
            format="json",
        )

        # user2 views shared notes
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token2)
        response = self.client.get("/api/notes/shared/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_revoke_sharing(self):
        """User1 share a note with user2."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token1)
        self.client.post(
            f"/api/notes/{self.note.id}/share/",
            {"target": self.user2.id},
            format="json",
        )

        target_id = self.user2.id
        # user1 deletes shared note
        response = self.client.delete(
            f"/api/notes/{self.note_id}/share/{target_id}/", format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Shared note deleted successfully"
            )


