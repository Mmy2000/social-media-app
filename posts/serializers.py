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
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'created_by',
            'post',
            'parent',
            'content',
            'time_since_created',
            'time_since_updated',
            'replies'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_replies(self, obj):
        replies = obj.replies.all()  # Get all replies (children)
        return CommentSerializer(replies, many=True).data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)

class PostLikeSerializer(serializers.ModelSerializer):
    created_by = SampleUserData(read_only=True)

    class Meta:
        model = Like
        fields = ("id", "created_by", "time_since_created","time_since_updated")


class PostSerializer(serializers.ModelSerializer):
    attachments = PostAttachmentSerializer(many=True)
    created_by = SampleUserData(read_only=True)
    likes = PostLikeSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

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

    def get_comments(self, obj):
        comments = obj.comments.filter(parent=None)  # Only top-level comments
        return CommentSerializer(comments, many=True).data

    def get_comments_count(self, obj):
        return obj.comments.count()


class PostCreateAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAttachment
        fields = ["id", "image", "video"]


class PostCreateSerializer(serializers.ModelSerializer):
    attachments = PostCreateAttachmentSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = ["id", "content", "role", "attachments"]

    def create(self, validated_data):
        request = self.context.get("request")
        files = request.FILES.getlist("attachments")  # <- get uploaded files

        post = Post.objects.create(
            content=validated_data.get("content"),
            role=validated_data.get("role"),
            created_by=request.user,  # directly use request.user
        )

        for file in files:
            attachment = PostAttachment.objects.create(
                created_by=request.user,
            )
            # Determine file type
            if file.content_type.startswith("image/"):
                attachment.image = file
            elif file.content_type.startswith("video/"):
                attachment.video = file
            attachment.save()
            post.attachments.add(attachment)

        return post

    def update(self, instance, validated_data):
        request = self.context.get('request')
        files = request.FILES.getlist('attachments')  # get uploaded files

        instance.content = validated_data.get('content', instance.content)
        instance.role = validated_data.get('role', instance.role)
        instance.save()

        if files:
            # Always clear old attachments if new files are uploaded
            instance.attachments.all().delete()  # delete attachment objects (optional: also delete files from storage)

            for file in files:
                attachment = PostAttachment.objects.create(
                    created_by=instance.created_by,
                )
                if file.content_type.startswith('image/'):
                    attachment.image = file
                elif file.content_type.startswith('video/'):
                    attachment.video = file
                attachment.save()
                instance.attachments.add(attachment)

        return instance
