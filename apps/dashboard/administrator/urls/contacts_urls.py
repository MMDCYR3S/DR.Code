from django.urls import path
from ..views import (
    ContactsListView,
    ContactDetailView,
    ContactDeleteView,
    ContactMarkReadView,
    ContactsBulkDeleteView
)

app_name = "contacts"

urlpatterns = [
    path('contacts/', ContactsListView.as_view(), name='contacts_list'),
    path('contacts/<int:pk>/', ContactDetailView.as_view(), name='contact_detail'),
    path('contacts/<int:pk>/mark-read/', ContactMarkReadView.as_view(), name='contact_mark_read'),
    path('contacts/<int:pk>/delete/', ContactDeleteView.as_view(), name='contact_delete'),
    path('contacts/bulk-delete/', ContactsBulkDeleteView.as_view(), name='contacts_bulk_delete'),
]
