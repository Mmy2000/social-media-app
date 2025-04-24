from rest_framework import serializers
from .models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'cover_picture', 'country', 'city', 'phone_number','bio', 'gender', 'full_name', 'full_address']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source="userprofile", read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'username','is_active','profile']


class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'password2']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')  # Remove password2 from data
        user = User.objects.create_user(**validated_data)
        return user


class ActiveAccountSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=100)
    otp = serializers.CharField(max_length=100)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                "New password and confirm password do not match."
            )
        return data

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_otp(self, value):
        """Validate the OTP"""
        user = User.objects.get(email=self.initial_data["email"])
        print("User OTP:", user.otp)
        print("Provided OTP:", value)
        if user.otp != value:
            raise serializers.ValidationError("Invalid OTP")
        return value

    def save(self):
        email = self.validated_data["email"]
        new_password = self.validated_data["new_password"]

        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()

        # Clear OTP after successful reset
        user.otp = None
        user.save()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
