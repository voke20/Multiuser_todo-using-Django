"""Note Models."""
from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField


class Note(models.Model):
    """Create note model."""

    Content_Type_Choices = [
        ('plain_text', 'Plain Text'),
        ('markdown', 'Markdown'),
    ]
    title = models.CharField(max_length=200)
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes'
    )
    content = RichTextField()
    content_type = models.CharField(
        max_length=20,
        choices=Content_Type_Choices,
        default='plain_text'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        """Display object."""
        return f"{self.title} - {self.owner.email.split('@')[0]}"


class Category(models.Model):
    """Category models."""

    name = models.CharField(max_length=100)
    description = RichTextField(blank=True, null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        """Display category object."""
        return f"{self.name}"


class NoteShare(models.Model):
    """Noteshare model."""

    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Display Noteshare object."""
        return (
            f"{self.note.title} shared with {self.target.email} "
            f"by {self.note.owner.email}"
        )


class NoteUpload(models.Model):
    """NoteUpload models."""

    File_Type_Choices = [
        ('image/png', 'PNG'),
        ('image/jpeg', 'JPEG'),
        ('image/jpg', 'JPG'),
        ('application/pdf', 'PDF'),
        ('text/plain', 'TXT'),
    ]
    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name="uploads"
    )
    file = models.FileField(upload_to='note_uploads/')
    file_type = models.CharField(max_length=50, choices=File_Type_Choices)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Display NoteUpload object."""
        return f"File for {self.note.title}"
