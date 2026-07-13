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
import io
import json
import logging
import base64
import re
import secrets
import urllib.parse
import msal
import requests

from note.models import Note

logger = logging.getLogger('authenticate')
User = get_user_model()

SCOPES = ['https://www.googleapis.com/auth/drive.file']
# MSAL adds 'offline_access', 'openid', and 'profile' automatically for a
# confidential client app - listing them here makes MSAL raise a ValueError.
ONEDRIVE_SCOPES = ['Files.ReadWrite']
ONEDRIVE_FOLDER = 'EmmaNotes'
GRAPH_UPLOAD_URL = (
    'https://graph.microsoft.com/v1.0/me/drive/root:/'
    '{folder}/{filename}:/content'
)

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
    state_data = json.dumps({
        'user_id': request.user.id,
        })
    state = base64.urlsafe_b64encode(state_data.encode()).decode()
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=state,
    )
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
        return Response({"auth_url:", auth_url})


class GoogleCallbackView(APIView):
    """Handle Google OAuth callback."""
    permission_classes = [AllowAny]

    def get(self, request):
        state = request.GET.get('state', '')
        code_verifier = request.GET.get("code_verifier", "")
        try:
            state_data = json.loads(base64.urlsafe_b64decode(state).decode())
            user_id = state_data['user_id']

        except Exception:
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
        flow.code_verifier = code_verifier
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


def get_msal_app():
    """Build MSAL confidential client for OneDrive OAuth."""
    return msal.ConfidentialClientApplication(
        settings.MICROSOFT_CLIENT_ID,
        authority=(
            f"https://login.microsoftonline.com/"
            f"{settings.MICROSOFT_TENANT_ID}"
        ),
        client_credential=settings.MICROSOFT_CLIENT_SECRET,
    )


def build_onedrive_auth_url(request):
    """Create a Microsoft OAuth authorization URL for the current user.

    We generate a random `state` value and remember it (and who is logging
    in) in the user's Django session. When Microsoft redirects the browser
    back to our callback, we check the state it sends matches what we saved.
    This proves the callback belongs to the same browser that started the
    flow, so a stranger can't link their own Microsoft account to someone
    else's notes by guessing a user id.
    """
    state = secrets.token_urlsafe(16)
    request.session['onedrive_state'] = state
    request.session['onedrive_user_id'] = request.user.id
    return get_msal_app().get_authorization_request_url(
        scopes=ONEDRIVE_SCOPES,
        state=state,
        redirect_uri=settings.MICROSOFT_REDIRECT_URI,
    )


def sanitize_onedrive_filename(title, note_id):
    """Turn a note title into a safe OneDrive filename.

    The note id is appended so two notes with the same title don't
    overwrite each other in OneDrive.
    """
    cleaned = re.sub(r'[\\/:*?"<>|]', '_', title).strip() or 'note'
    return f"{cleaned}-{note_id}.txt"


def save_onedrive_credentials(user, token_result):
    """Persist Graph tokens on the user (no client_secret stored)."""
    user.onedrive_credentials = json.dumps({
        'access_token': token_result.get('access_token'),
        'refresh_token': token_result.get('refresh_token'),
    })
    user.save(update_fields=['onedrive_credentials'])


def refresh_onedrive_access_token(user, refresh_token):
    """Use the refresh token to get a new access token and save it.

    Returns the new access token, or None if the refresh token itself is no
    longer valid (the user will need to reconnect OneDrive).
    """
    result = get_msal_app().acquire_token_by_refresh_token(
        refresh_token,
        scopes=ONEDRIVE_SCOPES,
    )
    if 'access_token' not in result:
        logger.error('OneDrive token refresh failed: %s', result.get('error'))
        user.onedrive_credentials = None
        user.save(update_fields=['onedrive_credentials'])
        return None

    # MSAL doesn't always return a new refresh token; keep the old one.
    result.setdefault('refresh_token', refresh_token)
    save_onedrive_credentials(user, result)
    return result['access_token']


class OneDriveAuthView(APIView):
    """Initiate Microsoft OneDrive OAuth flow."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"auth_url": build_onedrive_auth_url(request)})


class OneDriveCallbackView(APIView):
    """Handle Microsoft OAuth callback and store tokens."""

    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get('code', '')
        if not code:
            return Response(
                {'error': 'Authorization code is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # The state and user id were stashed in the session when the flow
        # started. If they're missing or don't match, this callback wasn't
        # triggered by a flow we started for this browser - reject it.
        # We only read (not clear) the session here: an unrelated or wrong
        # request must never wipe out someone else's in-progress login.
        state = request.GET.get('state', '')
        expected_state = request.session.get('onedrive_state')
        user_id = request.session.get('onedrive_user_id')
        if not expected_state or state != expected_state or not user_id:
            return Response(
                {'error': 'Invalid or expired state parameter'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Valid - clear it now so this exact callback can't be replayed.
        del request.session['onedrive_state']
        del request.session['onedrive_user_id']

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User Not Found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = get_msal_app().acquire_token_by_authorization_code(
            code,
            scopes=ONEDRIVE_SCOPES,
            redirect_uri=settings.MICROSOFT_REDIRECT_URI,
        )
        if 'access_token' not in result:
            logger.error(
                'OneDrive token exchange failed: %s',
                result.get('error_description') or result.get('error'),
            )
            return Response(
                {'error': 'Failed to connect OneDrive'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        save_onedrive_credentials(user, result)
        return Response(
            {'message': 'OneDrive connected!'},
            status=status.HTTP_200_OK,
        )


def put_note_on_onedrive(access_token, filename, note_content):
    """Upload note text to OneDrive via the Microsoft Graph API."""
    upload_url = GRAPH_UPLOAD_URL.format(
        folder=ONEDRIVE_FOLDER,
        filename=urllib.parse.quote(filename),
    )
    return requests.put(
        upload_url,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'text/plain',
        },
        data=note_content.encode('utf-8'),
        timeout=30,
    )


class OneDriveUploadView(APIView):
    """Upload note to OneDrive via Microsoft Graph."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {},
            }
        },
        responses={200: {"description": "Note uploaded to OneDrive"}},
    )
    def post(self, request, id):
        note = get_object_or_404(Note, id=id, owner=request.user)

        if not request.user.onedrive_credentials:
            return Response(
                {
                    "error": "Please connect OneDrive first",
                    "auth_url": build_onedrive_auth_url(request),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        creds = json.loads(request.user.onedrive_credentials)
        clean_content = re.sub(r'<[^>]+>', '', note.content)
        note_content = f"Title: {note.title}\n\nContent:\n{clean_content}"
        filename = sanitize_onedrive_filename(note.title, note.id)

        response = put_note_on_onedrive(
            creds['access_token'], filename, note_content
        )

        # Access tokens expire after about an hour. If Graph rejects it,
        # use the refresh token to get a new one and try once more.
        if response.status_code in (401, 403):
            new_access_token = refresh_onedrive_access_token(
                request.user, creds.get('refresh_token')
            )
            if not new_access_token:
                return Response(
                    {
                        "error": "Please connect OneDrive first",
                        "auth_url": build_onedrive_auth_url(request),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            response = put_note_on_onedrive(
                new_access_token, filename, note_content
            )

        if response.status_code not in (200, 201):
            logger.error(
                'OneDrive upload failed: %s %s',
                response.status_code,
                response.text[:500],
            )
            return Response(
                {'error': 'Failed to upload note to OneDrive'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        file_data = response.json()
        return Response(
            {
                'message': 'Note uploaded to OneDrive!',
                'onedrive_link': file_data.get('webUrl'),
            },
            status=status.HTTP_200_OK,
        )
