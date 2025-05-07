from django.urls import path
from chat.views import ConversationDetailView, ConversationListView, StartConversationView

urlpatterns = [
    path('conversations/', ConversationListView.as_view(), name='conversations-list'),
    path('conversations/<int:pk>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/start/<int:user_id>/', StartConversationView.as_view(), name='conversation-start'),
]
