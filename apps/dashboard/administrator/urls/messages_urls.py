from django.urls import path
from ..views import QuestionsListView, QuestionDetailView, QuestionActionView

app_name = 'questions'

urlpatterns = [
    path('questions/', QuestionsListView.as_view(), name='questions_list'),
    path('questions/<int:pk>/', QuestionDetailView.as_view(), name='questions_detail'),
    path('questions/<int:pk>/action/', QuestionActionView.as_view(), name='question_action'),
]
