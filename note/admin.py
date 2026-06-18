"""Note admin.py."""
from django.contrib import admin
from . models import Note, NoteShare, Category
# Register your models here.
admin.site.register(Note)
admin.site.register(NoteShare)
admin.site.register(Category)