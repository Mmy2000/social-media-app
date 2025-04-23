import random
from rest_framework import status
from rest_framework.views import APIView
from accounts.models import UserProfile
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import  RegisterSerializer, UserSerializer, UserOtpSerializer, ActiveAccountSerializer
from core.responses import CustomResponse
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMessage
from rest_framework import status, generics
from django.utils.translation import gettext as _

User = get_user_model()

class SendOTPEmailMixin:
    def send_otp(self, email):
        otp = random.randint(1000, 9999)

        self.send_message(email, f'Your OTP code is {otp}', 'Your OTP Code')
        return otp

    def send_message(self, email, message, subject):
        email = EmailMessage(subject, message, from_email=settings.EMAIL_HOST_USER, to=[email])
        try:
            email.send()
        except Exception as e:
            # This because sending mail from pc issues
            pass


class RegisterView(SendOTPEmailMixin, generics.CreateAPIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            user_data = UserSerializer(user, context={'request': request}).data
            otp = self.send_otp(user.email)
            user.otp = otp
            user.save()

            return CustomResponse(data={
                "access": access_token,
                "refresh": str(refresh),
                "user_data": user_data
            }, status=status.HTTP_201_CREATED, message="User registered successfully. Check your email for OTP.")

        return CustomResponse(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserOtpView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserOtpSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data["email"]
            try:
                user = User.objects.get(email=email)
                return CustomResponse(
                    {"otp": user.otp},
                    status=status.HTTP_200_OK,
                    message=_("OTP sent successfully."),
                )
            except User.DoesNotExist:
                return CustomResponse(
                    {
                        "error": _(
                            "The email address you entered does not exist. Please check the email or register a new account."
                        )
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
        return CustomResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActiveAccountView(SendOTPEmailMixin,APIView):
    def post(self, request):
        serializer = ActiveAccountSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            otp = serializer.validated_data.get("otp")

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return CustomResponse(data={"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            if user.otp == otp:
                user.is_active = True
                user.otp = None
                user.save()
                self.send_message(email, "account activated successfully", "account activated successfully")
                return CustomResponse(data=user.otp, status=status.HTTP_200_OK,message="Account activated successfully")

            return CustomResponse(data={"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        return CustomResponse(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        email_or_username = request.data.get("email_or_username")
        password = request.data.get("password")

        if not email_or_username or not password:
            return CustomResponse(
                data={"error": "Email/Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Check if the input is an email or username
            if "@" in email_or_username:
                user = User.objects.get(email=email_or_username)
            else:
                user = User.objects.get(username=email_or_username)
        except User.DoesNotExist:
            return CustomResponse(
                data={"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return CustomResponse(
                data={"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Tokens & data
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        user_data = UserSerializer(user, context={"request": request}).data

        if not user.is_active:
            return CustomResponse(
                data={
                    "access": access_token,
                    "refresh": str(refresh),
                    "user_data": user_data,
                },
                status=status.HTTP_403_FORBIDDEN,
                message="Account not active. Please verify OTP.",
            )

        return CustomResponse(
            data={
                "access": access_token,
                "refresh": str(refresh),
                "user_data": user_data,
            },
            status=status.HTTP_200_OK,
            message="Login successful",
        )
