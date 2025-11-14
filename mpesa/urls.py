from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'mpesa'

router = DefaultRouter()
router.register(r'transactions', views.MpesaTransactionViewSet, basename='mpesa-transaction')
router.register(r'configurations', views.MpesaConfigurationViewSet, basename='mpesa-configuration')

urlpatterns = [
    path('', include(router.urls)),
    path('stk-callback/', views.stk_callback, name='stk_callback'),
]