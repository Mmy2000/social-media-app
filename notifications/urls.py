from django.urls import path
from .views import (
    NotificationListView,
    MarkNotificationAsReadView,
    MarkAllNotificationsAsReadView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path(
        "<int:pk>/mark-read/",
        MarkNotificationAsReadView.as_view(),
        name="mark-notification-read",
    ),
    path(
        "mark-all-read/",
        MarkAllNotificationsAsReadView.as_view(),
        name="mark-all-notifications-read",
    ),
]
