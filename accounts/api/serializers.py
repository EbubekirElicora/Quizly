from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    """
    Validate registration data and create a new user account.

    The serializer checks whether both password fields match and whether
    the submitted username or email address is already registered.

    After successful validation, Django's `create_user()` method creates
    the account and stores the password as a secure hash.
    """

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirmed_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Validate passwords and ensure that account data is unique.

        The method compares the password and confirmation password.
        It also queries Django's user model to prevent duplicate email
        addresses and usernames.

        Args:
            attrs: Registration data that has already passed individual
                field validation.

        Returns:
            dict: The validated registration data.

        Raises:
            serializers.ValidationError: If the passwords do not match,
                the email address is already used, or the username already
                exists.
        """
        if attrs["password"] != attrs["confirmed_password"]:
            raise serializers.ValidationError("Passwords do not match.")

        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError("Email is already used.")

        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError("Username is already used.")

        return attrs

    def create(self, validated_data):
        """
        Create and return a new Django user.

        The confirmation password is removed because it is required only
        during validation. The remaining data is passed to Django's
        `create_user()` method, which hashes the password before saving it.

        Args:
            validated_data: Successfully validated registration data.

        Returns:
            User: The newly created Django user instance.
        """
        validated_data.pop("confirmed_password")
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Validate login credentials and provide the authenticated user.

    Django's authentication system checks the submitted username and
    password. After successful authentication, the user instance is added
    to the validated data for use by the login view.
    """

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Authenticate the submitted username and password.

        The credentials are passed to Django's `authenticate()` function.
        When authentication succeeds, the returned user is stored under
        the `user` key in the validated data.

        Args:
            attrs: Login data that has already passed individual field
                validation.

        Returns:
            dict: The validated login data including the authenticated user.

        Raises:
            serializers.ValidationError: If the username and password do
                not belong to a valid user account.
        """
        user = authenticate(
            username=attrs["username"],
            password=attrs["password"],
        )

        if user is None:
            raise serializers.ValidationError("Invalid login credentials.")

        attrs["user"] = user
        return attrs