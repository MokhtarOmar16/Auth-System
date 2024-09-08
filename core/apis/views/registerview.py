from rest_framework.generics import CreateAPIView
from ..serializers.userserializer import UserSerializer

class RegisterView(CreateAPIView):
    serializer_class = UserSerializer