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
from django.shortcuts import get_object_or_404
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from rest_framework.permissions import AllowAny
from django.shortcuts import redirect
import io
import json
import logging
import base64
# from django.apps import apps

from note.models import Note

logger = logging.getLogger('authenticate')
User = get_user_model()

SCOPES = ['https://www.googleapis.com/auth/drive.file']

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


def build_google_auth_url(request):
    """Create a Google OAuth authorization URL and persist the state."""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    logger.info(f'redirect_url: {flow.redirect_uri}')

    auth_url = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
    )
    code_verifier = flow.code_verifier
    logger.info(f'code_verifier after auth_url: {code_verifier}')
    state_data = json.dumps({
        'user_id': request.user.id,
        'code_verifier': code_verifier,
        })
    state = base64.urlsafe_b64encode(
        state_data.encode()
        ).decode()
    logger.info(f'auth_state: {state}')
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=state,
    )

    logger.info(f'Final state: {state_data}')
    # Persist the PKCE code_verifier so it can be used in the callback
    # try:
    #     request.session['google_code_verifier'] = flow.code_verifier
    #     logger.info(f'code-verifier: {flow.code_verifier}')
    #     logger.info(f"Session key: {request.session.session_key}")
    #     logger.info(f"Session data: {dict(request.session)}")
    # except Exception:
    #     # If sessions are not available for some reason, continue without crash
    #     logger.warning('Unable to save google_code_verifier to session')
    return auth_url


class GoogleAuthView(APIView):
    """Initiate Google OAuth flow."""
    permission_classes = [IsAuthenticated]

    def options(self, request):
        """Handle CORS preflight requests."""
        return Response(status=status.HTTP_200_OK)

    def get(self, request):
        request.session['google_user_id'] = request.user.id
        auth_url = build_google_auth_url(request)
        logger.info(
            f"AUTH - Session Key: {request.session.session_key}"
        )
        logger.info(
            f"AUTH - Session Data: {dict(request.session)}"
        )
        return Response({"auth_url": auth_url})
    


class GoogleCallbackView(APIView):
    """Handle Google OAuth callback."""
    permission_classes = [AllowAny]

    def get(self, request):
        # logger.info(
        #     f"CALLBACK - Session Key: {request.session.session_key}"
        # )
        # logger.info(
        #     f"CALLBACK - Session Data: {dict(request.session)}"
        # )
        state = request.GET.get('state', '')
        # logger.info(f'callback state: {state}')
        # # Try to retrieve the PKCE code_verifier from the session first,
        # # fall back to GET parameter if provided.
        # code_verifier = request.session.pop('google_code_verifier', None) or request.GET.get("code_verifier", "")
        # logger.info(f'callback code_verifier: {code_verifier}')
        try:
            state_data = json.loads(base64.urlsafe_b64decode(state).decode())
            user_id = state_data['user_id']
            code_verifier = state_data.get('code_verifier', '')
            logger.info(f"Decoded state: {state_data}")
            logger.info(f'user_id: {user_id}')
            logger.info(f'callback verifier: {code_verifier}')

        except Exception as e:
            logger.error(f'State decode error {e}')
            return Response(
                {'error': 'Invalid state parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User Not Found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            state=state
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        logger.info(f'callback flow.redirect_uri: {flow.redirect_uri}')
        if not code_verifier:
            return Response({'error': 'Missing code_verifier'}, status=status.HTTP_400_BAD_REQUEST)
        flow.code_verifier = code_verifier
        logger.info(f'callback flow.code_verifier: {flow.code_verifier}')
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials
        user.google_credentials = json.dumps({
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
        })
        user.save()
        return Response({'message': 'Google Drive connected!'}, status=status.HTTP_200_OK)


class GoogleDriveUploadView(APIView):
    """Upload note to Google Drive."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {},
            }
        },
        responses={200: {"description": "Note uploaded to Google Drive"}},
    )
    def post(self, request, id):
        note = get_object_or_404(Note, id=id, owner=request.user)

        if not request.user.google_credentials:
            return Response(
                {
                    "error": "Please connect Google Drive first",
                    "auth_url": build_google_auth_url(request),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            creds_data = json.loads(request.user.google_credentials)
            credentials = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data['refresh_token'],
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
            )
        except (TypeError, ValueError, KeyError):
            return Response(
                {
                    "error": "Please connect Google Drive first",
                    "auth_url": build_google_auth_url(request),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        service = build('drive', 'v3', credentials=credentials)

        # Create note content
        import re
        clean_content = re.sub(r'<[^>]+>', '', note.content)
        note_content = f"Title: {note.title}\n\nContent:\n{clean_content}"

        file_metadata = {'name': f'{note.title}.txt'}
        media = MediaIoBaseUpload(
            io.BytesIO(note_content.encode()),
            mimetype='text/plain'
        )

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        return Response({
            'message': 'Note uploaded to Google Drive!',
            'drive_link': file.get('webViewLink'),
        }, status=status.HTTP_200_OK)
    