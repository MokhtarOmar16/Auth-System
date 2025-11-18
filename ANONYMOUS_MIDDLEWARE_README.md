# Anonymous User Middleware for Django E-commerce

## Overview
This middleware automatically creates and manages anonymous user sessions for visitors without JWT authentication tokens. This is perfect for e-commerce applications that need to support quick ordering without requiring user registration.

## Features
- ✅ Automatic anonymous session creation for unauthenticated users
- ✅ UUID-based session tracking
- ✅ Secure cookie management (HttpOnly, SameSite)
- ✅ Automatic session persistence and updates
- ✅ No interference with JWT authenticated users
- ✅ Easy access to anonymous user data in views via `request.anonymous_user`

## Installation

### 1. Model
The `AnonymousUser` model has been added to `core/models.py`:
```python
class AnonymousUser(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
```

### 2. Middleware
The middleware is located at `core/middleware.py` and has been registered in `settings.py`.

### 3. Settings Configuration
The following settings have been added to `auth/settings.py`:
```python
ANONYMOUS_USER_COOKIE_NAME = 'anonymous_session_id'
ANONYMOUS_USER_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year
ANONYMOUS_USER_COOKIE_HTTPONLY = True
ANONYMOUS_USER_COOKIE_SECURE = False  # Set to True in production with HTTPS
ANONYMOUS_USER_COOKIE_SAMESITE = 'Lax'
```

## How It Works

1. **Request Processing:**
   - Middleware checks if the request has a JWT token (Authorization header or cookie)
   - If JWT token exists → No anonymous session is created
   - If no JWT token → Checks for existing anonymous session cookie
   - If no cookie exists → Creates new `AnonymousUser` and sets cookie

2. **Response Processing:**
   - Sets the anonymous session cookie in the response
   - Cookie is only set for non-authenticated users

3. **Session Persistence:**
   - Each request with an anonymous cookie updates the `last_active` timestamp
   - Sessions persist for 1 year by default (configurable)

## Usage in Views

### Accessing Anonymous User Data
```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([AllowAny])
def quick_order(request):
    # Check if user is authenticated
    if request.user.is_authenticated:
        user_id = request.user.id
        # Process order for authenticated user
    elif hasattr(request, 'anonymous_user') and request.anonymous_user:
        # Process order for anonymous user
        anonymous_session_id = request.anonymous_user.session_id
        # Link order to anonymous session
    
    return Response({'status': 'success'})
```

### Example: Cart Management
```python
from core.models import AnonymousUser
from django.db import models

class Cart(models.Model):
    user = models.ForeignKey('core.User', null=True, blank=True, on_delete=models.CASCADE)
    anonymous_user = models.ForeignKey(AnonymousUser, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @classmethod
    def get_or_create_cart(cls, request):
        if request.user.is_authenticated:
            cart, created = cls.objects.get_or_create(user=request.user)
        elif hasattr(request, 'anonymous_user') and request.anonymous_user:
            cart, created = cls.objects.get_or_create(anonymous_user=request.anonymous_user)
        else:
            return None
        return cart
```

### Example: Order Creation
```python
class Order(models.Model):
    user = models.ForeignKey('core.User', null=True, blank=True, on_delete=models.SET_NULL)
    anonymous_user = models.ForeignKey(AnonymousUser, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField()  # For anonymous orders
    # ... other fields

@api_view(['POST'])
@permission_classes([AllowAny])
def create_order(request):
    order_data = request.data
    
    if request.user.is_authenticated:
        order = Order.objects.create(
            user=request.user,
            email=request.user.email,
            **order_data
        )
    elif hasattr(request, 'anonymous_user') and request.anonymous_user:
        order = Order.objects.create(
            anonymous_user=request.anonymous_user,
            email=order_data.get('email'),
            **order_data
        )
    
    return Response({'order_id': order.id})
```

## Testing

### Test Endpoint
A test endpoint has been created at `/jwt/test-anonymous/` to verify middleware functionality.

### Test Anonymous User Creation
```bash
curl http://localhost:8000/jwt/test-anonymous/
```

Response:
```json
{
  "authenticated": false,
  "user": null,
  "anonymous_user": {
    "session_id": "399791cb-6f47-4bac-900b-6454a0408f9a",
    "created_at": "2025-11-18T06:01:43.682109+00:00",
    "last_active": "2025-11-18T06:01:43.682150+00:00"
  }
}
```

### Test Session Persistence
```bash
curl http://localhost:8000/jwt/test-anonymous/ \
  -H "Cookie: anonymous_session_id=399791cb-6f47-4bac-900b-6454a0408f9a"
```

The `last_active` timestamp will be updated.

### Test with JWT Token
```bash
curl http://localhost:8000/jwt/test-anonymous/ \
  -H "Authorization: JWT your-token-here"
```

No anonymous cookie will be set when JWT token is present.

## Production Considerations

### Security Settings
For production deployment with HTTPS, update `settings.py`:
```python
ANONYMOUS_USER_COOKIE_SECURE = True  # Requires HTTPS
ANONYMOUS_USER_COOKIE_SAMESITE = 'Strict'  # More restrictive
```

### Session Cleanup
Consider adding a periodic task to clean up old anonymous sessions:
```python
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import AnonymousUser

class Command(BaseCommand):
    help = 'Clean up old anonymous user sessions'
    
    def handle(self, *args, **options):
        # Delete sessions older than 1 year
        cutoff_date = timezone.now() - timedelta(days=365)
        deleted_count = AnonymousUser.objects.filter(
            last_active__lt=cutoff_date
        ).delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(f'Deleted {deleted_count} old anonymous sessions')
        )
```

### Migrating Anonymous to Authenticated
When an anonymous user registers or logs in, you can migrate their data:
```python
def migrate_anonymous_to_user(anonymous_user, user):
    """Migrate anonymous user data to authenticated user"""
    # Migrate cart items
    Cart.objects.filter(anonymous_user=anonymous_user).update(
        user=user,
        anonymous_user=None
    )
    
    # Migrate orders
    Order.objects.filter(anonymous_user=anonymous_user).update(
        user=user,
        anonymous_user=None
    )
    
    # Optionally delete the anonymous user record
    anonymous_user.delete()
```

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `ANONYMOUS_USER_COOKIE_NAME` | `'anonymous_session_id'` | Name of the cookie |
| `ANONYMOUS_USER_COOKIE_MAX_AGE` | `31536000` (1 year) | Cookie expiration in seconds |
| `ANONYMOUS_USER_COOKIE_HTTPONLY` | `True` | Prevents JavaScript access |
| `ANONYMOUS_USER_COOKIE_SECURE` | `False` | Requires HTTPS (set True in production) |
| `ANONYMOUS_USER_COOKIE_SAMESITE` | `'Lax'` | CSRF protection level |

## Database Schema

The `AnonymousUser` table structure:
```sql
CREATE TABLE core_anonymoususer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id UUID UNIQUE NOT NULL,
    created_at DATETIME NOT NULL,
    last_active DATETIME NOT NULL
);

CREATE INDEX idx_session_id ON core_anonymoususer(session_id);
```

## Troubleshooting

### Cookie Not Being Set
- Check that the middleware is registered in `MIDDLEWARE` setting
- Verify the response is not a redirect
- Check browser console for cookie errors

### Session Not Persisting
- Verify the cookie is being sent in subsequent requests
- Check cookie expiration settings
- Ensure the session_id in the cookie matches a database record

### Conflicts with Authentication
- The middleware automatically skips authenticated users
- JWT tokens take precedence over anonymous sessions
- No anonymous cookie is set when JWT token is present

## License
This implementation is part of your Django e-commerce project.
