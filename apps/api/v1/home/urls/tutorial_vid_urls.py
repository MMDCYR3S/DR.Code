from django.urls import path
from ..views import TutorialListView

urlpatterns = [
    path('tutorials/', TutorialListView.as_view(), name='tutorial_list'),
]
