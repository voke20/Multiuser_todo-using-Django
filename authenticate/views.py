from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from . serializers import RegisterSerializer
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

User = get_user_model()
# Create your views here.

@extend_schema(
    parameters=[
        OpenApiParameter(name='email', type=str, location=OpenApiParameter.QUERY, required=True)
    ]
)
class SearchUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        email = request.query_params.get('email', '')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            return Response({
                "id": user.id,
                "email": user.email,
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

@extend_schema(request=RegisterSerializer)
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Registered Successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        token = RefreshToken(request.data['refresh'])
        token.blacklist()
        return Response({"message": "Logged Out Successful"}, status=status.HTTP_200_OK)