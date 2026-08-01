from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User

from .models import (
    Notice,
    Notification,
)
from .serializers import (
    NoticeSerializer,
    NotificationReadStatusSerializer,
    NotificationSerializer,
)


def get_notice_recipient_queryset(audience):
    users = User.objects.filter(
        is_active=True,
    )

    if audience == "ALL":
        return users.exclude(
            role="SUPER_ADMIN",
        )

    return users.filter(
        role=audience,
    )


def create_notice_notifications(notice):
    recipients = get_notice_recipient_queryset(
        notice.audience
    )

    notifications = [
        Notification(
            user=user,
            title=notice.title,
            message=notice.message,
            notification_type="NOTICE",
            action_url="../notices.html",
            related_object_id=notice.id,
        )
        for user in recipients.iterator()
    ]

    if notifications:
        Notification.objects.bulk_create(
            notifications,
            batch_size=500,
        )

    return len(notifications)


class NoticeListCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        notices = Notice.objects.filter(
            audience__in=[
                "ALL",
                request.user.role,
            ]
        ).select_related(
            "created_by",
        ).order_by(
            "-id"
        )

        serializer = NoticeSerializer(
            notices,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": notices.count(),
            "data": serializer.data,
        })

    @transaction.atomic
    def post(self, request):
        if request.user.role != "SUPER_ADMIN":
            return Response(
                {
                    "success": False,
                    "message": (
                        "Only Super Admin can create a notice."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = NoticeSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        notice = serializer.save(
            created_by=request.user,
        )

        notification_count = (
            create_notice_notifications(
                notice
            )
        )

        response_serializer = NoticeSerializer(
            notice,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Notice created and notifications sent successfully."
                ),
                "notification_count": notification_count,
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class NotificationListAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user,
        )

        read_status = request.query_params.get(
            "status",
            "ALL",
        ).upper()

        notification_type = request.query_params.get(
            "type",
            "ALL",
        ).upper()

        search = request.query_params.get(
            "search",
            "",
        ).strip()

        if read_status == "READ":
            notifications = notifications.filter(
                is_read=True,
            )

        elif read_status == "UNREAD":
            notifications = notifications.filter(
                is_read=False,
            )

        if notification_type != "ALL":
            notifications = notifications.filter(
                notification_type=notification_type,
            )

        if search:
            notifications = notifications.filter(
                Q(title__icontains=search)
                | Q(message__icontains=search)
            )

        notifications = notifications.order_by(
            "-id"
        )

        serializer = NotificationSerializer(
            notifications,
            many=True,
            context={
                "request": request,
            },
        )

        all_user_notifications = (
            Notification.objects.filter(
                user=request.user,
            )
        )

        return Response({
            "success": True,
            "count": notifications.count(),
            "total_count": all_user_notifications.count(),
            "unread_count": (
                all_user_notifications.filter(
                    is_read=False,
                ).count()
            ),
            "read_count": (
                all_user_notifications.filter(
                    is_read=True,
                ).count()
            ),
            "data": serializer.data,
        })


class NotificationMarkReadAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def patch(
        self,
        request,
        notification_id,
    ):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=request.user,
            )

        except Notification.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Notification not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = NotificationReadStatusSerializer(
            data=request.data
            or {
                "is_read": True,
            }
        )

        serializer.is_valid(
            raise_exception=True,
        )

        is_read = serializer.validated_data[
            "is_read"
        ]

        if is_read:
            notification.mark_as_read()

        else:
            notification.mark_as_unread()

        notification.save(
            update_fields=[
                "is_read",
                "read_at",
            ]
        )

        return Response({
            "success": True,
            "message": (
                "Notification marked as read."
                if is_read
                else "Notification marked as unread."
            ),
            "data": NotificationSerializer(
                notification
            ).data,
        })


class NotificationMarkAllReadAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def patch(self, request):
        unread_notifications = (
            Notification.objects.filter(
                user=request.user,
                is_read=False,
            )
        )

        updated_count = (
            unread_notifications.update(
                is_read=True,
                read_at=timezone.now(),
            )
        )

        return Response({
            "success": True,
            "message": (
                "All notifications marked as read."
            ),
            "updated_count": updated_count,
            "unread_count": 0,
        })


class NotificationDeleteAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def delete(
        self,
        request,
        notification_id,
    ):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=request.user,
            )

        except Notification.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Notification not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.delete()

        return Response({
            "success": True,
            "message": (
                "Notification deleted successfully."
            ),
        })


class NotificationDeleteAllReadAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def delete(self, request):
        deleted_count, _ = (
            Notification.objects.filter(
                user=request.user,
                is_read=True,
            ).delete()
        )

        return Response({
            "success": True,
            "message": (
                "All read notifications deleted successfully."
            ),
            "deleted_count": deleted_count,
        })


class AdminNotificationOverviewAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        if request.user.role != "SUPER_ADMIN":
            return Response(
                {
                    "success": False,
                    "message": (
                        "Only Super Admin can view notification overview."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        notifications = Notification.objects.all()

        role_distribution = (
            notifications.values(
                "user__role",
            )
            .annotate(
                count=Count("id"),
                unread_count=Count(
                    "id",
                    filter=Q(
                        is_read=False,
                    ),
                ),
            )
            .order_by(
                "user__role",
            )
        )

        type_distribution = (
            notifications.values(
                "notification_type",
            )
            .annotate(
                count=Count("id"),
            )
            .order_by(
                "notification_type",
            )
        )

        return Response({
            "success": True,
            "data": {
                "total_count": (
                    notifications.count()
                ),
                "unread_count": (
                    notifications.filter(
                        is_read=False,
                    ).count()
                ),
                "read_count": (
                    notifications.filter(
                        is_read=True,
                    ).count()
                ),
                "role_distribution": list(
                    role_distribution
                ),
                "type_distribution": list(
                    type_distribution
                ),
            },
        })