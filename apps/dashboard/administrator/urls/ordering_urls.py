from django.urls import path
from ..views.ordering_views import (
    OrderListView,
    OrderCreateView,
    OrderUpdateView,
    OrderDeleteView,
    DrugSearchView,
    SectionBulkSyncView,
)
from ..views import (
    # صفحه ترکیبی
    OrderExtendedFormView,

    # DynamicField
    DynamicFieldSyncView,
    DynamicFieldGroupDetailView,
    DynamicFieldGroupDeleteView,
    DynamicFieldSubGroupDeleteView,
    DynamicFieldItemDeleteView,
 
    # Emergency
    EmergencySyncView,
    EmergencyDetailView,
    EmergencyNodeDeleteView,
    EmergencyDeleteView,
 
    # Media
    MediaAddImageView,
    MediaAddImageBulkView,
    MediaUpdateImageView,
    MediaDeleteImageView,
    MediaAddVideoView,
    MediaUpdateVideoView,
    MediaDeleteVideoView,
)

app_name = 'ordering'

urlpatterns = [
    # ═══════════════════════════════════════════════════════
    # Order
    # ═══════════════════════════════════════════════════════
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/create/', OrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/edit/', OrderUpdateView.as_view(), name='order_update'),
    path('orders/<int:pk>/delete/', OrderDeleteView.as_view(), name='order_delete'),

    # ═══════════════════════════════════════════════════════
    # Section/Item/Condition — یک endpoint یکپارچه
    # ═══════════════════════════════════════════════════════
    path(
        'orders/<int:order_id>/sections/sync/',
        SectionBulkSyncView.as_view(),
        name='section_sync',
    ),

    # ═══════════════════════════════════════════════════════
    # Drug search (autocomplete)
    # ═══════════════════════════════════════════════════════
    path('drugs/search/', DrugSearchView.as_view(), name='drug_search'),


        # ──────────────────────────────────────────────────────────────
    #  صفحه ترکیبی — ایجاد و ویرایش
    # ──────────────────────────────────────────────────────────────
    path(
        "create/extended/",
        OrderExtendedFormView.as_view(),
        name="order_extended_create",
    ),
    path(
        "<int:pk>/extended/",
        OrderExtendedFormView.as_view(),
        name="order_extended_edit",
    ),
 
    # ──────────────────────────────────────────────────────────────
    #  DynamicField — پیش‌بالینی
    # ──────────────────────────────────────────────────────────────
    # GET  → دریافت همه گروه‌های یک Order
    path(
        "<int:order_id>/dynamic-fields/",
        DynamicFieldGroupDetailView.as_view(),
        name="dynamic_field_list",
    ),
    # POST → ذخیره یکجا (sync)
    path(
        "<int:order_id>/dynamic-fields/sync/",
        DynamicFieldSyncView.as_view(),
        name="dynamic_field_sync",
    ),
    # POST → حذف گروه
    path(
        "dynamic-fields/group/<int:group_id>/delete/",
        DynamicFieldGroupDeleteView.as_view(),
        name="dynamic_field_group_delete",
    ),
    # POST → حذف زیرگروه
    path(
        "dynamic-fields/subgroup/<int:subgroup_id>/delete/",
        DynamicFieldSubGroupDeleteView.as_view(),
        name="dynamic_field_subgroup_delete",
    ),
    # POST → حذف آیتم
    path(
        "dynamic-fields/item/<int:item_id>/delete/",
        DynamicFieldItemDeleteView.as_view(),
        name="dynamic_field_item_delete",
    ),
 
    # ──────────────────────────────────────────────────────────────
    #  Emergency Disposition — تعیین تکلیف اورژانسی
    # ──────────────────────────────────────────────────────────────
    # GET  → دریافت تعیین تکلیف
    path(
        "<int:order_id>/emergency/",
        EmergencyDetailView.as_view(),
        name="emergency_detail",
    ),
    # POST → ذخیره یکجا (sync)
    path(
        "<int:order_id>/emergency/sync/",
        EmergencySyncView.as_view(),
        name="emergency_sync",
    ),
    # POST → حذف گره
    path(
        "emergency/node/<int:node_id>/delete/",
        EmergencyNodeDeleteView.as_view(),
        name="emergency_node_delete",
    ),
    # POST → حذف کل disposition
    path(
        "emergency/<int:disposition_id>/delete/",
        EmergencyDeleteView.as_view(),
        name="emergency_delete",
    ),
 
    # ──────────────────────────────────────────────────────────────
    #  Media — فایل‌های پیوست
    # ──────────────────────────────────────────────────────────────
    # POST → آپلود یک تصویر
    path(
        "<int:order_id>/media/image/add/",
        MediaAddImageView.as_view(),
        name="media_image_add",
    ),
    # POST → آپلود چند تصویر
    path(
        "<int:order_id>/media/images/bulk/",
        MediaAddImageBulkView.as_view(),
        name="media_image_bulk",
    ),
    # POST → ویرایش تصویر
    path(
        "media/image/<int:image_id>/update/",
        MediaUpdateImageView.as_view(),
        name="media_image_update",
    ),
    # POST → حذف تصویر
    path(
        "media/image/<int:image_id>/delete/",
        MediaDeleteImageView.as_view(),
        name="media_image_delete",
    ),
    # POST → افزودن ویدیو
    path(
        "<int:order_id>/media/video/add/",
        MediaAddVideoView.as_view(),
        name="media_video_add",
    ),
    # POST → ویرایش ویدیو
    path(
        "media/video/<int:video_id>/update/",
        MediaUpdateVideoView.as_view(),
        name="media_video_update",
    ),
    # POST → حذف ویدیو
    path(
        "media/video/<int:video_id>/delete/",
        MediaDeleteVideoView.as_view(),
        name="media_video_delete",
    ),
]