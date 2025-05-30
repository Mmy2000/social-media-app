from rest_framework import serializers
from .models import User, UserProfile, FriendshipRequest
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone


class SampleUserData(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username"]
        extra_kwargs = {
            "username": {"validators": []}  # disable default uniqueness validator
        }

    def validate_username(self, value):
        user = self.context["request"].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value


class UserProfileUpdate(serializers.ModelSerializer):
    user = SampleUserData()

    class Meta:
        model = UserProfile
        fields = [
            "profile_picture",
            "cover_picture",
            "country",
            "city",
            "phone_number",
            "bio",
            "gender",
            "date_of_birth",
            "age",
            "is_adult",
            "marital_status",
            "work",
            "education",
            "user",
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    cover_picture = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "full_name",
            "full_address",
            "country",
            "city",
            "phone_number",
            "gender",
            "date_of_birth",
            "age",
            "is_adult",
            "marital_status",
            "bio",
            "profile_picture",
            "cover_picture",
            "work",
            "education",
        ]

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        url = obj.get_profile_picture
        return request.build_absolute_uri(url) if request else url

    def get_cover_picture(self, obj):
        request = self.context.get("request")
        url = obj.get_cover_picture
        return request.build_absolute_uri(url) if request else url


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source="userprofile", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "username",
            "source",
            "is_active",
            "profile",
            "date_joined",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password", "password2"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")  # Remove password2 from data
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


class SocialLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(
        required=False, allow_blank=True
    )  # Optional for login
    first_name = serializers.CharField(
        required=False, allow_blank=True
    )  # Optional for login
    last_name = serializers.CharField(
        required=False, allow_blank=True
    )  # Optional for login
    profile_image = serializers.ImageField(
        required=False, allow_null=True
    )  # Optional for login
    source = serializers.CharField(
        required=False, allow_blank=True
    )  # Optional for login

    def create_or_get_user(self, validated_data):
        email = validated_data.get("email")
        username = validated_data.get("username", email.split("@")[0])
        first_name = validated_data.get("first_name", "")
        last_name = validated_data.get("last_name", "")
        source = validated_data.get("source", "local")
        image = validated_data.get("profile_image", None)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "source": source,
            },
        )
        if created and image:
            user.userprofile.profile_picture = image
            user.userprofile.save()

        refresh = RefreshToken.for_user(user)
        tokens = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        return user, created, tokens


class FriendshipRequestSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = FriendshipRequest
        fields = ["id", "created_by", "created_for", "status"]
        read_only_fields = ["status"]

    def validate(self, attrs):
        created_by = self.context["request"].user
        created_for = attrs.get("created_for")

        if created_by == created_for:
            raise serializers.ValidationError(
                "You cannot send a friend request to yourself."
            )

        if created_for in created_by.friends.all():
            raise serializers.ValidationError("You are already friends with this user.")

        if FriendshipRequest.objects.filter(
            created_by=created_by,
            created_for=created_for,
            status=FriendshipRequest.SENT,
        ).exists():
            raise serializers.ValidationError("Friend request already sent.")

        return attrs


class FriendshipRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendshipRequest
        fields = ["status"]

    def validate_status(self, value):
        if value not in [FriendshipRequest.ACCEPTED, FriendshipRequest.REJECTED]:
            raise serializers.ValidationError("Invalid status update.")
        return value

    def update(self, instance, validated_data):
        new_status = validated_data["status"]
        if new_status == FriendshipRequest.ACCEPTED:
            # Add each user to the other's friend list
            instance.created_by.friends.add(instance.created_for)
            instance.created_for.friends.add(instance.created_by)

            # Update friend counts
            instance.created_by.friends_count = instance.created_by.friends.count()
            instance.created_for.friends_count = instance.created_for.friends.count()
            instance.created_by.save()
            instance.created_for.save()

        instance.status = new_status
        instance.save()
        return instance


class ProfileFriends(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "full_name",
            "profile_picture",
        ]

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        url = obj.get_profile_picture
        return request.build_absolute_uri(url) if request else url


class FriendSerializer(serializers.ModelSerializer):
    profile = ProfileFriends(source="userprofile", read_only=True)
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "profile", "is_online"]

    def get_is_online(self, obj):
        try:
            now = timezone.now()
            return (
                now - obj.userprofile.last_active
            ).total_seconds() < 300  # 5 minutes
        except:
            return False


class FriendshipRequestSerializerSample(serializers.ModelSerializer):
    created_by = FriendSerializer()
    created_for = FriendSerializer()
    mutual_friends = serializers.SerializerMethodField()
    mutual_friends_count = serializers.SerializerMethodField()

    class Meta:
        model = FriendshipRequest
        fields = [
            "id",
            "created_by",
            "created_for",
            "status",
            "mutual_friends",
            "mutual_friends_count",
        ]

    def get_mutual_friends(self, obj):
        request_user = obj.created_for
        requester = obj.created_by
        mutuals = request_user.friends.filter(
            id__in=requester.friends.values_list("id", flat=True)
        )
        return FriendSerializer(mutuals, many=True, context=self.context).data

    def get_mutual_friends_count(self, obj):
        request_user = obj.created_for
        requester = obj.created_by
        return request_user.friends.filter(
            id__in=requester.friends.values_list("id", flat=True)
        ).count()


class FriendSuggestionsSerializer(serializers.ModelSerializer):
    profile = ProfileFriends(source="userprofile", read_only=True)
    mutual_friends = serializers.SerializerMethodField()
    mutual_friends_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "profile",
            "mutual_friends",
            "mutual_friends_count",
        ]

    def get_mutual_friends(self, obj):
        request = self.context.get("request")
        current_user = request.user
        current_user_friends = set(current_user.friends.all())
        suggested_user_friends = set(obj.friends.all())
        mutual = current_user_friends.intersection(suggested_user_friends)

        return [
            {
                "id": friend.id,
                "username": friend.username,
                "full_name": friend.userprofile.full_name,
                "profile_picture": (
                    request.build_absolute_uri(friend.userprofile.get_profile_picture)
                    if hasattr(friend, "userprofile")
                    else None
                ),
            }
            for friend in mutual
        ]

    def get_mutual_friends_count(self, obj):
        current_user = self.context["request"].user
        current_user_friends = set(current_user.friends.all())
        suggested_user_friends = set(obj.friends.all())
        mutual = current_user_friends.intersection(suggested_user_friends)
        return len(mutual)
