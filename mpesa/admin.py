from django.contrib import admin
from .models import MpesaTransaction, MpesaConfiguration, MpesaWebhookLog

@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id', 'order', 'phone_number', 'amount', 
        'status', 'is_complete', 'created_at'
    ]
    list_filter = ['status', 'is_complete', 'transaction_type', 'created_at']
    search_fields = [
        'transaction_id', 'merchant_request_id', 'checkout_request_id',
        'order__order_number', 'phone_number', 'mpesa_receipt_number'
    ]
    readonly_fields = [
        'transaction_id', 'merchant_request_id', 'checkout_request_id',
        'created_at', 'updated_at', 'callback_received_at',
        'init_request_data', 'callback_data'
    ]
    list_editable = ['status']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('order', 'transaction_id', 'status', 'is_complete')
        }),
        ('Payment Details', {
            'fields': ('phone_number', 'amount', 'transaction_type')
        }),
        ('M-Pesa Response', {
            'fields': (
                'merchant_request_id', 'checkout_request_id',
                'result_code', 'result_description', 'mpesa_receipt_number', 'transaction_date'
            )
        }),
        ('Raw Data', {
            'fields': ('init_request_data', 'callback_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'callback_received_at')
        }),
    )

@admin.register(MpesaConfiguration)
class MpesaConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'business_short_code', 'is_live', 'created_at']
    list_editable = ['is_live']
    
    def has_add_permission(self, request):
        # Only allow one configuration
        return not MpesaConfiguration.objects.exists()

@admin.register(MpesaWebhookLog)
class MpesaWebhookLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'transaction', 'ip_address', 'response_status', 'created_at']
    list_filter = ['response_status', 'created_at']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False