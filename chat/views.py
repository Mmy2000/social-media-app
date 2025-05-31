from django.shortcuts import get_object_or_404
from accounts.models import User
from chat.models import Conversation
from chat.serializers import ConversationDetailSerializer, ConversationListSerializer, ConversationMessageSerializer
from core.responses import CustomResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

# Create your views here.


class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = request.user.conversations.all()
        serializer = ConversationListSerializer(conversations, many=True,context={'request': request})
        return CustomResponse(data=serializer.data, status=200)

class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        conversation = get_object_or_404(request.user.conversations, pk=pk)
        conversation_serializer = ConversationDetailSerializer(conversation,context={'request': request})
        messages_serializer = ConversationMessageSerializer(conversation.messages.all(), many=True,context={'request': request})
        return CustomResponse(
            data={
                "conversation": conversation_serializer.data,
                "messages": messages_serializer.data
            },
            status=200
        )

class StartConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return CustomResponse(
                data={},
                status=404,
                message="User not found."
            )

        conversations = Conversation.objects.filter(users__in=[user_id]).filter(users__in=[request.user.id])

        if conversations.exists():
            conversation = conversations.first()
        else:
            conversation = Conversation.objects.create()
            conversation.users.add(request.user)
            conversation.users.add(target_user)

        return CustomResponse(
            data={"conversation_id": conversation.id},
            status=200,
            message="Conversation started successfully."
        )
