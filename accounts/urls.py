from django.urls import path
from .views import (
    ActiveAccountView,
    ForgotPasswordView,
    RegisterView,
    LoginView,
    ChangePasswordView,
    ResendCodeView,
    ResetPasswordView,
    LogoutView,
    SocialLoginView,
    ProfileView,
    ProfileUpdateView,
    SendFriendRequestView,
    UnfriendView,
    UpdateFriendRequestView
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("activate/", ActiveAccountView.as_view(), name="activate_user"),
    path("change_password/", ChangePasswordView.as_view(), name="change_password"),
    path("forget-password/", ForgotPasswordView.as_view(), name="forget_password"),
    path("reset_password/", ResetPasswordView.as_view(), name="reset_password"),
    path("resend_code/", ResendCodeView.as_view(), name="resend_code"),
    path("social_login/", SocialLoginView.as_view(), name="social_login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/<int:user_id>/", ProfileView.as_view(), name="profile"),
    path("update_profile/", ProfileUpdateView.as_view(), name="update_profile"),
    path('friend-request/send/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('friend-request/<int:pk>/update/', UpdateFriendRequestView.as_view(), name='update-friend-request'),
    path("friends/remove/<int:friend_id>/", UnfriendView.as_view(), name="unfriend"),
]
