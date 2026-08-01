from django.urls import path

from .views import (
    AdminNotificationOverviewAPIView,
    NoticeListCreateAPIView,
    NotificationDeleteAllReadAPIView,
    NotificationDeleteAPIView,
    NotificationListAPIView,
    NotificationMarkAllReadAPIView,
    NotificationMarkReadAPIView,
)


urlpatterns = [
    path(
        "notices/",
        NoticeListCreateAPIView.as_view(),
        name="notice-list-create",
    ),

    path(
        "",
        NotificationListAPIView.as_view(),
        name="notification-list",
    ),

    path(
        "mark-all-read/",
        NotificationMarkAllReadAPIView.as_view(),
        name="notification-mark-all-read",
    ),

    path(
        "delete-all-read/",
        NotificationDeleteAllReadAPIView.as_view(),
        name="notification-delete-all-read",
    ),

    path(
        "admin/overview/",
        AdminNotificationOverviewAPIView.as_view(),
        name="admin-notification-overview",
    ),

    path(
        "<int:notification_id>/read/",
        NotificationMarkReadAPIView.as_view(),
        name="notification-read",
    ),

    path(
        "<int:notification_id>/delete/",
        NotificationDeleteAPIView.as_view(),
        name="notification-delete",
    ),
]