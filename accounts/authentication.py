from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticates API requests using JSON Web Tokens.

    The authentication class first checks whether the request contains
    a regular Authorization header. If a header is present, the standard
    Simple JWT authentication process is used.

    If no Authorization header exists, the access token is read from the
    configured HTTP-only cookie. This allows the frontend to authenticate
    requests without storing JWT tokens in JavaScript-accessible storage.
    """

    def authenticate(self, request):
        """
        Authenticate the request using a header token or cookie token.

        The Authorization header takes priority. When it exists, token
        extraction and validation are delegated to the parent
        `JWTAuthentication` class.

        If no header is supplied, the method reads the access token from
        the cookie defined by `ACCESS_TOKEN_COOKIE_NAME`. A valid token is
        converted into an authenticated user and returned together with
        the validated token.

        Args:
            request: The incoming Django REST Framework request.

        Returns:
            tuple: The authenticated user and validated JWT token.
            None: If neither an Authorization header nor an access-token
            cookie is available.

        Raises:
            AuthenticationFailed: If a supplied JWT token is invalid,
            malformed, or expired.
        """
        header = self.get_header(request)

        if header is not None:
            return super().authenticate(request)

        raw_token = request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME)

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token