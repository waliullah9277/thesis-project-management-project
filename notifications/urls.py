from django.urls import path

from .views import (
    NoticeListCreateAPIView,
    NotificationListAPIView,
    NotificationMarkReadAPIView,
)


urlpatterns = [
    path("notices/", NoticeListCreateAPIView.as_view(), name="notice-list-create"),
    path("", NotificationListAPIView.as_view(), name="notification-list"),
    path("<int:notification_id>/read/", NotificationMarkReadAPIView.as_view(), name="notification-read"),
]