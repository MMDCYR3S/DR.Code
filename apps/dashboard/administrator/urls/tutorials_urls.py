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
    path('tutorials/', TutorialsListView.as_view(), name='tutorial_list'),
    path('tutorials/create/', TutorialCreateView.as_view(), name='tutorial_create'),
    path('tutorials/<int:tutorial_id>/update/', TutorialUpdateView.as_view(), name='tutorial_update'),
    path('tutorials/<int:tutorial_id>/delete/', TutorialDeleteView.as_view(), name='tutorial_delete'),
    path('tutorials/<int:tutorial_id>/embed/', TutorialEmbedView.as_view(), name='tutorial_embed'),
]