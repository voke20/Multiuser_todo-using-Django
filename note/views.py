from django.shortcuts import render
from rest_framework import viewsets, permissions
from . models import Note
from . serializers import NoteSerializer
from . permissions import Owner

# Create your views here.
class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated, Owner]
    def get_queryset(self):
        return Note.objects.filter(owner=self.request.user)
    def perform_create(self, serializer):
        serializer.save(owner = self.request.user)
