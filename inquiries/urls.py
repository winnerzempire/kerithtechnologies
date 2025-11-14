# inquiries/urls.py
from django.urls import path
from .views import contact_form  # import the function-based view
from .views import ServiceRequestCreateView,QuotationRequestCreateView,service_request_form,quotation_request_form



urlpatterns = [
    path('contact/', contact_form, name='contact_form'),  # use the function view
    path('service-request/', service_request_form, name='service_request_form'),
    path('quotation-request/', quotation_request_form, name='quotation_request_form'),
]
