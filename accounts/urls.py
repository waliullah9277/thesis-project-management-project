from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginAPIView,
    ProfileAPIView,
    FirstPasswordChangeAPIView,
    ChangePasswordAPIView,
    LogoutAPIView,
    CreateUserAPIView,
    UserListAPIView,
    UserDetailAPIView,
    UserStatusUpdateAPIView,
)

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("profile/", ProfileAPIView.as_view(), name="profile"),
    path("first-password-change/", FirstPasswordChangeAPIView.as_view(), name="first-password-change"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("users/create/", CreateUserAPIView.as_view(), name="create-user"),
    path("users/", UserListAPIView.as_view(), name="user-list"),
    path("users/<int:user_id>/", UserDetailAPIView.as_view(), name="user-detail"),
    path("users/<int:user_id>/status/", UserStatusUpdateAPIView.as_view(), name="user-status-update"),
]