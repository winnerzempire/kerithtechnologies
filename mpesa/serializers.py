from rest_framework import serializers
from .models import MpesaTransaction, MpesaConfiguration

class MpesaTransactionSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    formatted_phone = serializers.ReadOnlyField()
    is_successful = serializers.ReadOnlyField()
    
    class Meta:
        model = MpesaTransaction
        fields = [
            'id', 'transaction_id', 'order', 'order_number', 'phone_number', 
            'formatted_phone', 'amount', 'status', 'is_complete', 'is_successful',
            'mpesa_receipt_number', 'transaction_date', 'created_at'
        ]
        read_only_fields = [
            'transaction_id', 'status', 'is_complete', 'is_successful',
            'mpesa_receipt_number', 'transaction_date', 'created_at'
        ]

class MpesaPaymentRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15, required=True)
    order_id = serializers.IntegerField(required=True)
    
    def validate_phone_number(self, value):
        """Validate and format phone number"""
        phone = value.strip().replace(' ', '').replace('+', '')
        if phone.startswith('0') and len(phone) == 10:
            return '254' + phone[1:]
        elif phone.startswith('254') and len(phone) == 12:
            return phone
        else:
            raise serializers.ValidationError("Invalid phone number format. Use 07XXXXXXXX or 2547XXXXXXXX")

class MpesaConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaConfiguration
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']