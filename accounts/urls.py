from django.urls import path
from .views import ActiveAccountView, RegisterView, LoginView, UserOtpView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("userotp/", UserOtpView.as_view(), name="user_otp"),
    path("activate/", ActiveAccountView.as_view(), name="activate_user"),
]
