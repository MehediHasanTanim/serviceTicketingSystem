import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from infrastructure.db.core.models import (
    AuthToken,
    Organization,
    PasswordResetToken,
    RefreshToken,
    User,
    UserCredential,
    UserRole,
)
from interfaces.api.authentication import BearerTokenAuthentication
from interfaces.api.serializers import (
    SignupSerializer,
    LoginSerializer,
    RefreshSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)


TOKEN_TTL_DAYS = 7
REFRESH_TTL_DAYS = 30
RESET_TOKEN_TTL_MINUTES = 30


def _new_token_key():
    return secrets.token_hex(32)


def _create_auth_token(user):
    expires_at = timezone.now() + timedelta(days=TOKEN_TTL_DAYS)
    return AuthToken.objects.create(key=_new_token_key(), user=user, expires_at=expires_at)

def _create_refresh_token(user):
    expires_at = timezone.now() + timedelta(days=REFRESH_TTL_DAYS)
    return RefreshToken.objects.create(key=_new_token_key(), user=user, expires_at=expires_at)


@extend_schema(request=SignupSerializer)
class SignupView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        org = Organization.objects.filter(id=data["org_id"]).first()
        if not org:
            return Response({"detail": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

        if not request.user or not request.user.is_authenticated:
            return Response({"detail": "Admin credentials required"}, status=status.HTTP_403_FORBIDDEN)

        is_admin = UserRole.objects.filter(
            user=request.user,
            role__org=org,
            role__name__iexact="admin",
        ).exists()
        if not is_admin:
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)

        if User.objects.filter(org=org, email__iexact=data["email"]).exists():
            return Response({"detail": "User already exists"}, status=status.HTTP_409_CONFLICT)

        with transaction.atomic():
            user = User.objects.create(
                org=org,
                email=data["email"],
                phone=data.get("phone", ""),
                display_name=data["display_name"],
                status="active",
            )
            UserCredential.objects.create(
                user=user,
                password_hash=make_password(data["password"]),
                last_password_change_at=timezone.now(),
            )
            token = _create_auth_token(user)
            refresh = _create_refresh_token(user)

        return Response(
            {
                "user_id": user.id,
                "token": token.key,
                "expires_at": token.expires_at,
                "refresh_token": refresh.key,
                "refresh_expires_at": refresh.expires_at,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(request=LoginSerializer)
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.filter(org_id=data["org_id"], email__iexact=data["email"]).first()
        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        credential = getattr(user, "credential", None)
        if not credential or not check_password(data["password"], credential.password_hash):
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        token = _create_auth_token(user)
        refresh = _create_refresh_token(user)
        return Response(
            {
                "token": token.key,
                "expires_at": token.expires_at,
                "refresh_token": refresh.key,
                "refresh_expires_at": refresh.expires_at,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(request=None)
class LogoutView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def post(self, request):
        token = request.auth
        if token:
            token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=None)
@extend_schema(request=RefreshSerializer)
class RefreshView(APIView):
    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_key = serializer.validated_data["refresh_token"]

        refresh = (
            RefreshToken.objects.select_related("user")
            .filter(key=refresh_key, revoked_at__isnull=True, expires_at__gt=timezone.now())
            .first()
        )
        if not refresh:
            return Response({"detail": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh.revoked_at = timezone.now()
        refresh.save(update_fields=["revoked_at"])

        token = _create_auth_token(refresh.user)
        new_refresh = _create_refresh_token(refresh.user)
        return Response(
            {
                "token": token.key,
                "expires_at": token.expires_at,
                "refresh_token": new_refresh.key,
                "refresh_expires_at": new_refresh.expires_at,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(request=ForgotPasswordSerializer)
class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.filter(org_id=data["org_id"], email__iexact=data["email"]).first()
        if not user:
            return Response(status=status.HTTP_204_NO_CONTENT)

        token = PasswordResetToken.objects.create(
            user=user,
            token=_new_token_key(),
            expires_at=timezone.now() + timedelta(minutes=RESET_TOKEN_TTL_MINUTES),
        )

        return Response(
            {
                "reset_token": token.token,
                "expires_at": token.expires_at,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(request=ResetPasswordSerializer)
class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        token = (
            PasswordResetToken.objects.select_related("user")
            .filter(token=data["token"], used_at__isnull=True, expires_at__gt=timezone.now())
            .first()
        )
        if not token:
            return Response({"detail": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        credential, _ = UserCredential.objects.get_or_create(user=token.user)
        credential.password_hash = make_password(data["new_password"])
        credential.last_password_change_at = timezone.now()
        credential.save()

        token.used_at = timezone.now()
        token.save(update_fields=["used_at"])

        return Response(status=status.HTTP_204_NO_CONTENT)
