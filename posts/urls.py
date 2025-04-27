from django.urls import path
from .views import PostView,PostDetailView, PostCreateAPIView, PostUpdateAPIView
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
]
