from django.shortcuts import render
from rest_framework import viewsets, permissions
from . models import Note, NoteShare
from . serializers import NoteSerializer, NoteShareSerializer
from . permissions import Owner
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from django.contrib.auth.models import User
from rest_framework import status

# Create your views here.
class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated, Owner]
    def get_queryset(self):
        return Note.objects.filter(owner=self.request.user)
    def perform_create(self, serializer):
        serializer.save(owner = self.request.user)
    
# for sharing a note
class NoteShareViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(request=NoteShareSerializer)
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
        shares = NoteShare.objects.filter(target=request.user)
        notes = []
        for share in shares:
            notes.append(share.note)

        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

