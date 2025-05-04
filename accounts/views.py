import random
from rest_framework import status
from rest_framework.views import APIView
from accounts.models import FriendshipRequest, UserProfile
from rest_framework_simplejwt.tokens import RefreshToken

from posts.models import Post, PostAttachment
from posts.serializers import PostAttachmentSerializer, PostSerializer
from .serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    FriendSerializer,
    FriendshipRequestSerializer,
    FriendshipRequestSerializerSample,
    FriendshipRequestUpdateSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserProfileUpdate,
    UserSerializer,
    ActiveAccountSerializer,
    SocialLoginSerializer,
)
from core.responses import CustomResponse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import EmailMessage
from rest_framework import status, generics
from django.utils.translation import gettext as _
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

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

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data["current_password"]):
                return CustomResponse(
                    data={},
                    status=status.HTTP_400_BAD_REQUEST,
                    message="Current password is incorrect",
                )

            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return CustomResponse(
                data={},
                status=status.HTTP_200_OK,
                message="Password changed successfully",
            )
        return CustomResponse(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
            message="Password change failed",
        )


class ForgotPasswordView(SendOTPEmailMixin, generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data["email"]
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return CustomResponse(
                    data={},
                    message=_("User with this email does not exist."),
                    status=status.HTTP_404_NOT_FOUND,
                )

            otp = random.randint(1000, 9999)
            user.otp = otp
            user.save()

            subject = "Password Reset Request"
            message = f"Hello, use this code to reset your password {otp} ."
            self.send_message(email, message, subject)
            return CustomResponse(
                data={},
                message=_("Password reset email has been sent."),
                status=status.HTTP_200_OK,
            )
        return CustomResponse(
            data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

class ResetPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data['email']
            password = serializer.validated_data['new_password']
            if User.objects.filter(email=email):
                user = User.objects.get(email=email)
                if user.check_password(password):
                    return CustomResponse(data={}, message="not allowed one of your past passwords",
                                          status=status.HTTP_400_BAD_REQUEST)

                user.set_password(password)
                user.otp = None
                user.save()
                return CustomResponse(data={}, message="password changed successfully", status=status.HTTP_200_OK)
            else:
                return CustomResponse(data={}, message="user not found", status=status.HTTP_400_BAD_REQUEST)


class ResendCodeView(generics.GenericAPIView, SendOTPEmailMixin):
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data["email"]
            otp = self.send_otp(email)
            user = User.objects.get(email=email)
            user.otp = otp
            user.save()
            return CustomResponse(
                data={},
                message=_("code has been sent successfully"),
                status=status.HTTP_200_OK,
            )


class SocialLoginView(generics.GenericAPIView, SendOTPEmailMixin):

    def post(self, request, *args, **kwargs):
        serializer = SocialLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user, created, tokens = serializer.create_or_get_user(
                serializer.validated_data
            )
            if created:
                # New user registered
                user.otp = random.randint(1000, 9999)
                user.save()
                self.send_message(user.email, f'Your OTP code is {user.otp}', 'Your OTP Code')
                return CustomResponse(data={
                    "access": tokens["access"],
                    "refresh": tokens["refresh"],
                    "user_data": UserSerializer(user, context={"request": request}).data,
                }, status=status.HTTP_201_CREATED, message="User registered successfully. Check your email for OTP.")
            else:
                # Existing user logged in
                if not user.is_active:
                    return CustomResponse(data={
                    "access": tokens["access"],
                    "refresh": tokens["refresh"],
                    "user_data": UserSerializer(user, context={"request": request}).data,
                }, status=status.HTTP_403_FORBIDDEN, message="Account not active. Please verify OTP.")
                return CustomResponse(data={
                    "access": tokens["access"],
                    "refresh": tokens["refresh"],
                    "user_data": UserSerializer(user, context={"request": request}).data,
                }, status=status.HTTP_200_OK, message="Login successful")

        return CustomResponse(
            data=serializer.errors, status=status.HTTP_400_BAD_REQUEST, message="Invalid data"
        )


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return CustomResponse(data={}, message=_("logged out successfully"), status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return CustomResponse(data={}, message=str(e), status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]  # Allow both anonymous and authenticated users

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = self.serializer_class(user, partial=True, context={"request": request})

        # Safely determine if the authenticated user is the profile owner
        is_owner = False
        is_friend = False  # <--- initialize

        if request.user.is_authenticated:
            if request.user.id == user_id:
                is_owner = True
                posts = Post.objects.filter(created_by=user).order_by("-created_at")
            else:
                posts = Post.objects.filter(created_by=user, role="public").order_by("-created_at")
                # Check if authenticated user is a friend of the target user
                is_friend = user.friends.filter(id=request.user.id).exists()
        else:
            posts = Post.objects.filter(created_by=user, role="public").order_by("-created_at")

        photos = PostAttachment.objects.filter(post__in=posts, image__isnull=False).order_by("-created_at")

        posts = PostSerializer(posts, many=True, context={"request": request}).data
        followers_count = 1
        friends_qs = user.friends.all()
        friends_data = FriendSerializer(friends_qs, many=True, context={"request": request}).data
        friends = {"count": friends_qs.count(), "users": friends_data}
        followers = {
            "count":followers_count,
            "follwers_data": {}
        }
        photos = PostAttachmentSerializer(photos, many=True, context={"request": request}).data

        return CustomResponse(
            data={
                "user_data": serializer.data,
                "posts": posts,
                "followers": followers,
                "friends": friends,
                "photos": photos,
                "is_owner": is_owner,
                "is_friend": is_friend,  # <--- include in response
            },
            message=_("User profile retrieved successfully"),
            status=status.HTTP_200_OK,
        )


class ProfileUpdateView(APIView):
    serializer_class = UserProfileUpdate
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        try:
            profile = user.userprofile  # make sure every user has a UserProfile instance
        except UserProfile.DoesNotExist:
            return CustomResponse(message=_("User profile not found"), status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(profile, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(
                data=serializer.data,
                message=_("User profile updated successfully"),
                status=status.HTTP_200_OK
            )
        return CustomResponse(
            data=serializer.errors,
            message=_("Failed to update profile"),
            status=status.HTTP_400_BAD_REQUEST
        )


class SendFriendRequestView(generics.CreateAPIView):
    serializer_class = FriendshipRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return CustomResponse(
                data=serializer.data,
                message="Friend request sent successfully.",
                status=status.HTTP_201_CREATED,
            )
        return CustomResponse(
            data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

class UpdateFriendRequestView(generics.UpdateAPIView):
    queryset = FriendshipRequest.objects.all()
    serializer_class = FriendshipRequestUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        if obj.created_for != self.request.user:
            raise PermissionDenied("You are not allowed to modify this request.")
        return obj

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.status in ["accepted", "rejected"]:
            return CustomResponse(
                data={},
                message="This friend request has already been processed.",
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return CustomResponse(
                data=serializer.data,
                message="Friend request updated successfully.",
                status=status.HTTP_200_OK
            )
        return CustomResponse(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UnfriendView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, friend_id):
        user = request.user

        try:
            friend = User.objects.get(id=friend_id)
            print(friend)
        except User.DoesNotExist:
            return CustomResponse(message="User not found.", status=status.HTTP_404_NOT_FOUND)

        if friend in user.friends.all():
            user.friends.remove(friend)
            friend.friends.remove(user)  # Mutual removal

            # Optional: update friends_count if you're manually tracking it
            user.friends_count = user.friends.count()
            friend.friends_count = friend.friends.count()
            user.save()
            friend.save()

            return CustomResponse(
                message="Friend removed successfully.",
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return CustomResponse(
                message="You are not friends with this user.",
                status=status.HTTP_400_BAD_REQUEST
            )

class FriendsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        friends = user.friends.all()
        serializer = FriendSerializer(friends, many=True,context={'request': request})
        return CustomResponse(
            data=serializer.data,
            message="Friend retrieved successfully.",
            status=status.HTTP_200_OK,
        )

class FriendRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        requests = FriendshipRequest.objects.filter(created_for=user,status="sent")
        serializer = FriendshipRequestSerializerSample(
            requests, many=True, context={"request": request}
        )

        return CustomResponse(
            data=serializer.data,
            message="Friend Requests retrieved successfully.",
            status=status.HTTP_200_OK,
        )
