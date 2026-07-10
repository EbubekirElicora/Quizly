from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def get_cookie_settings():
    """Returns shared settings for authentication cookies."""

    return {
        "httponly": settings.AUTH_COOKIE_HTTP_ONLY,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
    }


def set_auth_cookies(response, access_token, refresh_token):
    """Adds access and refresh JWT cookies to a response."""

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
    """Adds only the access JWT cookie to a response."""

    response.set_cookie(
        settings.ACCESS_TOKEN_COOKIE_NAME,
        access_token,
        **get_cookie_settings(),
    )


def delete_auth_cookies(response):
    """Removes authentication cookies from the browser."""

    response.delete_cookie(settings.ACCESS_TOKEN_COOKIE_NAME)
    response.delete_cookie(settings.REFRESH_TOKEN_COOKIE_NAME)


def get_refresh_token_from_cookie(request):
    """Returns the refresh token from cookies."""

    return request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)


def blacklist_refresh_token(refresh_token):
    """Blacklists a refresh token if token blacklist is enabled."""

    token = RefreshToken(refresh_token)
    token.blacklist()


def get_user_data(user):
    """Returns public user data for API responses."""

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }