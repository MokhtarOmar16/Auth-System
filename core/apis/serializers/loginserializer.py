from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    

    def validate(self, attrs:dict):
        user = authenticate(username=attrs.get("username_or_email"), password=attrs.get("password"))
        if user is None:
            raise serializers.ValidationError("Invalid username or password")
        attrs['user'] = user
        return attrs
    
    def create(self, validated_data):
        user = validated_data['user']        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        return {
            'refresh': refresh_token,
            'access': access_token
        }
