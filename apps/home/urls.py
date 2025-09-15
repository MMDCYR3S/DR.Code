# home/urls.py

from django.urls import path
from .views import (
    HomeView, ContactView, TutorialListView, AboutView
)

app_name = 'home'

urlpatterns = [
    # صفحه اصلی
    path('', HomeView.as_view(), name='index'),
    
    # صفحات اصلی
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('tutorials/', TutorialListView.as_view(), name='tutorials'),
]
