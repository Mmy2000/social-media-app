from .models import Post, Comment, Like, PostAttachment
from rest_framework import serializers
from accounts.models import User, UserProfile

class SampleUserProfileData(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["full_name","profile_picture"]

class SampleUserData(serializers.ModelSerializer):
    profile = SampleUserProfileData(source="userprofile", read_only=True)
    class Meta:
        model = User
        fields = ["id","profile"]

class PostAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAttachment
        fields = ("id", "image", "video", "created_by", "created_at", "updated_at")

class CommentSerializer(serializers.ModelSerializer):
    created_by = SampleUserData(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "created_by", "content", "created_at", "updated_at")

class PostSerializer(serializers.ModelSerializer):
    attachments = PostAttachmentSerializer(many=True, read_only=True)
    created_by = SampleUserData(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "created_by",
            "likes",
            "likes_count",
            "comments",
            "comments_count",
            "content",
            "role",
            "attachments",
            "time_since_created",
            "time_since_updated",
        )
