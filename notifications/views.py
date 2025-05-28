from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import action
from .models import Notification
from .serializers import NotificationSerializer
from core.responses import CustomResponse

# Create your views here.


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        unread_count = queryset.filter(is_read=False).count()
        serializer = self.get_serializer(queryset, many=True)
        return CustomResponse(
            data={"notifications": serializer.data, "unread_count": unread_count},
            status=status.HTTP_200_OK,
            message="Notifications retrieved successfully",
        )


class MarkNotificationAsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.is_read = True
            notification.save()
            serializer = NotificationSerializer(
                notification, context={"request": request}
            )
            return CustomResponse(
                data=serializer.data,
                status=status.HTTP_200_OK,
                message="Notification marked as read",
            )
        except Notification.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Notification not found"
            )


class MarkAllNotificationsAsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True
        )
        return CustomResponse(
            data={},
            status=status.HTTP_200_OK,
            message="All notifications marked as read",
        )
