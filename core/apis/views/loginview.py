from ..serializers.loginserializer import LoginSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status



class LoginView(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_data = serializer.create(serializer.validated_data)
        return Response(token_data, status=status.HTTP_200_OK)
