from django.urls import path, include
from rest_framework import routers
from . import views


router = routers.DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='category')
router.register('', views.NoteViewSet, basename='note')




urlpatterns = [
    path('myshared/', views.MySharedNotesView.as_view(), name='my-shared-notes'),
    path('shared/', views.SharedNoteView.as_view(), name='shared-notes'),
    path('', include(router.urls)),
    path('<int:id>/share/', views.NoteShareViewSet.as_view(), name='note-share'),
    path('<int:id>/share/<int:target_id>/', views.RevokeShareView.as_view(), name= "note-share-delete"),
    path('<int:id>/uploads/', views.NoteUploadViewSet.as_view(), name='note-uploads'),
    path('<int:id>/send-email/', views.SendNoteEmailView.as_view(), name='send-note-email')
]