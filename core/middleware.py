import uuid
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .models import AnonymousUser


class AnonymousUserMiddleware(MiddlewareMixin):
    """
    Middleware that creates and manages anonymous user sessions for users without JWT tokens.
    Useful for e-commerce quick ordering without requiring authentication.
    """
    
    COOKIE_NAME = getattr(settings, 'ANONYMOUS_USER_COOKIE_NAME', 'anonymous_session_id')
    COOKIE_MAX_AGE = getattr(settings, 'ANONYMOUS_USER_COOKIE_MAX_AGE', 60 * 60 * 24 * 365)  # 1 year
    COOKIE_HTTPONLY = getattr(settings, 'ANONYMOUS_USER_COOKIE_HTTPONLY', True)
    COOKIE_SECURE = getattr(settings, 'ANONYMOUS_USER_COOKIE_SECURE', False)  # Set to True in production with HTTPS
    COOKIE_SAMESITE = getattr(settings, 'ANONYMOUS_USER_COOKIE_SAMESITE', 'Lax')
    
    def process_request(self, request):
        """
        Process incoming request to check for JWT token or anonymous session.
        """
        request.anonymous_user = None
        
        # Check if user is authenticated via JWT token
        if self._has_jwt_token(request):
            return None
        
        # Check for existing anonymous session cookie
        session_id = request.COOKIES.get(self.COOKIE_NAME)
        
        if session_id:
            try:
                # Try to retrieve existing anonymous user
                anonymous_user = AnonymousUser.objects.get(session_id=session_id)
                # Update last_active timestamp
                anonymous_user.save(update_fields=['last_active'])
                request.anonymous_user = anonymous_user
            except (AnonymousUser.DoesNotExist, ValueError):
                # Invalid or expired session, create new one
                request.anonymous_user = self._create_anonymous_user()
        else:
            # No session cookie, create new anonymous user
            request.anonymous_user = self._create_anonymous_user()
        
        return None
    
    def process_response(self, request, response):
        """
        Set anonymous session cookie in response if anonymous user was created/used.
        """
        # Only set cookie if there's an anonymous user and no JWT token
        if hasattr(request, 'anonymous_user') and request.anonymous_user and not self._has_jwt_token(request):
            response.set_cookie(
                key=self.COOKIE_NAME,
                value=str(request.anonymous_user.session_id),
                max_age=self.COOKIE_MAX_AGE,
                httponly=self.COOKIE_HTTPONLY,
                secure=self.COOKIE_SECURE,
                samesite=self.COOKIE_SAMESITE,
            )
        
        return response
    
    def _has_jwt_token(self, request):
        """
        Check if request has a valid JWT token in Authorization header or cookies.
        """
        # Check Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('JWT ') or auth_header.startswith('Bearer '):
            return True
        
        # Check for JWT token in cookies (if your app stores it there)
        jwt_cookie = request.COOKIES.get('jwt_token') or request.COOKIES.get('access_token')
        if jwt_cookie:
            return True
        
        return False
    
    def _create_anonymous_user(self):
        """
        Create a new anonymous user session.
        """
        return AnonymousUser.objects.create()
