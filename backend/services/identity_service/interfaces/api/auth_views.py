import secrets
from datetime import timedelta

from django.db import transaction, models, IntegrityError
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from infrastructure.db.core.models import (
    AuthToken,
    InviteToken,
    Organization,
    PasswordResetToken,
    RefreshToken,
    Role,
    User,
    UserCredential,
    UserDepartment,
    UserRole,
)
from interfaces.api.authentication import BearerTokenAuthentication
from interfaces.api.serializers import (
    SignupSerializer,
    LoginSerializer,
    RefreshSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ActivateInviteSerializer,
    MeSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserResponseSerializer,
    RoleCreateSerializer,
    RoleUpdateSerializer,
    RoleResponseSerializer,
    OrganizationCreateSerializer,
    OrganizationUpdateSerializer,
    OrganizationResponseSerializer,
)


TOKEN_TTL_DAYS = 7
REFRESH_TTL_DAYS = 30
RESET_TOKEN_TTL_MINUTES = 30
INVITE_TOKEN_TTL_HOURS = getattr(settings, "INVITE_TOKEN_TTL_HOURS", 72)


def _new_token_key():
    return secrets.token_hex(32)


def _create_auth_token(user):
    expires_at = timezone.now() + timedelta(days=TOKEN_TTL_DAYS)
    return AuthToken.objects.create(key=_new_token_key(), user=user, expires_at=expires_at)

def _create_refresh_token(user):
    expires_at = timezone.now() + timedelta(days=REFRESH_TTL_DAYS)
    return RefreshToken.objects.create(key=_new_token_key(), user=user, expires_at=expires_at)


def _create_invite_token(user):
    expires_at = timezone.now() + timedelta(hours=INVITE_TOKEN_TTL_HOURS)
    return InviteToken.objects.create(token=_new_token_key(), user=user, expires_at=expires_at)


def _build_invite_link(token: str) -> str:
    base = getattr(settings, "FRONTEND_APP_URL", "http://localhost:5176").rstrip("/")
    return f"{base}/activate?token={token}"


