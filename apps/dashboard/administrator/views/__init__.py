from .users_views import (
    AdminUsersListView,
    UserDeleteView,
    UserUpdateView,
    UserVerificationDetailView,
    PendingVerificationListView,
    AddUserView,
    ExportUsersToExcelView
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

from .discounts_views import(
    DiscountListView,
    DiscountCreateView,
    DiscountDeleteView,
    DiscountUpdateView
)

from .tutorials_views import (
    TutorialsListView,
    TutorialCreateView,
    TutorialUpdateView,
    TutorialDeleteView,
    TutorialEmbedView
)

from .drugs_views import *
from .index_views import admin_dashboard_view

from .plan_views import *
from .analysis_views import *
from .subscriptions_views import *
from .notifications_views import (
    NotificationDashboardView,
    AnnouncementCreateView,
    AnnouncementUpdateView,
    AnnouncementDeleteView,
    AnnouncementDetailView,
    NotificationDeleteView,
    NotificationCreateView,
    UserSearchJsonView,
)
