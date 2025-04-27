from rest_framework import status, generics, permissions
from posts.models import Like, Post
from .serializers import PostSerializer, CommentSerializer,PostLikeSerializer ,PostCreateSerializer
from rest_framework.views import APIView
from core.responses import CustomResponse


class PostView(APIView):
    def get(self, request):
        # Assuming you have a queryset of posts to serialize
        posts = Post.objects.all()
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
            return CustomResponse(data=serializer.data, status=status.HTTP_200_OK ,message="Post retrieved successfully")
        except Post.DoesNotExist:
            return CustomResponse(status=status.HTTP_404_NOT_FOUND, message="Post not found")

    def delete(self, request, pk):
        if not request.user.is_authenticated:
            return CustomResponse(
                data=None,
                status=status.HTTP_401_UNAUTHORIZED,
                message="Authentication required to create a post",
            )
        try:
            post = Post.objects.get(pk=pk)
            post.delete()
            return CustomResponse(data={} , status=status.HTTP_200_OK ,message="Post deleted successfully")
        except Post.DoesNotExist:
            return CustomResponse(status=status.HTTP_404_NOT_FOUND, message="Post not found")


class PostCreateAPIView(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)  # Just create, no need to capture response
        queryset = self.get_queryset().order_by("-created_at")  # or whatever ordering you want
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
                like = Like.objects.create(created_by=request.user)
                post.likes.add(like)
                post.likes_count += 1
                post.save()

                return CustomResponse(
                    data=serializer.data,
                    status=status.HTTP_200_OK,
                    message="Post liked successfully",
                )
            else:
                # Unlike: remove the Like object
                post.likes.remove(like)
                like.delete()
                post.likes_count -= 1
                post.save()

                return CustomResponse(
                    data=serializer.data,
                    status=status.HTTP_200_OK,
                    message="Post unliked successfully",
                )

        except Post.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Post not found"
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

        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(post=post)
            return CustomResponse(data=serializer.data,message="Comment added successfully" ,status=status.HTTP_201_CREATED)

        return CustomResponse(data={},message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
