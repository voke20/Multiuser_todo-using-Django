from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# tokenobtainview handles login and returns access + refresh tokens
# TokenRefreshView handles token refresh

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name = 'register' ),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name = 'logout'),
]
