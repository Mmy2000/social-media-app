from .models import CommentLike, Post, Comment, Like, PostAttachment
from rest_framework import serializers
from accounts.models import User, UserProfile

class SampleUserProfileData(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    class Meta:
        model = UserProfile
        fields = ["full_name","profile_picture"]

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        url = obj.get_profile_picture
        return request.build_absolute_uri(url) if request else url

class SampleUserData(serializers.ModelSerializer):
    profile = SampleUserProfileData(source="userprofile", read_only=True)
    class Meta:
        model = User
        fields = ["id","profile"]

class PostAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAttachment
        fields = ("id", "image", "created_by", "created_at", "updated_at")


class CommentLikeSerializer(serializers.ModelSerializer):
    created_by = SampleUserData(read_only=True)
    class Meta:
        model = CommentLike
        fields = ("id", "created_by", "comment", "created_at")
        read_only_fields = ("id", "created_by", "created_at")


class CommentSerializer(serializers.ModelSerializer):
    created_by = SampleUserData(read_only=True)
    replies = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "created_by",
            "post",
            "parent",
            "content",
            "time_since_created",
            "time_since_updated",
            "replies",
            "likes",  # <-- Add likes field (optional)
            "like_count",  # <-- Add like_count field (optional)
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_replies(self, obj):
        replies = obj.replies.all()  # Get all replies (children)
        return CommentSerializer(replies, many=True, context=self.context).data

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_likes(self, obj):
        likes = obj.likes.select_related('created_by', 'created_by__userprofile')  # Avoid N+1 queries
        data = []

        for like in likes:
            user = like.created_by
            profile_picture_url = None
            request = self.context.get("request")

            if hasattr(user, 'userprofile') and user.userprofile.profile_picture:
                profile_picture_url = request.build_absolute_uri(
                    user.userprofile.get_profile_picture
                )

            else:
                # fallback if no profile or no picture
                profile_picture_url = "/static/default_images/default_profile_picture.jpg"
                profile_picture_url = request.build_absolute_uri(profile_picture_url)

            data.append({
                "id": user.id,
                "username": user.username,
                "image": profile_picture_url,
            })

        return data

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["created_by"] = user
        return super().create(validated_data)


class PostLikeSerializer(serializers.ModelSerializer):
    created_by = SampleUserData(read_only=True)

    class Meta:
        model = Like
        fields = ("id", "created_by", "time_since_created","time_since_updated")


class PostSerializer(serializers.ModelSerializer):
    attachments = PostAttachmentSerializer(many=True)
    created_by = SampleUserData(read_only=True)
    likes = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "created_by",
            "likes",
            "like_count",
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
        return CommentSerializer(comments, many=True, context=self.context).data

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_likes(self, obj):
        likes = obj.likes.select_related('created_by', 'created_by__userprofile')
        data = []
        request = self.context.get("request")

        for like in likes:
            user = like.created_by
            profile_picture_url = None

            if hasattr(user, 'userprofile') and user.userprofile.profile_picture:
                profile_picture_url = request.build_absolute_uri(
                    user.userprofile.get_profile_picture
                )
            else:
                # fallback if no profile or no picture
                profile_picture_url = "/static/default_images/default_profile_picture.jpg"
                profile_picture_url = request.build_absolute_uri(profile_picture_url)

            data.append({
                "id": user.id,
                "username": user.username,
                "image": profile_picture_url,
            })
        return data

    def get_like_count(self, obj):
        return obj.likes.count()


class PostCreateAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAttachment
        fields = ["id", "image"]


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
        print("role", validated_data.get("role"))
        print("content", validated_data.get("content"))
        print("attachments", files)

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
