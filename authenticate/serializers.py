from rest_framework import serializers
from . models import CustomerModel

class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only = True) # for password hashing
    class Meta:
        model = CustomerModel
        fields = ('email', 'password', 'phone_number')
    
    def create(self, validated_data):
        user = CustomerModel.objects.create_user(
            phone_number = validated_data.get('phone_number', ''),
            email = validated_data['email'],
            password = validated_data['password']
        )
        return user
        