"""Authenticate views."""
from rest_framework.views import APIView
from rest_framework.response import Response
from authenticate.serializers import (
    RegisterSerializer,
    CustomTokenSerializer,
    UserSerializer,
)
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
import logging
logger = logging.getLogger('authenticate')
User = get_user_model()


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='email',
            type=str,
            location=OpenApiParameter.QUERY,
            required=True
            )
    ]
)
class SearchUserView(APIView):
    """Search users."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user."""
        email = request.query_params.get('email', '')
        if not email:
            return Response({"error": "Email is required"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"},
                            status=status.HTTP_404_NOT_FOUND)


@extend_schema(request=RegisterSerializer)
class RegisterView(APIView):
    """Register View."""

    def post(self, request):
        """Create user."""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f'New user registered: {request.data.get("email")}')
            try:
                html_content = render_to_string('email/welcome.html', {
                    'first_name': User.first_name or User.email.split('@')[0],
                })
                email = EmailMessage(
                    subject='Welcome to NoteApp! 🎉',
                    body=html_content,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[request.data.get("email")],
                )
                email.content_subtype = 'html'
                email.send()
                logger.info(f'Welcome email sent successfully to {request.data.get("first_name")}')
            except Exception as e:
                logger.error(f'Welcome email failed: {e}')
                # print(f'Failed to send welcome email: {e}')
            return Response({"message": "Registered Successfully"},
                            status=status.HTTP_201_CREATED)
        logger.warning(f'Registration failed: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout view."""

    def post(self, request):
        """Send token."""
        token = RefreshToken(request.data['refresh'])
        token.blacklist()
        return Response({"message": "Logged Out Successful"},
                        status=status.HTTP_200_OK)


class CustomTokenView(TokenObtainPairView):
    """Customizing Token View."""

    serializer_class = CustomTokenSerializer
