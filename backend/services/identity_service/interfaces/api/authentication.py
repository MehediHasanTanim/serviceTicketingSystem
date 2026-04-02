from datetime import datetime, timezone
from rest_framework import authentication, exceptions
from infrastructure.db.core.models import AuthToken


class BearerTokenAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith(self.keyword + " "):
            return None

        token_key = auth_header[len(self.keyword) + 1 :].strip()
        if not token_key:
            return None

        now = datetime.now(timezone.utc)
        try:
            token = AuthToken.objects.select_related("user").get(key=token_key, expires_at__gt=now)
        except AuthToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid or expired token")

        return (token.user, token)
