from ..serializers.refreshserializer import RefreshSerializer
from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.response import Response

class RefreshView(GenericAPIView):
    serializer_class = RefreshSerializer
    
    def post(self, req, *args, **kwargs):
        data = req.data
        serializer :RefreshSerializer= self.get_serializer_class(data=data)
        serializer.is_valid(raise_exception=1)
        data = serializer.create(serializer.validated_data)
        return Response(data , status=status.HTTP_200_OK)