from rest_framework import viewsets, permissions
from note.models import (
    Note,
    NoteShare,
    Category,
    NoteUpload,
    FileTypeChoices,
    Rating,
)
from note.serializers import (
    NoteSerializer,
    NoteShareSerializer,
    CategorySerializer,
    NoteUploadSerializer,
    SendEmailSerializer,
    NoteShareRequestSerializer,
    RatingSerializer
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
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import HttpResponse
from django.db.models import Avg
import logging
import magic
import re

logger = logging.getLogger('note')
User = get_user_model()
# Create your views here.


class NoteViewSet(viewsets.ModelViewSet):

    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated, Owner]
    filter_backends = [SearchFilter]
    search_fields = ["title", "content"]
    pagination_class = NotePagination

    def get_queryset(self):
        """Return notes belonging to the requesting user."""
        queryset = Note.objects.filter(owner=self.request.user)
        pinned = self.request.query_params.get('is_pinned', '').lower()
        is_pinned = pinned == "true"
        if is_pinned:
            queryset = queryset.filter(is_pinned=is_pinned)
        category = self.request.query_params.get('category', None)
                
        if category is not None:
            queryset = queryset.filter(category=category)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        logger.info(f'Note created by {self.request.user.email}')

    def perform_destroy(self, instance):
        """Delete logs."""
        logger.info(f'Note {instance.id} deleted by {self.request.user.email}')
        instance.delete()


class CategoryViewSet(viewsets.ModelViewSet):

    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CategoryPagination

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class NoteShareViewSet(APIView):

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


class DeleteShareView(APIView):

    @extend_schema(request=NoteShareSerializer)
    def delete(self, request, id, target_id):
        share = NoteShare.objects.filter(
            note__id=id,
            note__owner=request.user,
            target=target_id,
        )
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

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        shares = NoteShare.objects.filter(note__owner=request.user)
        serializer = NoteShareSerializer(shares, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class SharedNotesView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notes = Note.objects.filter(shares__target=request.user)
        serializer = NoteSerializer(notes, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class NoteUploadViewSet(APIView):

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
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        note = get_object_or_404(Note, id=id, owner=request.user)
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
        uploads = NoteUpload.objects.filter(note__id=id, note__owner=request.user)
        serializer = NoteUploadSerializer(uploads, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class SendNoteEmailView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=SendEmailSerializer)
    def post(self, request, id):
        recipient_email = request.data.get("recipient_email")
        include_attachments = request.data.get("include_attachments", False)
        if not recipient_email:
            return Response(
                {"error": "Recipient email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        note = get_object_or_404(Note, id=id)
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
            reply_to=[note.owner.email],
        )
        email.content_subtype = 'html'
        if include_attachments:
            uploads = NoteUpload.objects.filter(note=note)
            for upload in uploads:
                try:
                    with upload.file.open('rb') as f:
                        email.attach(upload.file.name, f.read(),
                                     upload.file.field.content_type)
                except Exception as e:
                    logger.error(f"Failed to attach {upload.file.name}: {e}")
        email.send()
        return Response(
            {"message": "Note sent via email successfully"},
            status=status.HTTP_200_OK,
        )


class RateNoteView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=RatingSerializer)
    def post(self, request, id):
        note = get_object_or_404(Note, id=id)
        if note.owner == request.user:
            return Response(
                {"error": "You cannot rate your own note"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not NoteShare.objects.filter(
            note=note,
            target=request.user
        ).exists():
            return Response(
                {"error": "This note was not shared to you"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = RatingSerializer(data=request.data)
        
        if serializer.is_valid():
            rating, created = Rating.objects.update_or_create(
                note=note,
                user=request.user,
                defaults={
                    'rating': serializer.validated_data['rating']
                }
            )
            return Response(
                {
                    "message": (
                        "Rating created"
                        if created
                        else "Rating Updated"
                    )
                },
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request, id):
        """Get note average rating."""
        note = get_object_or_404(Note, id=id)
        ratings = Rating.objects.filter(note=note)
        avg_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
        return Response({
            'average_rating': round(avg_rating, 1),
            'total_ratings': ratings.count(),
        }, status=status.HTTP_200_OK)


class DownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: "PDF file"})
    def get(self, request, id):
        note = None
        try:
            note = Note.objects.get(id=id, owner=request.user)
        except Note.DoesNotExist:
            # Check if shared with user
            share = NoteShare.objects.filter(
                note_id=id,
                target=request.user
            ).first()
            if share:
                note = share.note
            else:
                return Response(
                    {"error": "Note not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Strip HTML tags
        clean_content = re.sub(r'<[^>]+>', '', note.content)

        # Create PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{note.title}.pdf"'

        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter

        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, note.title)

        # Meta info
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 70, f"By: {note.owner.email}")
        p.drawString(50, height - 85, f"Created: {note.created_at.strftime('%B %d, %Y')}")

        # Content
        p.setFont("Helvetica", 12)
        y = height - 120

        # Word wrap content
        words = clean_content.split()
        line = ""
        for word in words:
            if len(line + word) < 80:
                line += word + " "
            else:
                p.drawString(50, y, line)
                y -= 20
                line = word + " "
                if y < 50:
                    p.showPage()
                    y = height - 50

        if line:
            p.drawString(50, y, line)

        p.showPage()
        p.save()

        return response
