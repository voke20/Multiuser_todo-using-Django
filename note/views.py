"""Note views."""
from rest_framework import viewsets, permissions
from note.models import Note, NoteShare, Category, NoteUpload, FileTypeChoices
from note.serializers import (
    NoteSerializer,
    NoteShareSerializer,
    CategorySerializer,
    NoteUploadSerializer,
    SendEmailSerializer,
    NoteShareRequestSerializer,
)
from note.permissions import Owner
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.filters import SearchFilter
from django.core.mail import EmailMessage
from django.conf import settings
from note.pagination import NotePagination, CategoryPagination
from django.template.loader import render_to_string
import logging
import magic
import re

logger = logging.getLogger('note')
User = get_user_model()
# Create your views here.


class NoteViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for user's notes."""

    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated, Owner]
    filter_backends = [SearchFilter]
    search_fields = ["title", "content"]
    pagination_class = NotePagination

    def get_queryset(self):
        """Return notes belonging to the requesting user."""
        queryset = Note.objects.filter(owner=self.request.user)
        is_pinned = self.request.query_params.get('is_pinned', None)
        category = self.request.query_params.get('category', None)
        if is_pinned is not None:
            queryset = queryset.filter(is_pinned=is_pinned.lower() == 'true')
        if category is not None:
            queryset = queryset.filter(category=category)
        return queryset

    def perform_create(self, serializer):
        """Save a new note setting the owner to the requester."""
        serializer.save(owner=self.request.user)
        logger.info(f'Note created by {self.request.user.email}')

    def perform_destroy(self, instance):
        """Delete logs."""
        logger.info(f'Note {instance.id} deleted by {self.request.user.email}')
        instance.delete()


class CategoryViewSet(viewsets.ModelViewSet):
    """Category Views."""

    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CategoryPagination

    def get_queryset(self):
        """Return categories owned by the requesting user."""
        return Category.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """Save a new category setting the owner to the requester."""
        serializer.save(owner=self.request.user)


class NoteShareViewSet(APIView):
    """Endpoint for sharing a note with another user."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=NoteShareRequestSerializer)
    def post(self, request, id):
        """Share a note owned by the requester with a target user."""
        note = get_object_or_404(Note, id=id)
        if note.owner != request.user:
            return Response(
                {"error": "You dont own this note"},
                status=status.HTTP_403_FORBIDDEN,
            )
        target = User.objects.get(id=request.data["target"])
        NoteShare.objects.create(note=note, target=target)
        return Response(
            {"message": "Note shared successfully"},
            status=status.HTTP_201_CREATED,
        )


class RevokeShareView(APIView):
    """Endpoint to revoke a previously created note share."""

    @extend_schema(request=NoteShareSerializer)
    def delete(self, request, id, target_id):
        """Remove a share record for a note owned by the requester."""
        note = get_object_or_404(Note, id=id)
        if note.owner != request.user:
            return Response(
                {"error": "you do not own this note"},
                status=status.HTTP_403_FORBIDDEN,
            )
        share = NoteShare.objects.filter(note=note, target=target_id)
        if not share.exists():
            return Response(
                {"error": "Share record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        share.delete()
        return Response(
            {"message": "Shared note deleted successfully"},
            status=status.HTTP_200_OK,
        )


class MySharedNotesView(APIView):
    """Endpoint for viewing shared notes."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get shared notes."""
        shares = NoteShare.objects.filter(note__owner=request.user)
        serializer = NoteShareSerializer(shares, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class SharedNoteView(APIView):
    """Endpoint for viewing shared notes."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get shared notes."""
        notes = Note.objects.filter(shares__target=request.user)
        serializer = NoteSerializer(notes, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class NoteUploadViewSet(APIView):
    """Noteupload views."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                },
            }
        }
    )
    def post(self, request, id):
        """Upload files."""
        note = get_object_or_404(Note, id=id, owner=request.user)
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        file_type = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)
        Allowed_Types = [choice[0] for choice in FileTypeChoices]
        if file_type not in Allowed_Types:
            return Response(
                {"error": f"File type {file_type} not allowed"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = NoteUploadSerializer(
            data={"file": file, "file_type": file_type}
        )
        if serializer.is_valid():
            serializer.save(note=note)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses=NoteUploadSerializer(many=True))
    def get(self, request, id):
        """Get user uploads."""
        note = get_object_or_404(Note, id=id, owner=request.user)
        uploads = NoteUpload.objects.filter(note=note)
        serializer = NoteUploadSerializer(uploads, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class SendNoteEmailView(APIView):
    """Send Note by email."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=SendEmailSerializer)
    def post(self, request, id):
        """Send note email."""
        note = get_object_or_404(Note, id=id)
        recipient_email = request.data.get("recipient_email")
        include_attachments = request.data.get("include_attachments", False)
        if not recipient_email:
            return Response(
                {"error": "Recipient email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        clean_content = re.sub(r"<[^>]+>", "", note.content)
        html_content = render_to_string('email/sendemail.html', {
            'title': note.title,
            'content': clean_content,
            'link': 'http://localhost:5173/register',
            'sender': note.owner.email
        })
        email = EmailMessage(
            subject=f"Note shared with you: {note.title}",
            body=(html_content),
            from_email=settings.EMAIL_HOST_USER,
            to=[recipient_email],
        )
        email.content_subtype = 'html'
        if include_attachments:
            uploads = NoteUpload.objects.filter(note=note)
            for upload in uploads:
                try:
                    email.attach_file(upload.file.path)
                except Exception:
                    pass
        email.send()
        return Response(
            {"message": "Note sent via email successfully"},
            status=status.HTTP_200_OK,
        )

