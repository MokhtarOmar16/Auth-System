"""
Example usage of Anonymous User Middleware in Django E-commerce views
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from core.models import AnonymousUser


# Example 1: Cart Model with Anonymous User Support
class Cart(models.Model):
    user = models.ForeignKey('core.User', null=True, blank=True, on_delete=models.CASCADE)
    anonymous_user = models.ForeignKey(AnonymousUser, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carts'
    
    @classmethod
    def get_or_create_cart(cls, request):
        """Get or create cart for authenticated or anonymous user"""
        if request.user.is_authenticated:
            cart, created = cls.objects.get_or_create(user=request.user)
        elif hasattr(request, 'anonymous_user') and request.anonymous_user:
            cart, created = cls.objects.get_or_create(anonymous_user=request.anonymous_user)
        else:
            return None
        return cart


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_id = models.IntegerField()
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'cart_items'


# Example 2: Add to Cart View
@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_cart(request):
    """
    Add item to cart for both authenticated and anonymous users
    """
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity', 1)
    price = request.data.get('price')
    
    if not all([product_id, price]):
        return Response(
            {'error': 'product_id and price are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create cart
    cart = Cart.get_or_create_cart(request)
    
    if not cart:
        return Response(
            {'error': 'Unable to create cart'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Add or update cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product_id=product_id,
        defaults={'quantity': quantity, 'price': price}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    return Response({
        'message': 'Item added to cart',
        'cart_id': cart.id,
        'item_id': cart_item.id,
        'quantity': cart_item.quantity
    }, status=status.HTTP_201_CREATED)


# Example 3: View Cart
@api_view(['GET'])
@permission_classes([AllowAny])
def view_cart(request):
    """
    View cart contents for authenticated or anonymous user
    """
    cart = Cart.get_or_create_cart(request)
    
    if not cart:
        return Response({'items': [], 'total': 0})
    
    items = CartItem.objects.filter(cart=cart).values(
        'id', 'product_id', 'quantity', 'price'
    )
    
    total = sum(item['quantity'] * float(item['price']) for item in items)
    
    return Response({
        'cart_id': cart.id,
        'items': list(items),
        'total': total,
        'is_anonymous': not request.user.is_authenticated
    })


# Example 4: Order Model with Anonymous User Support
class Order(models.Model):
    user = models.ForeignKey('core.User', null=True, blank=True, on_delete=models.SET_NULL)
    anonymous_user = models.ForeignKey(AnonymousUser, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'orders'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.IntegerField()
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'order_items'


# Example 5: Quick Order (Checkout)
@api_view(['POST'])
@permission_classes([AllowAny])
def quick_order(request):
    """
    Create order for authenticated or anonymous user
    """
    email = request.data.get('email')
    phone = request.data.get('phone')
    address = request.data.get('address')
    
    # For authenticated users, use their email if not provided
    if request.user.is_authenticated and not email:
        email = request.user.email
    
    if not all([email, phone, address]):
        return Response(
            {'error': 'email, phone, and address are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get cart
    cart = Cart.get_or_create_cart(request)
    
    if not cart or not cart.items.exists():
        return Response(
            {'error': 'Cart is empty'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate total
    cart_items = cart.items.all()
    total_amount = sum(item.quantity * item.price for item in cart_items)
    
    # Create order
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        anonymous_user=request.anonymous_user if hasattr(request, 'anonymous_user') else None,
        email=email,
        phone=phone,
        address=address,
        total_amount=total_amount
    )
    
    # Create order items
    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price=cart_item.price
        )
    
    # Clear cart
    cart.items.all().delete()
    
    return Response({
        'message': 'Order created successfully',
        'order_id': order.id,
        'total_amount': str(total_amount),
        'status': order.status
    }, status=status.HTTP_201_CREATED)


# Example 6: Migrate Anonymous User Data After Registration/Login
def migrate_anonymous_to_authenticated(anonymous_user, authenticated_user):
    """
    Migrate anonymous user's cart and orders to authenticated user
    Call this function after user registers or logs in
    """
    # Migrate cart
    Cart.objects.filter(anonymous_user=anonymous_user).update(
        user=authenticated_user,
        anonymous_user=None
    )
    
    # Migrate orders
    Order.objects.filter(anonymous_user=anonymous_user).update(
        user=authenticated_user,
        anonymous_user=None
    )
    
    # Optionally delete the anonymous user record
    # anonymous_user.delete()
    
    return True


# Example 7: Login View with Migration
@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_migration(request):
    """
    Login view that migrates anonymous user data
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    from django.contrib.auth import authenticate
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if not user:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Migrate anonymous user data if exists
    if hasattr(request, 'anonymous_user') and request.anonymous_user:
        migrate_anonymous_to_authenticated(request.anonymous_user, user)
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    })


# Example 8: Check Session Status
@api_view(['GET'])
@permission_classes([AllowAny])
def session_status(request):
    """
    Get current session status (authenticated or anonymous)
    """
    if request.user.is_authenticated:
        return Response({
            'type': 'authenticated',
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email
            }
        })
    elif hasattr(request, 'anonymous_user') and request.anonymous_user:
        return Response({
            'type': 'anonymous',
            'session_id': str(request.anonymous_user.session_id),
            'created_at': request.anonymous_user.created_at.isoformat()
        })
    else:
        return Response({
            'type': 'none',
            'message': 'No session found'
        })
