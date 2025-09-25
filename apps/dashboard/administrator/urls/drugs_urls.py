from django.urls import path
from ..views import (
    DrugListView, 
    DrugCreateView, 
    DrugUpdateView, 
    DrugDeleteView,
    DrugDetailView
)

app_name = 'drugs'

urlpatterns = [
    path('drugs/', DrugListView.as_view(), name='drug_list'),
    path('drugs/create/', DrugCreateView.as_view(), name='drug_create'),
    path('drugs/<int:pk>/update/', DrugUpdateView.as_view(), name='drug_update'),
    path('drugs/<int:pk>/delete/', DrugDeleteView.as_view(), name='drug_delete'),
    path('drugs/<int:pk>/detail/', DrugDetailView.as_view(), name='drug_detail'),
]
