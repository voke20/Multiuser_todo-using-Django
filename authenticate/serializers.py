from rest_framework import serializers
from authenticate.models import CustomerModel
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:

        model = CustomerModel
        fields = [
            'email',
            'password',
            'phone_number',
            'first_name',
            'last_name'
            ]

    def create(self, validated_data):
        """Create Register Serializer."""
        email = validated_data["email"]
        password = validated_data["password"]
        first_name = validated_data["first_name"]
        last_name = validated_data["last_name"]

        user = CustomerModel.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        return user

class CustomTokenSerializer(TokenObtainPairSerializer):
    """Customize token response."""

    def validate(self, attrs):
        """Validate token response."""
        data = super().validate(attrs)
        data['first_name'] = self.user.first_name
        data['last_name'] = self.user.last_name
        data['email'] = self.user.email
        return data


class UserSerializer(serializers.ModelSerializer):
    """User Serializer."""

    class Meta:
        model = CustomerModel
        fields = ['id', 'email']
