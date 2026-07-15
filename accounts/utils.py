from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


def get_cookie_settings():
    """
    Return the shared security configuration for authentication cookies.

    The values are read from the Django settings so that access-token and
    refresh-token cookies use the same HttpOnly, Secure, and SameSite
    configuration throughout the authentication flow.

    Returns:
        dict: Cookie options that can be passed directly to Django's
            `set_cookie()` method.
    """
    return {
        "httponly": settings.AUTH_COOKIE_HTTP_ONLY,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
    }


def set_auth_cookies(response, access_token, refresh_token):
    """
    Add access-token and refresh-token cookies to an HTTP response.

    This helper is used after a successful login. Both JWT values are stored
    under the cookie names configured in the Django settings. The shared
    security options are provided by `get_cookie_settings()`.

    Args:
        response: The Django REST Framework response that receives the
            authentication cookies.
        access_token: The serialized JWT access token.
        refresh_token: The serialized JWT refresh token.

    Returns:
        None: The supplied response object is modified directly.
    """
    cookie_settings = get_cookie_settings()

    response.set_cookie(
        settings.ACCESS_TOKEN_COOKIE_NAME,
        access_token,
        **cookie_settings,
    )
    response.set_cookie(
        settings.REFRESH_TOKEN_COOKIE_NAME,
        refresh_token,
        **cookie_settings,
    )


def set_access_cookie(response, access_token):
    """
    Add a newly generated access-token cookie to an HTTP response.

    This function is used during token refresh. It replaces only the access
    token while leaving the existing refresh-token cookie unchanged.

    Args:
        response: The Django REST Framework response that receives the new
            access-token cookie.
        access_token: The serialized JWT access token.

    Returns:
        None: The supplied response object is modified directly.
    """
    response.set_cookie(
        settings.ACCESS_TOKEN_COOKIE_NAME,
        access_token,
        **get_cookie_settings(),
    )


def delete_auth_cookies(response):
    """
    Remove the access-token and refresh-token cookies from the browser.

    Django adds expired cookie values to the response so that the browser
    deletes the authentication cookies. This helper is used during logout.

    Args:
        response: The Django REST Framework response from which the
            authentication cookies should be removed.

    Returns:
        None: The supplied response object is modified directly.
    """
    response.delete_cookie(settings.ACCESS_TOKEN_COOKIE_NAME)
    response.delete_cookie(settings.REFRESH_TOKEN_COOKIE_NAME)


def get_refresh_token_from_cookie(request):
    """
    Read the refresh token from the incoming request cookies.

    The cookie name is taken from the Django settings instead of being
    hard-coded inside the authentication views.

    Args:
        request: The incoming Django REST Framework request.

    Returns:
        str | None: The serialized refresh token when its cookie exists,
            otherwise `None`.
    """
    return request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)


def blacklist_refresh_token(refresh_token):
    """
    Invalidate a refresh token using Simple JWT's blacklist system.

    The serialized token is converted into a `RefreshToken` instance and
    added to the blacklist. `TokenError` is ignored because the supplied
    token may already be expired, malformed, or blacklisted.

    Ignoring this exception makes logout idempotent. Repeated logout requests
    can therefore complete without causing an internal server error.

    Args:
        refresh_token: The serialized JWT refresh token that should become
            invalid.

    Returns:
        None.
    """
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError:
        pass


def get_user_data(user):
    """
    Build the public user representation returned by authentication APIs.

    Only the account fields required by the frontend are included. Sensitive
    information such as the password hash, permissions, and internal account
    attributes is deliberately excluded.

    Args:
        user: The authenticated Django user instance.

    Returns:
        dict: The user's ID, username, and email address.
    """
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }