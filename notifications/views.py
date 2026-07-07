from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.permissions import IsSuperAdmin
from .models import Notice, Notification
from .serializers import NoticeSerializer, NotificationSerializer


class NoticeListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notices = Notice.objects.filter(
            audience__in=["ALL", request.user.role]
        ).order_by("-id")

        serializer = NoticeSerializer(notices, many=True)

        return Response({
            "success": True,
            "count": notices.count(),
            "data": serializer.data
        })

    def post(self, request):
        if request.user.role != "SUPER_ADMIN":
            return Response({
                "success": False,
                "message": "Only super admin can create notice."
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = NoticeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)

        return Response({
            "success": True,
            "message": "Notice created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by("-id")

        serializer = NotificationSerializer(notifications, many=True)

        return Response({
            "success": True,
            "count": notifications.count(),
            "unread_count": notifications.filter(is_read=False).count(),
            "data": serializer.data
        })


class NotificationMarkReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=request.user
            )
        except Notification.DoesNotExist:
            return Response({
                "success": False,
                "message": "Notification not found."
            }, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.save()

        return Response({
            "success": True,
            "message": "Notification marked as read.",
            "data": NotificationSerializer(notification).data
        })