from django.urls import path
from ..views import QuestionsListView, QuestionDetailView, QuestionActionView

app_name = 'questions'

urlpatterns = [
    path('questions/', QuestionsListView.as_view(), name='list'),
    path('questions/<int:pk>/', QuestionDetailView.as_view(), name='detail'),
    path('questions/<int:pk>/action/', QuestionActionView.as_view(), name='action'),
]