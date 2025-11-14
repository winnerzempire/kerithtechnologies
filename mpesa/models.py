from django.db import models
from store.models import Order
from django.utils.translation import gettext_lazy as _

class MpesaTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('paybill', 'PayBill'),
        ('till', 'Buy Goods Till'),
        ('phone', 'Phone Number'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Order relationship
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='mpesa_transactions'
    )
    
    # M-Pesa transaction details
    transaction_id = models.CharField(max_length=50, unique=True, blank=True)
    merchant_request_id = models.CharField(max_length=50, blank=True)
    checkout_request_id = models.CharField(max_length=50, blank=True)
    
    # Payment details
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='paybill')
    
    # M-Pesa response fields
    result_code = models.IntegerField(null=True, blank=True)
    result_description = models.TextField(blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_complete = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    callback_received_at = models.DateTimeField(null=True, blank=True)
    
    # Raw responses (for debugging)
    init_request_data = models.JSONField(null=True, blank=True)
    callback_data = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'mpesa_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['merchant_request_id']),
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"MPesa {self.transaction_id} - {self.amount}"
    
    @property
    def is_successful(self):
        return self.status == 'success' and self.is_complete
    
    @property
    def formatted_phone(self):
        """Format phone number to 2547XXXXXXXX"""
        phone = self.phone_number.strip().replace(' ', '').replace('+', '')
        if phone.startswith('0'):
            return '254' + phone[1:]
        elif phone.startswith('254'):
            return phone
        else:
            return '254' + phone
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import uuid
            self.transaction_id = f"MPESA{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

class MpesaConfiguration(models.Model):
    name = models.CharField(max_length=100, default='Default Configuration')
    
    # API Credentials
    consumer_key = models.CharField(max_length=255)
    consumer_secret = models.CharField(max_length=255)
    business_short_code = models.CharField(max_length=10)
    passkey = models.CharField(max_length=255)
    
    # URLs
    callback_url = models.URLField(blank=True)
    validation_url = models.URLField(blank=True)
    confirmation_url = models.URLField(blank=True)
    
    # Environment
    is_live = models.BooleanField(default=False)
    
    # Transaction limits
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=150000.00)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'mpesa_configurations'
        verbose_name = 'M-Pesa Configuration'
        verbose_name_plural = 'M-Pesa Configurations'
    
    def __str__(self):
        return f"{self.name} ({'Live' if self.is_live else 'Sandbox'})"

class MpesaWebhookLog(models.Model):
    transaction = models.ForeignKey(
        MpesaTransaction, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='webhook_logs'
    )
    
    # Webhook data
    payload = models.JSONField()
    headers = models.JSONField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Response
    response_status = models.IntegerField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mpesa_webhook_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Webhook {self.id} - {self.created_at}"
