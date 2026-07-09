"""Authenticate Urls."""
from django.urls import path
from authenticate import views
from rest_framework_simplejwt.views import TokenRefreshView

# tokenobtainview handles login and returns access + refresh tokens
# TokenRefreshView handles token refresh

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomTokenView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('search/', views.SearchUserView.as_view(), name='search-user'),
    path('google/', views.GoogleAuthView.as_view(), name='google-auth'),
    path('google/callback/', views.GoogleCallbackView.as_view(), name='google-callback'),
]
