from django.urls import path
from ..views import ContactView, ContactInfoView

urlpatterns = [
    path('contact/', ContactView.as_view(), name='contact'),
    path('contact/info/', ContactInfoView.as_view(), name='contact_info'),
]