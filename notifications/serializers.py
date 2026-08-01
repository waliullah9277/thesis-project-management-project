from rest_framework import serializers

from .models import (
    Notice,
    Notification,
)


class NoticeSerializer(
    serializers.ModelSerializer
):
    created_by_name = serializers.SerializerMethodField()

    audience_display = serializers.CharField(
        source="get_audience_display",
        read_only=True,
    )

    class Meta:
        model = Notice

        fields = [
            "id",
            "title",
            "message",
            "audience",
            "audience_display",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "created_by",
            "created_at",
            "updated_at",
        ]

    def validate_title(self, value):
        value = str(value or "").strip()

        if not value:
            raise serializers.ValidationError(
                "Notice title is required."
            )

        return value

    def validate_message(self, value):
        value = str(value or "").strip()

        if not value:
            raise serializers.ValidationError(
                "Notice message is required."
            )

        return value

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None

        full_name = (
            f"{obj.created_by.first_name or ''} "
            f"{obj.created_by.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.created_by.email
            or "Super Admin"
        )


class NotificationSerializer(
    serializers.ModelSerializer
):
    notification_type_display = serializers.CharField(
        source="get_notification_type_display",
        read_only=True,
    )

    class Meta:
        model = Notification

        fields = [
            "id",
            "title",
            "message",
            "notification_type",
            "notification_type_display",
            "action_url",
            "related_object_id",
            "is_read",
            "read_at",
            "created_at",
        ]

        read_only_fields = fields


class NotificationReadStatusSerializer(
    serializers.Serializer
):
    is_read = serializers.BooleanField(
        required=True,
    )