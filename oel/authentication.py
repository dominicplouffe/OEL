# your_app/authentication.py

from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from datetime import timedelta


class ExpiringTokenAuthentication(TokenAuthentication):
    """
    Overrides DRF TokenAuthentication to expire tokens after 1 day.
    """

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        if timezone.now() - token.created > timedelta(days=1):
            token.delete()  # remove old token
            raise AuthenticationFailed("Token has expired")
        return (user, token)
