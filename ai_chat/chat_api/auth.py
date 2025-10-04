from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .models import AuthToken

class TokenHeaderAuthentication(BaseAuthentication):
    """
    Looks for:
      - Header: Authorization: Token <key>
      - OR Header: X-Auth-Token: <key>
    Sets request.user when valid.
    """
    keyword = "Token"

    def authenticate(self, request):
        auth = request.headers.get("Authorization", "")
        xheader = request.headers.get("X-Auth-Token")

        token_key = None
        if auth and auth.startswith(self.keyword + " "):
            token_key = auth.split(" ", 1)[1].strip()
        elif xheader:
            token_key = xheader.strip()

        if not token_key:
            return None  # no credentials provided

        try:
            token = AuthToken.objects.select_related("user").get(key=token_key)
        except AuthToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid or expired token.")

        return (token.user, None)
