from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'brands', views.BrandViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'reviews', views.ProductReviewViewSet)
router.register(r'cart', views.CartViewSet, basename='cart')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'wishlist', views.WishlistViewSet, basename='wishlist')
router.register(r'shipping-addresses', views.ShippingAddressViewSet, basename='shippingaddress')

urlpatterns = [
    path('', include(router.urls)),
]