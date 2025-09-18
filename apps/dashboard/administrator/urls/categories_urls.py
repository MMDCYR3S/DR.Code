# your_app/urls.py

from django.urls import path
from ..views import(
    CategoryListView,
    CategoryDeleteView,
    CategoryCreateView,
    CategoryUpdateView
)

app_name = 'categories'

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),
]