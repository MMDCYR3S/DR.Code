from django.urls import path
from ..views import (
    TutorialsListView,
    TutorialCreateView,
    TutorialUpdateView,
    TutorialDeleteView,
    TutorialEmbedView
) 

app_name = "tutorials"

urlpatterns = [
    path('tutorials/', TutorialsListView.as_view(), name='admin_tutorials'),
    path('tutorials/create/', TutorialCreateView.as_view(), name='admin_tutorials_create'),
    path('tutorials/<int:tutorial_id>/update/', TutorialUpdateView.as_view(), name='admin_tutorials_update'),
    path('tutorials/<int:tutorial_id>/delete/', TutorialDeleteView.as_view(), name='admin_tutorials_delete'),
    path('tutorials/embed/<int:tutorial_id>/', TutorialEmbedView.as_view(), name='embed'),
]
