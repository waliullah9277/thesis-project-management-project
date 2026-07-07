from rest_framework import serializers
from .models import Notice, Notification


class NoticeSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = [
            "id",
            "title",
            "message",
            "audience",
            "created_by",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = ["created_by", "created_at"]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return None


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "is_read",
            "created_at",
        ]