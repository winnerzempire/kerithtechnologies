from django.contrib import admin
from .models import Category, Brand, Product, ProductImage, ProductAttribute, ProductReview, Cart, CartItem, Order, OrderItem, Wishlist, ShippingAddress

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1

class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'featured', 'active', 'order']
    list_filter = ['featured', 'active', 'parent']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['featured', 'active', 'order']

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'active']
    list_filter = ['active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'category', 'brand', 'price', 
        'compare_price', 'stock', 'featured', 'best_seller', 
        'new_arrival', 'active'
    ]
    list_filter = [
        'category', 'brand', 'featured', 'best_seller', 
        'new_arrival', 'active', 'created_at'
    ]
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = [
        'price', 'compare_price', 'stock', 'featured', 
        'best_seller', 'new_arrival', 'active'
    ]
    inlines = [ProductImageInline, ProductAttributeInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'description', 'short_description')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price', 'cost_price')
        }),
        ('Relationships', {
            'fields': ('category', 'brand')
        }),
        ('Inventory', {
            'fields': ('stock', 'low_stock_threshold')
        }),
        ('Flags', {
            'fields': ('featured', 'best_seller', 'new_arrival', 'active')
        }),
        ('Physical Attributes', {
            'fields': ('weight', 'dimensions')
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description')
        }),
        ('Images', {
            'fields': ('main_image',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'verified_purchase', 'created_at']
    list_filter = ['rating', 'verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__username', 'title']
    readonly_fields = ['created_at', 'updated_at']



# ... (keep existing admin classes) ...

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'total_quantity', 'total_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'session_key']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]
    
    def total_quantity(self, obj):
        return obj.total_quantity
    total_quantity.short_description = 'Items'
    
    def total_price(self, obj):
        return f"KSh {obj.total_price}"
    total_price.short_description = 'Total'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'payment_status', 
        'total_amount', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__username', 'customer_email']
    readonly_fields = [
        'order_number', 'created_at', 'updated_at', 
        'paid_at', 'delivered_at', 'cancelled_at'
    ]
    inlines = [OrderItemInline]
    list_editable = ['status', 'payment_status']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'payment_method')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total_amount')
        }),
        ('Customer Information', {
            'fields': ('customer_email', 'customer_phone')
        }),
        ('Addresses', {
            'fields': ('shipping_address', 'billing_address')
        }),
        ('Payment', {
            'fields': ('transaction_id', 'payment_details')
        }),
        ('Notes', {
            'fields': ('customer_notes', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'delivered_at', 'cancelled_at')
        }),
    )

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['created_at']

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'last_name', 'city', 'is_default']
    list_filter = ['city', 'state', 'country', 'is_default']
    search_fields = ['user__username', 'first_name', 'last_name', 'city']
    list_editable = ['is_default']