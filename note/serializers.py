from rest_framework import serializers
from django.contrib.auth.models import User
from . models import Note, NoteShare

class NoteSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    class Meta:
        model = Note
        fields ="__all__"

class NoteShareSerializer(serializers.ModelSerializer):
    note= NoteSerializer()
    class Meta:
        model = NoteShare
        fields = ["id", "note", "target", "created_at"]

