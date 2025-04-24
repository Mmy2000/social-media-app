from django.urls import path
from .views import ActiveAccountView, ForgotPasswordView, RegisterView, LoginView, ChangePasswordView, ResendCodeView, ResetPasswordView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("activate/", ActiveAccountView.as_view(), name="activate_user"),
    path("change_password/", ChangePasswordView.as_view(), name="change_password"),
    path("forget-password/", ForgotPasswordView.as_view(), name="forget_password"),
    path("reset_password/", ResetPasswordView.as_view(), name="reset_password"),
    path("resend_code/", ResendCodeView.as_view(), name="resend_code"),
]
