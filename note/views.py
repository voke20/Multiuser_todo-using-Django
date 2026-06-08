from django.shortcuts import render
from rest_framework import viewsets, permissions
from . models import Note, NoteShare, Category, NoteUpload
from . serializers import NoteSerializer, NoteShareSerializer, CategorySerializer, NoteUploadSerializer, SendEmailSerializer, NoteShareRequestSerializer
from . permissions import Owner
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.filters import SearchFilter
from django.core.mail import send_mail
from django.conf import settings
import magic

User = get_user_model()
# Create your views here.
class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated, Owner]
    filter_backends = [SearchFilter]
    search_fields = ['title', 'content']
    def get_queryset(self):
        return Note.objects.filter(owner=self.request.user)
    def perform_create(self, serializer):
        serializer.save(owner = self.request.user)
    
    
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
# for sharing a note
class NoteShareViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(request=NoteShareRequestSerializer)
    def post(self, request, id):
        note = get_object_or_404(Note, id=id)
        if (note.owner != request.user):
            return Response({"error": "You dont own this note"}, status=status.HTTP_403_FORBIDDEN)
        target = User.objects.get(id=request.data['target'])
        NoteShare.objects.create(note=note, target=target)
        return Response({"message": "Note shared successfully"}, status=status.HTTP_201_CREATED)

# for deleting a shared note
class RevokeShareView(APIView):
    @extend_schema(request=NoteShareSerializer)
    def delete(self, request, id, target_id):
        note = get_object_or_404(Note, id=id)
        if(note.owner != request.user):
            return Response({"error": "you do not own this note"}, status=status.HTTP_403_FORBIDDEN)
        share = get_object_or_404(NoteShare, note=note, target=target_id)
        share.delete()
        return Response({"message": "Shared note deleted successfully"}, status= status.HTTP_200_OK)

# for getting all notes user have shared
class MySharedNotesView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        shares = NoteShare.objects.filter(note__owner=request.user)
        serializer = NoteShareSerializer(shares, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# for getting notes being shared to me
class SharedNoteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        notes = Note.objects.filter(shares__target=request.user)
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NoteUploadViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'},
                }
            }
        }
    )
    
    def post(self, request, id):
        note = get_object_or_404(Note, id=id, owner=request.user)
        file = request.FILES.get('file')
        
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # auto detect file type
        file_type = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # reset file pointer after reading
        
        # validate file type
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf', 'text/plain']
        if file_type not in allowed_types:
            return Response({"error": f"File type {file_type} not allowed"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = NoteUploadSerializer(data={'file': file, 'file_type': file_type})
        if serializer.is_valid():
            serializer.save(note=note)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses=NoteUploadSerializer(many=True))
    def get(self, request, id):
        note = get_object_or_404(Note, id=id, owner=request.user)
        uploads = NoteUpload.objects.filter(note=note)
        serializer = NoteUploadSerializer(uploads, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SendNoteEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=SendEmailSerializer)
    def post(self, request, id):
        note = get_object_or_404(Note, id=id)
        recipient_email = request.data.get('recipient_email')

        if not recipient_email:
            return Response({"error": "Recipient email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        send_mail(
            subject= f"Note sent to you: {note.title}",
            message= f"""
            {note.owner.email} sent you a note.

            Title: {note.title}

            Content: {note.content}
            
            Sent Via Multiuser NoteApp
            """,
            from_email= settings.EMAIL_HOST_USER,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return Response({"message": "Note sent via email successfully"}, status=status.HTTP_200_OK)
                
    
