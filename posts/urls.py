from django.urls import path
from .views import PostView,PostDetailView, PostCreateAPIView, PostUpdateAPIView, PostLikeAPIView, AddCommentView, UpdateCommentView, DeleteCommentView
urlpatterns = [
    path(
        "", PostView.as_view(), name="post-list-create"
    ),  # for GET (list)
    path(
        "<int:pk>/", PostDetailView.as_view(), name="post-detail"
    ),  # for GET, DELETE a specific post
    path(
        "create/", PostCreateAPIView.as_view(), name="post-create"
    ),  # for creating a new post
    path(
        "<int:pk>/update/", PostUpdateAPIView.as_view(), name="post-update"
    ),  # for updating a specific post
    path(
        "<int:pk>/like/", PostLikeAPIView.as_view(), name="like"
    ),  # for liking a specific post
    path(
        "<int:pk>/comment/", AddCommentView.as_view(), name="add-comment"
    ),  # for adding a comment to a specific post
    path(
        "comment/<int:pk>/update/",
        UpdateCommentView.as_view(),
        name="update-comment",
    ),  # for updating a specific comment
    path(
        "comment/<int:pk>/delete/",
        DeleteCommentView.as_view(),
        name="delete-comment",
    ),  # for deleting a specific comment
]
