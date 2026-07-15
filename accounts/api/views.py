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
    """
    Register a new user account.

    The endpoint accepts registration data and validates it with
    `RegisterSerializer`. The serializer checks the submitted fields,
    verifies password confirmation, prevents duplicate usernames and email
    addresses, and creates the Django user account.

    Authentication is disabled for this view because registration must be
    available to users who do not yet have an account.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """
        Validate the request data and create a new user.

        The submitted registration data is passed to `RegisterSerializer`.
        When validation succeeds, the serializer creates the user account
        and the endpoint returns HTTP 201.

        Args:
            request: The incoming Django REST Framework request containing
                username, email, password, and password confirmation.

        Returns:
            Response: A success message with HTTP 201 when the account is
            created, or serializer validation errors with HTTP 400.
        """
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "User created successfully!"},
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(APIView):
    """
    Authenticate a user and create JWT authentication cookies.

    The submitted credentials are validated by `LoginSerializer`. After
    successful authentication, Simple JWT creates a refresh token and its
    corresponding access token.

    Both tokens are stored in HTTP-only cookies through
    `set_auth_cookies()`. Public user information is prepared by
    `get_user_data()` and included in the response.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """
        Validate login credentials and return an authenticated response.

        The serializer uses Django's authentication system to verify the
        username and password. Valid credentials produce new access and
        refresh tokens for the authenticated user.

        Args:
            request: The incoming Django REST Framework request containing
                the username and password.

        Returns:
            Response: User information and authentication cookies with
            HTTP 200, or an error message with HTTP 400 when authentication
            fails.
        """
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

        set_auth_cookies(
            response,
            str(refresh.access_token),
            str(refresh),
        )

        return response


class LogoutView(APIView):
    """
    Log out an authenticated user.

    The endpoint reads the refresh token from the configured cookie and
    passes it to `blacklist_refresh_token()` so that it cannot be used
    again.

    The access and refresh cookies are then removed from the browser through
    `delete_auth_cookies()`. Authentication is required because logout is
    only available to signed-in users.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Blacklist the refresh token and remove authentication cookies.

        A missing refresh-token cookie does not prevent logout. The response
        still removes both authentication cookies so that the browser no
        longer sends them with later requests.

        Args:
            request: The authenticated Django REST Framework request.

        Returns:
            Response: A logout confirmation with HTTP 200 and expired
            authentication cookies.
        """
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
    """
    Create a new access token from the refresh-token cookie.

    The endpoint reads the refresh token with
    `get_refresh_token_from_cookie()`. Simple JWT validates the token and
    creates a new access token.

    Only the access-token cookie is replaced through `set_access_cookie()`;
    the existing refresh-token cookie remains unchanged.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """
        Refresh the access token stored in the authentication cookie.

        Args:
            request: The incoming Django REST Framework request containing
                the refresh-token cookie.

        Returns:
            Response: A refreshed access-token cookie with HTTP 200, or
            HTTP 401 when the refresh-token cookie is missing.
        """
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