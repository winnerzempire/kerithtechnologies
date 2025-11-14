from rest_framework import serializers
from .models import Category, Brand, Product, ProductImage, ProductAttribute, ProductReview, Cart, CartItem, Order, OrderItem, Wishlist, ShippingAddress

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = '__all__'
    
    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.all(), many=True).data
        return []
    
    def get_product_count(self, obj):
        return obj.products.filter(active=True).count()

class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = '__all__'
    
    def get_product_count(self, obj):
        return obj.products.filter(active=True).count()

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'order')

class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ('name', 'value')

class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    
    class Meta:
        model = ProductReview
        fields = '__all__'
        read_only_fields = ('user', 'verified_purchase', 'helpful', 'not_helpful')

class ProductListSerializer(serializers.ModelSerializer):
    main_image = serializers.ImageField(read_only=True)
    discount_percentage = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'sku', 'main_image', 'price', 
            'compare_price', 'discount_percentage', 'in_stock',
            'featured', 'best_seller', 'new_arrival', 'on_sale',
            'average_rating', 'review_count', 'short_description'
        )
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0
    
    def get_review_count(self, obj):
        return obj.reviews.count()

class ProductDetailSerializer(ProductListSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    additional_images = ProductImageSerializer(many=True, read_only=True)
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    
    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + (
            'description', 'category', 'brand', 'additional_images', 
            'attributes', 'reviews', 'stock', 'weight', 'dimensions',
            'created_at', 'updated_at'
        )

# ... (add after existing serializers) ...

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    total_price = serializers.ReadOnlyField()
    unit_price = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    total_quantity = serializers.ReadOnlyField()
    is_empty = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()
    items_count = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('order_number', 'created_at', 'updated_at')

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = Wishlist
        fields = '__all__'
        read_only_fields = ('user',)

class ShippingAddressSerializer(serializers.ModelSerializer):
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = ShippingAddress
        fields = '__all__'
        read_only_fields = ('user',)