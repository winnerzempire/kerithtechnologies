from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from .models import Category, Brand, Product, ProductReview, Cart, CartItem, Order, OrderItem, Wishlist, ShippingAddress
from .serializers import *
from django.utils import timezone

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = Category.objects.filter(active=True)
        parent = self.request.query_params.get('parent', None)
        if parent == 'null':
            queryset = queryset.filter(parent__isnull=True)
        return queryset
    
    @action(detail=False)
    def featured(self, request):
        featured_categories = self.queryset.filter(featured=True)
        serializer = self.get_serializer(featured_categories, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def main_categories(self, request):
        main_categories = self.queryset.filter(parent__isnull=True)
        serializer = self.get_serializer(main_categories, many=True)
        return Response(serializer.data)

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.filter(active=True)
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'



class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['brand', 'featured', 'best_seller', 'new_arrival']  # remove 'category'
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Product.objects.filter(active=True).select_related(
            'category', 'brand'
        ).prefetch_related(
            'additional_images', 'attributes', 'reviews'
        )

        # 🔍 Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search) |
                Q(short_description__icontains=search)
            )

        # 💰 Price filtering
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # 🏷️ Category filter via slug
        category_slug = self.request.query_params.get('category') or \
                        self.request.query_params.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # 🏢 Brand filter via slug
        brand_slug = self.request.query_params.get('brand_slug')
        if brand_slug:
            queryset = queryset.filter(brand__slug=brand_slug)

        # 🔄 Ordering
        ordering = self.request.query_params.get('ordering')
        if ordering:
            if ordering == 'price':
                queryset = queryset.order_by('price')
            elif ordering == '-price':
                queryset = queryset.order_by('-price')
            elif ordering == 'name':
                queryset = queryset.order_by('name')
            elif ordering == '-name':
                queryset = queryset.order_by('-name')
            elif ordering == '-created_at':
                queryset = queryset.order_by('-created_at')
            elif ordering == 'created_at':
                queryset = queryset.order_by('created_at')
            elif ordering == 'rating':
                queryset = queryset.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    # 🌟 Featured products
    @action(detail=False)
    def featured(self, request):
        featured_products = self.get_queryset().filter(featured=True)[:12]
        serializer = self.get_serializer(featured_products, many=True)
        return Response(serializer.data)

    # 🏆 Best sellers
    @action(detail=False)
    def best_sellers(self, request):
        best_sellers = self.get_queryset().filter(best_seller=True)[:12]
        serializer = self.get_serializer(best_sellers, many=True)
        return Response(serializer.data)

    # 🆕 New arrivals
    @action(detail=False)
    def new_arrivals(self, request):
        new_arrivals = self.get_queryset().filter(new_arrival=True)[:12]
        serializer = self.get_serializer(new_arrivals, many=True)
        return Response(serializer.data)

    # 💸 On sale
    @action(detail=False)
    def on_sale(self, request):
        on_sale_products = self.get_queryset().filter(on_sale=True)[:12]
        serializer = self.get_serializer(on_sale_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='slug/(?P<slug>[^/.]+)')
    def get_by_slug(self, request, slug=None):
        ...



class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ProductReview.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



# ... (keep existing views) ...

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.AllowAny]  # 👈 Allow guests too

    def get_cart(self, request):
        """Get or create cart for user or session"""
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()  # create session if it doesn’t exist
                session_key = request.session.session_key

            cart, created = Cart.objects.get_or_create(session_key=session_key, user=None)
        return cart

    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        cart = self.get_cart(request)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart = self.get_cart(request)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id, active=True)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        if product.stock < quantity:
            return Response({'error': f'Only {product.stock} items available'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def update_item(self, request):
        cart = self.get_cart(request)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        cart = self.get_cart(request)
        product_id = request.data.get('product_id')

        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        cart = self.get_cart(request)
        cart.items.all().delete()
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_status']
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')
    
    def perform_create(self, serializer):
        # Get user's cart
        try:
            cart = Cart.objects.get(user=self.request.user)
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Cart is empty")
        
        if cart.is_empty:
            raise serializers.ValidationError("Cart is empty")
        
        # Validate stock and calculate totals
        subtotal = 0
        order_items = []
        
        for cart_item in cart.items.all():
            product = cart_item.product
            
            # Check stock
            if product.stock < cart_item.quantity:
                raise serializers.ValidationError(
                    f"Not enough stock for {product.name}. Only {product.stock} available."
                )
            
            # Calculate item total
            item_total = product.price * cart_item.quantity
            subtotal += item_total
            
            # Prepare order item data
            order_items.append({
                'product': product,
                'quantity': cart_item.quantity,
                'price': product.price,
                'product_name': product.name,
                'product_sku': product.sku
            })
        
        # Calculate other amounts (simplified for now)
        shipping_cost = 200  # Fixed shipping cost for Kenya
        tax_amount = subtotal * 0.16  # 16% VAT in Kenya
        total_amount = subtotal + shipping_cost + tax_amount
        
        # Create order
        order = serializer.save(
            user=self.request.user,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            total_amount=total_amount,
            customer_email=self.request.user.email,
            customer_phone=self.request.user.phone or '',
        )
        
        # Create order items and update product stock
        for item_data in order_items:
            OrderItem.objects.create(order=order, **item_data)
            # Update product stock
            item_data['product'].stock -= item_data['quantity']
            item_data['product'].save()
        
        # Clear cart
        cart.items.all().delete()
        
        return order
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        if not order.can_be_cancelled:
            return Response(
                {'error': 'Order cannot be cancelled at this stage'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'cancelled'
        order.cancelled_at = timezone.now()
        order.save()
        
        # Restore product stock
        for order_item in order.items.all():
            product = order_item.product
            product.stock += order_item.quantity
            product.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)

class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')
    
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        product_id = request.data.get('product_id')
        
        try:
            product = Product.objects.get(id=product_id, active=True)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user, 
            product=product
        )
        
        if not created:
            wishlist_item.delete()
            return Response({'added': False})
        
        return Response({'added': True})
    
    @action(detail=False, methods=['get'])
    def my_wishlist(self, request):
        wishlist_items = self.get_queryset()
        serializer = self.get_serializer(wishlist_items, many=True)
        return Response(serializer.data)

class ShippingAddressViewSet(viewsets.ModelViewSet):
    serializer_class = ShippingAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        try:
            default_address = ShippingAddress.objects.get(
                user=request.user, 
                is_default=True
            )
            serializer = self.get_serializer(default_address)
            return Response(serializer.data)
        except ShippingAddress.DoesNotExist:
            return Response(
                {'error': 'No default address found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
# class ProductViewSet(viewsets.ModelViewSet):
#     queryset = Product.objects.all()
#     serializer_class = ProductListSerializer

#     def get_serializer_class(self):
#         if self.action in ['retrieve', 'get_by_slug']:
#             return ProductDetailSerializer
#         return ProductListSerializer

#     @action(detail=False, methods=['get'], url_path='slug/(?P<slug>[^/.]+)')
#     def get_by_slug(self, request, slug=None):
#         try:
#             product = Product.objects.get(slug=slug)
#             serializer = ProductDetailSerializer(product, context={'request': request})
#             return Response(serializer.data)
#         except Product.DoesNotExist:
#             return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)