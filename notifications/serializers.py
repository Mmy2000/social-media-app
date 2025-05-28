from rest_framework import serializers
from .models import Notification
from posts.serializers import PostSerializer, CommentSerializer
from accounts.serializers import FriendSerializer


class NotificationSerializer(serializers.ModelSerializer):
    sender = FriendSerializer(read_only=True)
    post = PostSerializer(read_only=True)
    comment = CommentSerializer(read_only=True)
    notification_message = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "sender",
            "notification_type",
            "post",
            "comment",
            "is_read",
            "created_at",
            "notification_message",
        ]
        read_only_fields = [
            "id",
            "sender",
            "notification_type",
            "post",
            "comment",
            "created_at",
            "notification_message",
        ]

    def get_notification_message(self, obj):
        """Generate a human-readable message for the notification"""
        sender_name = obj.sender.userprofile.full_name
        if obj.notification_type == "like":
            return f"{sender_name} liked your post"
        elif obj.notification_type == "comment":
            return f"{sender_name} commented on your post"
        elif obj.notification_type == "reply":
            return f"{sender_name} replied to your comment"
        elif obj.notification_type == "comment_like":
            return f"{sender_name} liked your comment"
        elif obj.notification_type == "friend_request":
            return f"{sender_name} sent you a friend request"
        elif obj.notification_type == "friend_request_accepted":
            return f"{sender_name} accepted your friend request"
        elif obj.notification_type == "friend_request_rejected":
            return f"{sender_name} rejected your friend request"
        elif obj.notification_type == "friend_request_cancelled":
            return f"{sender_name} cancelled their friend request"
        return ""
