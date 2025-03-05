from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from accounts.models import UserProfile
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer
from core.responses import CustomResponse
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model


User = get_user_model()

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            user_data = UserSerializer(user, context={'request': request}).data

            return CustomResponse(data={
                "access": access_token,
                "refresh": str(refresh),
                "user_data":user_data
            }, status=status.HTTP_201_CREATED,message="User registered successfully")

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

        if not check_password(password, user.password):
            return CustomResponse(
                data={"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Serialize user data
        user_data = UserSerializer(user, context={"request": request}).data

        return CustomResponse(
            data={
                "access": access_token,
                "refresh": str(refresh),
                "user_data": user_data,
            },
            status=status.HTTP_200_OK,
            message="Login successful",
        )
