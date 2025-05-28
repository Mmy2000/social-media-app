from rest_framework import status, generics, permissions
from posts.models import Comment, CommentLike, Like, Post
from .serializers import (
    PostSerializer,
    CommentSerializer,
    PostLikeSerializer,
    PostCreateSerializer,
    SharePostSerializer,
)
from rest_framework.views import APIView
from core.responses import CustomResponse
from notifications.models import Notification


class PostView(APIView):
    def get(self, request):
        user_ids = [request.user.id]
        if request.user.is_authenticated:
            for user in request.user.friends.all():
                user_ids.append(user.id)
            posts = Post.objects.filter(created_by_id__in=list(user_ids))
        else:
            posts = []
        serializer = PostSerializer(posts, many=True, context={"request": request})
        return CustomResponse(
            data=serializer.data,
            status=status.HTTP_200_OK,
            message="Posts retrieved successfully",
        )


class PostDetailView(APIView):
    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            serializer = PostSerializer(post, context={"request": request})
            return CustomResponse(
                data=serializer.data,
                status=status.HTTP_200_OK,
                message="Post retrieved successfully",
            )
        except Post.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Post not found"
            )

    def delete(self, request, pk):
        if not request.user.is_authenticated:
            return CustomResponse(
                data=None,
                status=status.HTTP_401_UNAUTHORIZED,
                message="Authentication required to delete a post",
            )
        try:
            post = Post.objects.get(pk=pk)
            post.delete()
            return CustomResponse(
                data={}, status=status.HTTP_200_OK, message="Post deleted successfully"
            )
        except Post.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Post not found"
            )


class PostCreateAPIView(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        super().create(
            request, *args, **kwargs
        )  # Just create, no need to capture response
        queryset = self.get_queryset().order_by(
            "-created_at"
        )  # or whatever ordering you want
        serializer = PostSerializer(queryset, many=True, context={"request": request})
        return CustomResponse(
            data=serializer.data,
            status=status.HTTP_201_CREATED,
            message="Post created successfully",
        )


class PostUpdateAPIView(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        instance = (
            self.get_object()
        )  # Because in update, self.get_object() gives you the updated instance
        serializer = PostSerializer(instance, context={"request": request})
        return CustomResponse(
            data=serializer.data,
            status=status.HTTP_200_OK,
            message="Post updated successfully",
        )


class PostLikeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            serializer = PostLikeSerializer(post, context={"request": request})

            # Check if a Like by this user already exists
            like = post.likes.filter(created_by=request.user).first()

            if not like:
                # Create a Like object
                Like.objects.create(created_by=request.user, post=post)

                # Create notification for the post owner
                if post.created_by != request.user:
                    Notification.objects.create(
                        recipient=post.created_by,
                        sender=request.user,
                        notification_type="like",
                        post=post,
                    )

                return CustomResponse(
                    data=serializer.data,
                    status=status.HTTP_200_OK,
                    message="Post liked successfully",
                )
            else:
                # Unlike: just delete the Like object
                like.delete()

                return CustomResponse(
                    data=serializer.data,
                    status=status.HTTP_200_OK,
                    message="Post unliked successfully",
                )

        except Post.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND,
                message="Post not found",
            )


class AddCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return CustomResponse(
                data={},
                message="Post not found",
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CommentSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            comment = serializer.save(post=post)

            # Create notification for the post owner
            if post.created_by != request.user:
                Notification.objects.create(
                    recipient=post.created_by,
                    sender=request.user,
                    notification_type="comment",
                    post=post,
                    comment=comment,
                )

            # If this is a reply, also notify the parent comment's author
            parent_comment_id = request.data.get("parent")
            if parent_comment_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_comment_id)
                    if parent_comment.created_by != request.user:
                        Notification.objects.create(
                            recipient=parent_comment.created_by,
                            sender=request.user,
                            notification_type="reply",
                            post=post,
                            comment=comment,
                        )
                except Comment.DoesNotExist:
                    pass

            return CustomResponse(
                data=serializer.data,
                message="Comment added successfully",
                status=status.HTTP_201_CREATED,
            )

        return CustomResponse(
            data={}, message=serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class CommentLikeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
            serializer = PostLikeSerializer(comment, context={"request": request})

            # Check if a Like by this user already exists
            like = comment.likes.filter(created_by=request.user).first()

            if not like:
                # Create a Like object
                CommentLike.objects.create(created_by=request.user, comment=comment)

                # Create notification for the comment owner
                if comment.created_by != request.user:
                    Notification.objects.create(
                        recipient=comment.created_by,
                        sender=request.user,
                        notification_type="comment_like",
                        post=comment.post,
                        comment=comment,
                    )

                return CustomResponse(
                    data=serializer.data,
                    status=status.HTTP_200_OK,
                    message="Comment liked successfully",
                )
            else:
                # Unlike: just delete the Like object
                like.delete()

                return CustomResponse(
                    data=serializer.data,
                    status=status.HTTP_200_OK,
                    message="Comment unliked successfully",
                )

        except Comment.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND,
                message="Comment not found",
            )


class UpdateCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return CustomResponse(
                data={},
                message="Comment not found",
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(
                data=serializer.data,
                message="Comment updated successfully",
                status=status.HTTP_200_OK,
            )

        return CustomResponse(
            data={}, message=serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class DeleteCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
            comment.delete()
            return CustomResponse(
                data={},
                message="Comment deleted successfully",
                status=status.HTTP_200_OK,
            )
        except Comment.DoesNotExist:
            return CustomResponse(
                data={}, message="Comment not found", status=status.HTTP_404_NOT_FOUND
            )


class SharePostView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SharePostSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            post = serializer.save()
            posts = Post.objects.all()
            posts = PostSerializer(posts, many=True, context={"request": request})
            return CustomResponse(
                data=posts.data,
                message="Post shared successfully",
                status=status.HTTP_201_CREATED,
            )
        return CustomResponse(
            data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )
