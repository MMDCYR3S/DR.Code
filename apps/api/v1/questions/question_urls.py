from django.urls import path
from .question_views import QuestionCreateView

app_name = 'questions'

urlpatterns = [
    path('create/', QuestionCreateView.as_view(), name='question-create'),
]
