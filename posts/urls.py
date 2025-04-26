from django.urls import path
from .views import PostView,PostDetailView
urlpatterns = [
    path(
        "", PostView.as_view(), name="post-list-create"
    ),  # for GET (list) and POST (create)
    path(
        "<int:pk>/", PostDetailView.as_view(), name="post-detail"
    ),  # for GET, PUT, DELETE a specific post
]