def _send_invite_email(user, invite_token: InviteToken):
    if not settings.EMAIL_HOST:
        return
    subject = "You are invited to Service Ticketing"
    activation_link = _build_invite_link(invite_token.token)
    message = (
        f"Hello {user.display_name},\n\n"
        "You have been invited to Service Ticketing.\n"
        f"Activate your account here: {activation_link}\n\n"
        "If you did not expect this invitation, you can ignore this email."
    )
    html_message = f"""
        <div style="font-family: Arial, sans-serif; background: #f6f7fb; padding: 24px;">
          <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 14px; padding: 24px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);">
            <h2 style="margin: 0 0 12px; color: #1f2a44;">You're invited</h2>
            <p style="margin: 0 0 16px; color: #4b5563;">Hello {user.display_name},</p>
            <p style="margin: 0 0 20px; color: #4b5563;">You have been invited to Service Ticketing. Click below to activate your account.</p>
            <a href="{activation_link}" style="display: inline-block; padding: 12px 20px; background: #1d3aff; color: #ffffff; text-decoration: none; border-radius: 10px; font-weight: 600;">Activate Account</a>
            <p style="margin: 20px 0 0; color: #6b7280; font-size: 13px;">If you did not expect this invitation, you can ignore this email.</p>
          </div>
        </div>
    """
    send_mail(
        subject=subject,
        message=message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    invite_token.sent_at = timezone.now()
    invite_token.save(update_fields=["sent_at"])

def _require_admin(user, org_id: int):
    if not user:
        return False
    if hasattr(user, "is_authenticated") and not user.is_authenticated:
        return False
    return _is_admin(user, org_id)


def _get_normalized_roles(user, org_id: int):
    roles = (
        UserRole.objects.filter(user=user, role__org_id=org_id)
        .select_related("role")
        .values_list("role__name", flat=True)
    )
    return {name.lower().strip().replace("_", " ") for name in roles}


def _is_super_admin(user, org_id: int):
    return "super admin" in _get_normalized_roles(user, org_id)


def _is_admin(user, org_id: int):
    normalized = _get_normalized_roles(user, org_id)
    return "admin" in normalized or "super admin" in normalized


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
        RefreshToken.objects.filter(
            user=request.user,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).update(revoked_at=timezone.now())
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


@extend_schema(request=ActivateInviteSerializer)
class ActivateInviteView(APIView):
    def post(self, request):
        serializer = ActivateInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        invite = (
            InviteToken.objects.select_related("user")
            .filter(token=data["token"], used_at__isnull=True, expires_at__gt=timezone.now())
            .first()
        )
        if not invite:
            if InviteToken.objects.filter(token=data["token"], used_at__isnull=False).exists():
                return Response({"detail": "Invite token already used"}, status=status.HTTP_400_BAD_REQUEST)
            if InviteToken.objects.filter(token=data["token"], expires_at__lte=timezone.now()).exists():
                return Response({"detail": "Invite token expired"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": "Invalid invite token"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            credential, _ = UserCredential.objects.get_or_create(user=invite.user)
            credential.password_hash = make_password(data["password"])
            credential.last_password_change_at = timezone.now()
            credential.save()

            invite.user.status = "active"
            invite.user.save(update_fields=["status", "updated_at"])

            invite.used_at = timezone.now()
            invite.save(update_fields=["used_at"])

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=None, responses=MeSerializer)
class MeView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def get(self, request):
        user = request.user
        roles = list(
            UserRole.objects.filter(user=user)
            .select_related("role")
            .values_list("role__name", flat=True)
        )
        return Response(
            {
                "id": user.id,
                "org_id": user.org_id,
                "email": user.email,
                "display_name": user.display_name,
                "roles": roles,
                "is_admin": _is_admin(user, user.org_id),
                "is_super_admin": _is_super_admin(user, user.org_id),
            },
            status=status.HTTP_200_OK,
        )


class UserListCreateView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(request=UserCreateSerializer, responses=UserResponseSerializer)
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not _require_admin(request.user, data["org_id"]):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)

        if User.objects.filter(org_id=data["org_id"], email__iexact=data["email"]).exists():
            return Response({"detail": "User already exists"}, status=status.HTTP_409_CONFLICT)

        if data.get("status") == "active" and not data.get("password"):
            return Response({"detail": "Password is required for active users"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create(
            org_id=data["org_id"],
            email=data["email"],
            display_name=data["display_name"],
            phone=data.get("phone", ""),
            status=data.get("status", "invited"),
        )
        if data.get("password"):
            UserCredential.objects.update_or_create(
                user=user,
                defaults={
                    "password_hash": make_password(data["password"]),
                    "last_password_change_at": timezone.now(),
                },
            )
        role_name = data.get("role_name")
        if role_name:
            role = Role.objects.filter(org_id=data["org_id"], name__iexact=role_name).first()
            if not role:
                return Response({"detail": "Role not found"}, status=status.HTTP_400_BAD_REQUEST)
            UserRole.objects.get_or_create(user=user, role=role)
        if user.status == "invited":
            invite_token = _create_invite_token(user)
            _send_invite_email(user, invite_token)
        roles = list(
            UserRole.objects.filter(user=user)
            .select_related("role")
            .values_list("role__name", flat=True)
        )

        return Response(
            {
                "id": user.id,
                "org_id": user.org_id,
                "email": user.email,
                "display_name": user.display_name,
                "phone": user.phone,
                "status": user.status,
                "roles": roles,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(responses=UserResponseSerializer(many=True))
    def get(self, request):
        org_id = request.query_params.get("org_id")
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not _require_admin(request.user, int(org_id)):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)
        qs = User.objects.filter(org_id=org_id)
        query = request.query_params.get("q")
        if query:
            qs = qs.filter(models.Q(email__icontains=query) | models.Q(display_name__icontains=query))

        sort_by = request.query_params.get("sort_by", "id")
        sort_dir = request.query_params.get("sort_dir", "asc")
        allowed_sorts = {"id", "display_name", "email", "status", "created_at"}
        if sort_by not in allowed_sorts:
            sort_by = "id"
        prefix = "-" if sort_dir == "desc" else ""

        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), 100)
        total = qs.count()
        offset = (page - 1) * page_size
        users = []
        for user in qs.order_by(f"{prefix}{sort_by}")[offset:offset + page_size]:
            roles = list(
                UserRole.objects.filter(user=user)
                .select_related("role")
                .values_list("role__name", flat=True)
            )
            users.append(
                {
                    "id": user.id,
                    "org_id": user.org_id,
                    "email": user.email,
                    "display_name": user.display_name,
                    "phone": user.phone,
                    "status": user.status,
                    "roles": roles,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                }
            )
        return Response(
            {
                "results": users,
                "count": total,
                "page": page,
                "page_size": page_size,
            },
            status=status.HTTP_200_OK,
        )


class RoleListView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(responses=RoleResponseSerializer(many=True))
    def get(self, request):
        org_id = request.query_params.get("org_id")
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not _is_admin(request.user, int(org_id)):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)

        roles = Role.objects.filter(org_id=org_id)
        query = request.query_params.get("q")
        if query:
            roles = roles.filter(models.Q(name__icontains=query) | models.Q(description__icontains=query))

        sort_by = request.query_params.get("sort_by", "id")
        sort_dir = request.query_params.get("sort_dir", "asc")
        allowed_sorts = {"id", "name", "created_at"}
        if sort_by not in allowed_sorts:
            sort_by = "id"
        prefix = "-" if sort_dir == "desc" else ""

        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), 100)
        total = roles.count()
        offset = (page - 1) * page_size
        roles = roles.order_by(f"{prefix}{sort_by}")[offset:offset + page_size]

        return Response(
            {
                "results": [
                    {
                        "id": role.id,
                        "org_id": role.org_id,
                        "name": role.name,
                        "description": role.description,
                        "created_at": role.created_at,
                        "updated_at": role.updated_at,
                    }
                    for role in roles
                ],
                "count": total,
                "page": page,
                "page_size": page_size,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=RoleCreateSerializer, responses=RoleResponseSerializer)
    def post(self, request):
        serializer = RoleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not _is_admin(request.user, int(data["org_id"])):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)

        try:
            role = Role.objects.create(
                org_id=data["org_id"],
                name=data["name"],
                description=data.get("description", ""),
            )
        except IntegrityError:
            return Response({"detail": "Role already exists"}, status=status.HTTP_409_CONFLICT)

        return Response(
            {
                "id": role.id,
                "org_id": role.org_id,
                "name": role.name,
                "description": role.description,
                "created_at": role.created_at,
                "updated_at": role.updated_at,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(responses=RoleResponseSerializer)
class RoleDetailView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def get(self, request, role_id: int):
        role = Role.objects.filter(id=role_id).first()
        if not role:
            return Response({"detail": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _is_admin(request.user, int(role.org_id)):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            {
                "id": role.id,
                "org_id": role.org_id,
                "name": role.name,
                "description": role.description,
                "created_at": role.created_at,
                "updated_at": role.updated_at,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=RoleUpdateSerializer, responses=RoleResponseSerializer)
    def patch(self, request, role_id: int):
        role = Role.objects.filter(id=role_id).first()
        if not role:
            return Response({"detail": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _is_admin(request.user, int(role.org_id)):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)

        serializer = RoleUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "name" in data:
            role.name = data["name"]
        if "description" in data:
            role.description = data["description"]

        try:
            role.save()
        except IntegrityError:
            return Response({"detail": "Role already exists"}, status=status.HTTP_409_CONFLICT)

        return Response(
            {
                "id": role.id,
                "org_id": role.org_id,
                "name": role.name,
                "description": role.description,
                "created_at": role.created_at,
                "updated_at": role.updated_at,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=None, responses=None)
    def delete(self, request, role_id: int):
        role = Role.objects.filter(id=role_id).first()
        if not role:
            return Response({"detail": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _is_admin(request.user, int(role.org_id)):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)
        try:
            role.delete()
        except IntegrityError:
            return Response({"detail": "Role is in use"}, status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationListCreateView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(responses=OrganizationResponseSerializer(many=True))
    def get(self, request):
        if not _is_admin(request.user, request.user.org_id):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)
        orgs = Organization.objects.all().order_by("id")
        return Response(
            [
                {
                    "id": org.id,
                    "name": org.name,
                    "legal_name": org.legal_name,
                    "status": org.status,
                    "created_at": org.created_at,
                    "updated_at": org.updated_at,
                }
                for org in orgs
            ],
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=OrganizationCreateSerializer, responses=OrganizationResponseSerializer)
    def post(self, request):
        if not _is_admin(request.user, request.user.org_id):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        org = Organization.objects.create(
            name=data["name"],
            legal_name=data["legal_name"],
            status=data.get("status", "active"),
        )
        return Response(
            {
                "id": org.id,
                "name": org.name,
                "legal_name": org.legal_name,
                "status": org.status,
                "created_at": org.created_at,
                "updated_at": org.updated_at,
            },
            status=status.HTTP_201_CREATED,
        )


class OrganizationDetailView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(responses=OrganizationResponseSerializer)
    def get(self, request, org_id: int):
        org = Organization.objects.filter(id=org_id).first()
        if not org:
            return Response({"detail": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _is_admin(request.user, request.user.org_id):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            {
                "id": org.id,
                "name": org.name,
                "legal_name": org.legal_name,
                "status": org.status,
                "created_at": org.created_at,
                "updated_at": org.updated_at,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=OrganizationUpdateSerializer, responses=OrganizationResponseSerializer)
    def patch(self, request, org_id: int):
        org = Organization.objects.filter(id=org_id).first()
        if not org:
            return Response({"detail": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _is_admin(request.user, request.user.org_id):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)
        serializer = OrganizationUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        for field in ["name", "legal_name", "status"]:
            if field in data:
                setattr(org, field, data[field])
        org.save()
        return Response(
            {
                "id": org.id,
                "name": org.name,
                "legal_name": org.legal_name,
                "status": org.status,
                "created_at": org.created_at,
                "updated_at": org.updated_at,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=None, responses=None)
    def delete(self, request, org_id: int):
        org = Organization.objects.filter(id=org_id).first()
        if not org:
            return Response({"detail": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _is_admin(request.user, request.user.org_id):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)
        org.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses=UserResponseSerializer)
class UserDetailView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def get(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _require_admin(request.user, user.org_id):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)

        return Response(
            {
                "id": user.id,
                "org_id": user.org_id,
                "email": user.email,
                "display_name": user.display_name,
                "phone": user.phone,
                "status": user.status,
                "roles": list(
                    UserRole.objects.filter(user=user)
                    .select_related("role")
                    .values_list("role__name", flat=True)
                ),
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=UserUpdateSerializer, responses=UserResponseSerializer)
    def patch(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _require_admin(request.user, user.org_id):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        for field in ["email", "display_name", "phone", "status"]:
            if field in data:
                setattr(user, field, data[field])
        user.save()
        role_name = data.get("role_name")
        if role_name:
            role = Role.objects.filter(org_id=user.org_id, name__iexact=role_name).first()
            if not role:
                return Response({"detail": "Role not found"}, status=status.HTTP_400_BAD_REQUEST)
            UserRole.objects.filter(user=user).delete()
            UserRole.objects.get_or_create(user=user, role=role)

        return Response(
            {
                "id": user.id,
                "org_id": user.org_id,
                "email": user.email,
                "display_name": user.display_name,
                "phone": user.phone,
                "status": user.status,
                "roles": list(
                    UserRole.objects.filter(user=user)
                    .select_related("role")
                    .values_list("role__name", flat=True)
                ),
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=None, responses=None)
    def delete(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _is_admin(request.user, user.org_id):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)

        target_is_super = _is_super_admin(user, user.org_id)
        requester_is_super = _is_super_admin(request.user, user.org_id)
        if target_is_super and not requester_is_super:
            return Response({"detail": "Super admin required to delete this user"}, status=status.HTTP_403_FORBIDDEN)

        # clean protected relations before deleting user
        UserRole.objects.filter(user=user).delete()
        UserDepartment.objects.filter(user=user).delete()
        AuthToken.objects.filter(user=user).delete()
        RefreshToken.objects.filter(user=user).delete()
        PasswordResetToken.objects.filter(user=user).delete()
        UserCredential.objects.filter(user=user).delete()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=None, responses=UserResponseSerializer)
class UserInviteView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def post(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _require_admin(request.user, user.org_id):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)

        user.status = "invited"
        user.save(update_fields=["status", "updated_at"])
        invite_token = _create_invite_token(user)
        _send_invite_email(user, invite_token)

        return Response(
            {
                "id": user.id,
                "org_id": user.org_id,
                "email": user.email,
                "display_name": user.display_name,
                "phone": user.phone,
                "status": user.status,
                "roles": list(
                    UserRole.objects.filter(user=user)
                    .select_related("role")
                    .values_list("role__name", flat=True)
                ),
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(request=None, responses=UserResponseSerializer)
class UserSuspendView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def post(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _require_admin(request.user, user.org_id):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)

        user.status = "suspended"
        user.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "id": user.id,
                "org_id": user.org_id,
                "email": user.email,
                "display_name": user.display_name,
                "phone": user.phone,
                "status": user.status,
                "roles": list(
                    UserRole.objects.filter(user=user)
                    .select_related("role")
                    .values_list("role__name", flat=True)
                ),
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(request=None, responses=UserResponseSerializer)
class UserReactivateView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def post(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _require_admin(request.user, user.org_id):
            return Response({"detail": "Admin role required"}, status=status.HTTP_403_FORBIDDEN)

        user.status = "active"
        user.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "id": user.id,
                "org_id": user.org_id,
                "email": user.email,
                "display_name": user.display_name,
                "phone": user.phone,
                "status": user.status,
                "roles": list(
                    UserRole.objects.filter(user=user)
                    .select_related("role")
                    .values_list("role__name", flat=True)
                ),
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            },
            status=status.HTTP_200_OK,
        )
