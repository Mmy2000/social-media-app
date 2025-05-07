from rest_framework import serializers
from .models import Conversation, ConversationMessage
from accounts.serializers import FriendSerializer


class ConversationListSerializer(serializers.ModelSerializer):
    users = FriendSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id",
            "users",
            "modified_at",
        )


class ConversationDetailSerializer(serializers.ModelSerializer):
    users = FriendSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id",
            "users",
            "modified_at",
        )


class ConversationMessageSerializer(serializers.ModelSerializer):
    sent_to = FriendSerializer(many=False, read_only=True)
    created_by = FriendSerializer(many=False, read_only=True)

    class Meta:
        model = ConversationMessage
        fields = (
            "id",
            "body",
            "sent_to",
            "created_by",
        )
