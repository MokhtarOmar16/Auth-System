from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([AllowAny])
def test_anonymous_middleware(request):
    """
    Test endpoint to verify anonymous user middleware functionality.
    Returns information about the current session.
    """
    response_data = {
        'authenticated': request.user.is_authenticated,
        'user': None,
        'anonymous_user': None,
    }
    
    if request.user.is_authenticated:
        response_data['user'] = {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
        }
    
    if hasattr(request, 'anonymous_user') and request.anonymous_user:
        response_data['anonymous_user'] = {
            'session_id': str(request.anonymous_user.session_id),
            'created_at': request.anonymous_user.created_at.isoformat(),
            'last_active': request.anonymous_user.last_active.isoformat(),
        }
    
    return Response(response_data, status=status.HTTP_200_OK)
