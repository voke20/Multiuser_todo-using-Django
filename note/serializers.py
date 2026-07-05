from rest_framework import serializers
from . models import (
    Note,
    NoteShare,
    Category,
    NoteUpload,
    Rating
)


class NoteSerializer(serializers.ModelSerializer):

    owner = serializers.ReadOnlyField(source='owner.email')

    class Meta:

        model = Note
        fields = "__all__"


class NoteShareSerializer(serializers.ModelSerializer):

    note = NoteSerializer()
    target_email = serializers.SerializerMethodField()

    class Meta:

        model = NoteShare
        fields = ['id', 'note', 'target', 'target_email', 'created_at']

    def get_target_email(self, obj):
        """Get target email."""
        return obj.target.email


class NoteShareRequestSerializer(serializers.Serializer):
    """NoteShareRequest Serializers."""

    target = serializers.IntegerField()


class CategorySerializer(serializers.ModelSerializer):
    """Category Serializers."""

    owner = serializers.ReadOnlyField(source='owner.email')
    note = NoteSerializer(many=True, read_only=True)

    class Meta:
        """Category Serializers meta class."""

        model = Category
        fields = "__all__"


class NoteUploadSerializer(serializers.ModelSerializer):
    """NoteUpload Serializers."""

    class Meta:
        """NoteUpload Serializers meta class."""

        model = NoteUpload
        fields = "__all__"
        read_only_fields = ['note', 'uploaded_at']


class SendEmailSerializer(serializers.Serializer):
    """SendEMail Serializers."""

    recipient_email = serializers.EmailField()


class RatingSerializer(serializers.ModelSerializer):
    """Rating Serializers."""

    rating = serializers.IntegerField(
        min_value=1,
        max_value=5
    )

    class Meta:

        model = Rating
        fields = "__all__"
        read_only_fields = [
            'note',
            'user',
            'id',
            'created_at',
            'updated_at'
        ]
