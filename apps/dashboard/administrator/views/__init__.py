from .users_views import (
    AdminUsersListView,
    UserDeleteView,
    UserUpdateView,
    UserVerificationDetailView,
    PendingVerificationListView
)

from .categories_views import (
    CategoryCreateView,
    CategoryListView,
    CategoryDeleteView,
    CategoryUpdateView
)

from .prescriptions_views import(
    PrescriptionListView,
    PrescriptionCreateView,
    PrescriptionUpdateView,
    PrescriptionDeleteView,
    PrescriptionDetailView
)

from .contacts_views import (
    ContactsListView,
    ContactDetailView,
    ContactDeleteView,
    ContactMarkReadView,
    ContactsBulkDeleteView 
)

from .messages_views import (
    QuestionsListView,
    QuestionActionView,
    QuestionDetailView
)
