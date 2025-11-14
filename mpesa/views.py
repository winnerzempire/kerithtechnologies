from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json
import logging
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import MpesaTransaction, MpesaConfiguration, MpesaWebhookLog
from .serializers import (
    MpesaTransactionSerializer, 
    MpesaPaymentRequestSerializer,
    MpesaConfigurationSerializer
)
from .services import MpesaGateway, MpesaCallbackHandler
from store.models import Order

logger = logging.getLogger(__name__)


class MpesaTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = MpesaTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Allow unauthenticated access to payment initiation.
        Require authentication for everything else.
        """
        if self.action in ['initiate_payment']:
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        # Protect user transactions — only visible to authenticated users
        if self.request.user.is_authenticated:
            return MpesaTransaction.objects.filter(order__user=self.request.user)
        return MpesaTransaction.objects.none()

    @action(detail=False, methods=['post'])
    def initiate_payment(self, request):
        """Initiate M-Pesa STK push payment"""
        serializer = MpesaPaymentRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        order_id = serializer.validated_data['order_id']

        try:
            from store.models import Order
            order = Order.objects.get(id=order_id)

            # Validate order
            if order.payment_status != 'pending':
                return Response(
                    {'error': 'Order payment has already been processed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Initialize M-Pesa gateway
            mpesa_gateway = MpesaGateway()

            from django.urls import reverse
            callback_url = request.build_absolute_uri(reverse('mpesa:stk_callback'))

            # ✅ Add your till number here (or pull from settings)
            TILL_NUMBER = "4315570"

            # Initiate STK push
            result = mpesa_gateway.stk_push(
                phone_number=phone_number,
                amount=order.total_amount,
                account_reference=order.order_number,
                transaction_desc=f"Payment for order {order.order_number}",
                callback_url=callback_url,
                till_number=TILL_NUMBER,
            )

            if result['success']:
                MpesaTransaction.objects.create(
                    order=order,
                    phone_number=phone_number,
                    amount=order.total_amount,
                    merchant_request_id=result.get('merchant_request_id'),
                    checkout_request_id=result.get('checkout_request_id'),
                    init_request_data=result.get('raw_response'),
                    status='pending'
                )

                order.payment_method = 'mpesa'
                order.save()

                return Response({
                    'success': True,
                    'message': 'Payment request sent successfully',
                    'customer_message': result.get('customer_message')
                })

            return Response({
                'success': False,
                'error': result.get('error_message', 'Payment initiation failed')
            }, status=status.HTTP_400_BAD_REQUEST)

        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Payment initiation error: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MpesaConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = MpesaConfigurationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MpesaConfiguration.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            from rest_framework.permissions import IsAdminUser
            return [IsAdminUser()]
        return [IsAuthenticated()]

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def stk_callback(request):
    """
    Handle M-Pesa STK push callback
    """
    try:
        # Log the webhook
        webhook_log = MpesaWebhookLog.objects.create(
            payload=request.data,
            headers=dict(request.headers),
            ip_address=get_client_ip(request)
        )
        
        # Process the callback
        callback_handler = MpesaCallbackHandler()
        success = callback_handler.handle_stk_callback(request.data)
        
        # Update webhook log with response
        webhook_log.response_status = 200 if success else 400
        webhook_log.save()
        
        if success:
            return JsonResponse({
                "ResultCode": 0,
                "ResultDesc": "Success"
            })
        else:
            return JsonResponse({
                "ResultCode": 1,
                "ResultDesc": "Failed"
            }, status=400)
            
    except Exception as e:
        logger.error(f"STK callback error: {str(e)}")
        return JsonResponse({
            "ResultCode": 1,
            "ResultDesc": "Failed"
        }, status=400)

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
