from rest_framework import serializers
from django.contrib.auth.models import User
from . models import Note

class NoteSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    class Meta:
        model = Note
        fields ="__all__"