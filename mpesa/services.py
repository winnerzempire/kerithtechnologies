import requests
import base64
import json
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import logging

logger = logging.getLogger(__name__)

class MpesaGateway:
    def __init__(self, config=None):
        self.config = config
        if not config:
            from .models import MpesaConfiguration
            self.config = MpesaConfiguration.objects.first()
        
        if not self.config:
            raise Exception("M-Pesa configuration not found")
        
        self.base_url = (
            "https://api.safaricom.co.ke" 
            if self.config.is_live 
            else "https://sandbox.safaricom.co.ke"
        )
        self.access_token = None
        self.token_expiry = None
    
    def get_access_token(self):
        """Get M-Pesa OAuth access token"""
        if self.access_token and self.token_expiry and timezone.now() < self.token_expiry:
            return self.access_token
        
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        
        # Create authentication string
        auth_string = f"{self.config.consumer_key}:{self.config.consumer_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data['access_token']
            # Token expires in 1 hour, set expiry to 55 minutes for safety
            self.token_expiry = timezone.now() + timezone.timedelta(minutes=55)
            
            logger.info("Successfully obtained M-Pesa access token")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get M-Pesa access token: {str(e)}")
            raise Exception(f"Failed to get access token: {str(e)}")
    
    def generate_password(self, timestamp):
        """Generate M-Pesa API password"""
        data = f"{self.config.business_short_code}{self.config.passkey}{timestamp}"
        return base64.b64encode(data.encode()).decode()
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url=None):
        """Initiate STK push request"""
        try:
            access_token = self.get_access_token()
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            payload = {
                "BusinessShortCode": self.config.business_short_code,
                "Password": self.generate_password(timestamp),
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": str(int(amount)),  # M-Pesa expects integer amount
                "PartyA": self.format_phone_number(phone_number),
                "PartyB": self.config.business_short_code,
                "PhoneNumber": self.format_phone_number(phone_number),
                "CallBackURL": callback_url or self.config.callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Initiating STK push for {phone_number}, amount: {amount}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            logger.info(f"STK push response: {response_data}")
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'merchant_request_id': response_data.get('MerchantRequestID'),
                    'checkout_request_id': response_data.get('CheckoutRequestID'),
                    'response_description': response_data.get('ResponseDescription'),
                    'customer_message': response_data.get('CustomerMessage'),
                    'raw_response': response_data
                }
            else:
                return {
                    'success': False,
                    'error_code': response_data.get('errorCode'),
                    'error_message': response_data.get('errorMessage'),
                    'raw_response': response_data
                }
                
        except Exception as e:
            logger.error(f"STK push failed: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    def format_phone_number(self, phone_number):
        """Format phone number to 2547XXXXXXXX format"""
        phone = phone_number.strip().replace(' ', '').replace('+', '')
        if phone.startswith('0'):
            return '254' + phone[1:]
        elif phone.startswith('254'):
            return phone
        else:
            return '254' + phone
    
    def check_transaction_status(self, checkout_request_id):
        """Check status of a transaction"""
        try:
            access_token = self.get_access_token()
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            payload = {
                "BusinessShortCode": self.config.business_short_code,
                "Password": self.generate_password(timestamp),
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'result_code': response_data.get('ResultCode'),
                    'result_description': response_data.get('ResultDesc'),
                    'raw_response': response_data
                }
            else:
                return {
                    'success': False,
                    'error_message': response_data.get('errorMessage', 'Unknown error'),
                    'raw_response': response_data
                }
                
        except Exception as e:
            logger.error(f"Transaction status check failed: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }

class MpesaCallbackHandler:
    """Handle M-Pesa callback responses"""
    
    @staticmethod
    def handle_stk_callback(callback_data):
        """
        Handle STK push callback from M-Pesa
        """
        from .models import MpesaTransaction
        
        try:
            body = callback_data.get('Body', {})
            stk_callback = body.get('stkCallback', {})
            
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_description = stk_callback.get('ResultDesc')
            
            logger.info(f"Processing callback for {checkout_request_id}, ResultCode: {result_code}")
            
            # Find transaction
            try:
                transaction = MpesaTransaction.objects.get(
                    checkout_request_id=checkout_request_id
                )
            except MpesaTransaction.DoesNotExist:
                logger.error(f"Transaction not found for checkout_request_id: {checkout_request_id}")
                return False
            
            # Update transaction with callback data
            transaction.callback_data = callback_data
            transaction.result_code = result_code
            transaction.result_description = result_description
            transaction.callback_received_at = timezone.now()
            
            # Check if payment was successful
            if result_code == 0:
                # Payment successful
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                items = callback_metadata.get('Item', [])
                
                for item in items:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        transaction.mpesa_receipt_number = item.get('Value', '')
                    elif item.get('Name') == 'Amount':
                        transaction.amount = item.get('Value', transaction.amount)
                    elif item.get('Name') == 'TransactionDate':
                        transaction.transaction_date = timezone.make_aware(
                            datetime.strptime(str(item.get('Value')), '%Y%m%d%H%M%S')
                        )
                    elif item.get('Name') == 'PhoneNumber':
                        transaction.phone_number = item.get('Value', transaction.phone_number)
                
                transaction.status = 'success'
                transaction.is_complete = True
                
                # Update order status
                transaction.order.payment_status = 'paid'
                transaction.order.status = 'confirmed'
                transaction.order.paid_at = timezone.now()
                transaction.order.transaction_id = transaction.mpesa_receipt_number
                transaction.order.save()
                
                logger.info(f"Payment successful for order {transaction.order.order_number}")
                
            else:
                # Payment failed
                transaction.status = 'failed'
                transaction.is_complete = True
                
                # Update order status
                transaction.order.payment_status = 'failed'
                transaction.order.save()
                
                logger.warning(f"Payment failed for order {transaction.order.order_number}: {result_description}")
            
            transaction.save()
            return True
            
        except Exception as e:
            logger.error(f"Error handling M-Pesa callback: {str(e)}")
            return False