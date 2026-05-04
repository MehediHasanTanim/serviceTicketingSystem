from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings

from infrastructure.db.core.models import User


class BearerTokenAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get(api_settings.USER_ID_CLAIM)
        if not user_id:
            raise AuthenticationFailed("Invalid token")
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise AuthenticationFailed("User not found")
        return user
