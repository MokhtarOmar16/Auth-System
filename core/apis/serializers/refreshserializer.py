from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    def validate(self, attrs):
        refresh_token = attrs.get('refresh')
        try:
            # Validate the provided refresh token
            token = RefreshToken(refresh_token)
            # Ensure the token is not blacklisted
            if token.blacklisted:
                raise serializers.ValidationError("The refresh token is blacklisted.")
        except :
            raise serializers.ValidationError("Invalid refresh token.")

        return attrs
    
    def create(self, validated_data):
        token = validated_data['refresh']
        token = RefreshToken(token)
        return {"access": str(token.access_token) }