from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from .models import Inquiry
from .serializers import InquirySerializer

class InquiryCreateView(generics.CreateAPIView):
    queryset = Inquiry.objects.all()
    serializer_class = InquirySerializer
    permission_classes = [AllowAny]


@api_view(['POST'])
@permission_classes([AllowAny])
def contact_form(request):
    data = request.data
    try:
        # Save to database
        inquiry = Inquiry.objects.create(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            message=data.get('message'),
            subject=data.get('subject', 'Website Inquiry')
        )

        # Email details
        subject = f"New Inquiry from {inquiry.name}"
        message = f"""
You have received a new message from your website contact form.

Name: {inquiry.name}
Email: {inquiry.email}
Phone: {inquiry.phone}

Message:
{inquiry.message}
"""
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ['kerithofficetechltd@gmail.com'],  # Replace with your main inbox
                fail_silently=False,
            )
        except BadHeaderError:
            return Response({'error': 'Invalid email header found.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'success': 'Message saved and email sent!'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from .models import ServiceRequest, QuotationRequest
from .serializers import ServiceRequestSerializer, QuotationRequestSerializer


class ServiceRequestCreateView(generics.CreateAPIView):
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer
    permission_classes = [AllowAny]


class QuotationRequestCreateView(generics.CreateAPIView):
    queryset = QuotationRequest.objects.all()
    serializer_class = QuotationRequestSerializer
    permission_classes = [AllowAny]


@api_view(['POST'])
@permission_classes([AllowAny])
def service_request_form(request):
    data = request.data
    try:
        service_request = ServiceRequest.objects.create(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            company=data.get('company', ''),
            service_type=data.get('serviceType'),
            description=data.get('description'),
            preferred_date=data.get('preferredDate') or None,
            message=data.get('message', '')
        )

        subject = f"New Service Request from {service_request.name}"
        message = f"""
You have received a new service request from your website.

Name: {service_request.name}
Email: {service_request.email}
Phone: {service_request.phone}
Company: {service_request.company}
Service Type: {service_request.service_type}
Description: {service_request.description}
Preferred Date: {service_request.preferred_date}
Additional Message: {service_request.message}
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            ['kerithofficetechltd@gmail.com'],
            fail_silently=False,
        )
        return Response({'success': 'Service request saved and email sent!'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def quotation_request_form(request):
    data = request.data
    try:
        quotation_request = QuotationRequest.objects.create(
            name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            company=data.get('company', ''),
            product_details=data.get('product_details', ''),  # matches frontend
            quantity=int(data.get('quantity', 0)),
            message=data.get('message', '')
        )

        subject = f"New Quotation Request from {quotation_request.name}"
        message = f"""
You have received a new quotation request from your website.

Name: {quotation_request.name}
Email: {quotation_request.email}
Phone: {quotation_request.phone}
Company: {quotation_request.company}
Product Details: {quotation_request.product_details}
Quantity: {quotation_request.quantity}
Additional Message: {quotation_request.message}
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            ['kerithofficetechltd@gmail.com'],
            fail_silently=False,
        )
        return Response({'success': 'Quotation request saved and email sent!'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        print("Error:", e)  # 👈 print the error in console
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
