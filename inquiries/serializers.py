from rest_framework import serializers
from .models import Inquiry, ServiceRequest, QuotationRequest

class InquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = '__all__'



class ServiceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = '__all__'

class QuotationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationRequest
        fields = '__all__'
