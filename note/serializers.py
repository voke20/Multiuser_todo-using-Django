from rest_framework import serializers
from django.conf import settings
from . models import Note, NoteShare, Category, NoteUpload



class NoteSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.email.split("@")[0]')
    class Meta:
        model = Note
        fields ="__all__"

class NoteShareSerializer(serializers.ModelSerializer):
    note= NoteSerializer()
    class Meta:
        model = NoteShare
        fields = ["id", "note", "target", "created_at"]

class NoteShareRequestSerializer(serializers.Serializer):
    target = serializers.IntegerField()

class CategorySerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.email')
    note = NoteSerializer(many=True, read_only=True)
    class Meta:
        model = Category
        fields = "__all__"
    
class NoteUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteUpload
        fields = "__all__"
        read_only_fields = ['note', 'uploaded_at']

class SendEmailSerializer(serializers.Serializer):
    recipient_email = serializers.EmailField()
