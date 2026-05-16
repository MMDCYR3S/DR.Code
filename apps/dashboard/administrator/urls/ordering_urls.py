from django.urls import path

from ..views.ordering_views import (
    # DynamicField — مرحله ۱
    DynamicFieldGroupListView,
    DynamicFieldGroupCreateView,
    DynamicFieldGroupUpdateView,
    DynamicFieldGroupDeleteView,
    DynamicFieldSubGroupCreateView,
    DynamicFieldItemCreateView,

    # Order — مرحله ۲
    OrderListView,
    OrderCreateView,
    OrderUpdateView,
    OrderDeleteView,
    OrderDetailView,
    OrderSearchView,

    # Emergency — مرحله ۳
    EmergencyCreateView,
    EmergencyUpdateView,
    EmergencyDeleteView,

    # Media — مرحله ۴
    MediaView,
    MediaImageUploadView,
    MediaImageUpdateView,
    MediaImageDeleteView,
    MediaVideoCreateView,
    MediaVideoUpdateView,
    MediaVideoDeleteView,
)

app_name = "ordering"

urlpatterns = [

    # ─── DynamicField (مستقل از Order) ────────────────────────────────────────
    path(
        "ordering/dynamic-fields/",
        DynamicFieldGroupListView.as_view(),
        name="dynamic_field_list",
    ),
    path(
        "ordering/dynamic-fields/create/",
        DynamicFieldGroupCreateView.as_view(),
        name="dynamic_field_create",
    ),
    path(
        "ordering/dynamic-fields/<int:pk>/update/",
        DynamicFieldGroupUpdateView.as_view(),
        name="dynamic_field_update",
    ),
    path(
        "ordering/dynamic-fields/<int:pk>/delete/",
        DynamicFieldGroupDeleteView.as_view(),
        name="dynamic_field_delete",
    ),
    path(
        "ordering/dynamic-fields/<int:pk>/subgroups/create/",
        DynamicFieldSubGroupCreateView.as_view(),
        name="dynamic_subgroup_create",
    ),
    path(
        "ordering/dynamic-fields/subgroups/<int:pk>/items/create/",
        DynamicFieldItemCreateView.as_view(),
        name="dynamic_item_create",
    ),

    # ─── Order ────────────────────────────────────────────────────────────────
    path(
        "ordering/",
        OrderListView.as_view(),
        name="order_list",
    ),
    path(
        "ordering/create/",
        OrderCreateView.as_view(),
        name="order_create",
    ),
    path(
        "ordering/search/",
        OrderSearchView.as_view(),
        name="order_search",
    ),
    path(
        "ordering/<int:pk>/",
        OrderDetailView.as_view(),
        name="order_detail",
    ),
    path(
        "ordering/<int:pk>/update/",
        OrderUpdateView.as_view(),
        name="order_update",
    ),
    path(
        "ordering/<int:pk>/delete/",
        OrderDeleteView.as_view(),
        name="order_delete",
    ),

    # ─── Emergency — زیر ordering/<pk>/ ──────────────────────────────────────
    path(
        "ordering/<int:pk>/emergency/",
        EmergencyCreateView.as_view(),
        name="emergency_create",
    ),
    path(
        "ordering/<int:pk>/emergency/update/",
        EmergencyUpdateView.as_view(),
        name="emergency_update",
    ),
    path(
        "ordering/<int:pk>/emergency/delete/",
        EmergencyDeleteView.as_view(),
        name="emergency_delete",
    ),

    # ─── Media — زیر ordering/<pk>/ ───────────────────────────────────────────
    path(
        "ordering/<int:pk>/media/",
        MediaView.as_view(),
        name="media",
    ),
    path(
        "ordering/<int:pk>/media/images/upload/",
        MediaImageUploadView.as_view(),
        name="media_image_upload",
    ),
    path(
        "ordering/<int:pk>/media/images/<int:image_id>/update/",
        MediaImageUpdateView.as_view(),
        name="media_image_update",
    ),
    path(
        "ordering/<int:pk>/media/images/<int:image_id>/delete/",
        MediaImageDeleteView.as_view(),
        name="media_image_delete",
    ),
    path(
        "ordering/<int:pk>/media/videos/create/",
        MediaVideoCreateView.as_view(),
        name="media_video_create",
    ),
    path(
        "ordering/<int:pk>/media/videos/<int:video_id>/update/",
        MediaVideoUpdateView.as_view(),
        name="media_video_update",
    ),
    path(
        "ordering/<int:pk>/media/videos/<int:video_id>/delete/",
        MediaVideoDeleteView.as_view(),
        name="media_video_delete",
    ),
]