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
    attachments = PostAttachmentSerializer(many=True)
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

