from django.shortcuts import render
from rest_framework import status, generics
from posts.models import Post
from .serializers import PostSerializer, CommentSerializer, PostAttachmentSerializer
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

    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(data=serializer.data, status=status.HTTP_201_CREATED ,message="Post created successfully")
        return CustomResponse(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST, message="Failed to create post")

class PostDetailView(APIView):
    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            serializer = PostSerializer(post, context={"request": request})
            return CustomResponse(data=serializer.data, status=status.HTTP_200_OK ,message="Post retrieved successfully")
        except Post.DoesNotExist:
            return CustomResponse(status=status.HTTP_404_NOT_FOUND, message="Post not found")

    def put(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            serializer = PostSerializer(post, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return CustomResponse(data=serializer.data, status=status.HTTP_200_OK ,message="Post updated successfully")
            return CustomResponse(data=serializer.errors, status=400, message="Failed to update post")
        except Post.DoesNotExist:
            return CustomResponse(status=status.HTTP_404_NOT_FOUND, message="Post not found")

    def delete(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            post.delete()
            return CustomResponse(data={} , status=status.HTTP_200_OK ,message="Post deleted successfully")
        except Post.DoesNotExist:
            return CustomResponse(status=status.HTTP_404_NOT_FOUND, message="Post not found")
