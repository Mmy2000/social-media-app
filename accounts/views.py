from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from accounts.models import UserProfile
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer
from core.responses import CustomResponse
from django.contrib.auth import authenticate


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
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return CustomResponse(data={"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=email, password=password)

        if user is None:
            return CustomResponse(data={"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Serialize user data
        user_data = UserSerializer(user, context={'request': request}).data

        return CustomResponse(data={
            "access": access_token,
            "refresh": str(refresh),
            "user_data": user_data
        }, status=status.HTTP_200_OK,message="Login successful")