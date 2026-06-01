from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Note(models.Model):

    Content_Type_Choices = [
        ('plain_text', 'Plain Text'),
        ('markdown', 'Markdown'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    content_type = models.CharField(max_length=20, choices=Content_Type_Choices, default='plain_text')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.owner.username}"

class NoteShare(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    target = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.note.title} shared with {self.target.username} by {self.note.owner.username}"