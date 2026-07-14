from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.utils import (
    blacklist_refresh_token,
    delete_auth_cookies,
    get_refresh_token_from_cookie,
    get_user_data,
    set_access_cookie,
    set_auth_cookies,
)
from .serializers import LoginSerializer, RegisterSerializer

class RegisterView(APIView):
    """Creates a new user account."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "User created successfully!"},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Logs in a user and sets JWT cookies."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid login credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        response = Response(
            {
                "detail": "Login successful.",
                "user": get_user_data(user),
            },
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, str(refresh.access_token), str(refresh))
        return response


class LogoutView(APIView):
    """Logs out a user and deletes authentication cookies."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = get_refresh_token_from_cookie(request)
        response = Response(
            {
                "detail": (
                    "Logout successful. All tokens have been deleted. "
                    "The refresh token is now invalid."
                )
            },
            status=status.HTTP_200_OK,
        )

        if refresh_token:
            blacklist_refresh_token(refresh_token)

        delete_auth_cookies(response)
        return response


class TokenRefreshView(APIView):
    """Refreshes the access token using the refresh cookie."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_token = get_refresh_token_from_cookie(request)

        if not refresh_token:
            return Response(
                {"detail": "Refresh token missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken(refresh_token)
        response = Response(
            {"detail": "Token refreshed"},
            status=status.HTTP_200_OK,
        )
        set_access_cookie(response, str(refresh.access_token))
        return response