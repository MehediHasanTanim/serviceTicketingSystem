import secrets
from datetime import timedelta, datetime, timezone as dt_timezone

from django.db import transaction, models, IntegrityError
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from rest_framework_simplejwt.tokens import RefreshToken as SimpleJWTRefreshToken

from application.services.audit_logging import AuditContext
from infrastructure.db.core.models import (
    Department,
    InviteToken,
    Organization,
    AuditLog,
    PasswordResetToken,
    Permission,
    Property,
    Role,
    RolePermission,
    User,
    UserCredential,
    UserDepartment,
    UserProperty,
    UserRole,
    RefreshToken as RefreshTokenModel,
)
from infrastructure.services.audit_logging import get_audit_logger
from interfaces.api.authentication import BearerTokenAuthentication
from interfaces.api.serializers import (
    SignupSerializer,
    LoginSerializer,
    RefreshSerializer,
    JWTPairResponseSerializer,
    SignupJWTResponseSerializer,
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
    PermissionCreateSerializer,
    PermissionUpdateSerializer,
    PermissionResponseSerializer,
    RolePermissionAssignSerializer,
    OrganizationCreateSerializer,
    OrganizationUpdateSerializer,
    OrganizationResponseSerializer,
    PropertyCreateSerializer,
    PropertyUpdateSerializer,
    PropertyResponseSerializer,
    DepartmentCreateSerializer,
    DepartmentUpdateSerializer,
    DepartmentResponseSerializer,
    UserDepartmentAssignSerializer,
    UserPropertyAssignSerializer,
    UserRoleAssignSerializer,
)


RESET_TOKEN_TTL_MINUTES = 30
INVITE_TOKEN_TTL_HOURS = getattr(settings, "INVITE_TOKEN_TTL_HOURS", 72)


def _new_token_key():
    return secrets.token_hex(32)


def _token_exp_to_iso(exp_value: int | None) -> str | None:
    if not exp_value:
        return None
    return datetime.fromtimestamp(int(exp_value), tz=dt_timezone.utc).isoformat()


def _store_refresh_token(user, refresh_token: SimpleJWTRefreshToken) -> None:
    jti = refresh_token.get("jti")
    exp = refresh_token.get("exp")
    if not jti:
        return
    expires_at = datetime.fromtimestamp(int(exp), tz=dt_timezone.utc) if exp else timezone.now()
    RefreshTokenModel.objects.update_or_create(
        key=jti,
        defaults={
            "user": user,
            "expires_at": expires_at,
            "revoked_at": None,
        },
    )


def _issue_tokens(user):
    refresh = SimpleJWTRefreshToken.for_user(user)
    access = refresh.access_token
    _store_refresh_token(user, refresh)
    return {
        "access": str(access),
        "refresh": str(refresh),
        "access_expires_at": _token_exp_to_iso(access.get("exp")),
        "refresh_expires_at": _token_exp_to_iso(refresh.get("exp")),
    }


def _rotate_refresh_token(refresh: SimpleJWTRefreshToken, user: User) -> SimpleJWTRefreshToken:
    rotate = settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", False)
    if not rotate:
        return refresh
    new_refresh = SimpleJWTRefreshToken.for_user(user)
    _store_refresh_token(user, new_refresh)
    return new_refresh


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


def _has_permission(user, code: str) -> bool:
    if not user:
        return False
    if hasattr(user, "is_authenticated") and not user.is_authenticated:
        return False
    if _is_super_admin(user, user.org_id):
        return True
    return RolePermission.objects.filter(
        role__user_roles__user=user,
        permission__code=code,
    ).exists()


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


def _get_request_ip(request) -> str:
    if hasattr(request, "audit_context"):
        return request.audit_context.get("ip_address", "")
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _build_audit_context(request, org_id: int, *, property_id: int | None = None, actor_user=None) -> AuditContext:
    if hasattr(request, "audit_context"):
        meta = request.audit_context
        return AuditContext(
            org_id=org_id,
            property_id=property_id,
            actor_user_id=getattr(actor_user, "id", None),
            ip_address=meta.get("ip_address", ""),
            user_agent=meta.get("user_agent", ""),
        )
    return AuditContext(
        org_id=org_id,
        property_id=property_id,
        actor_user_id=getattr(actor_user, "id", None),
        ip_address=_get_request_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


def _audit_action(
    request,
    *,
    org_id: int,
    action: str,
    target_type: str,
    target_id: str,
    metadata: dict | None = None,
    property_id: int | None = None,
    actor_user=None,
) -> None:
    logger = get_audit_logger()
    context = _build_audit_context(request, org_id, property_id=property_id, actor_user=actor_user)
    logger.log_action(
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        metadata=metadata or {},
        context=context,
    )


def _audit_entity_change(
    request,
    *,
    org_id: int,
    entity_type: str,
    entity_id: str,
    change_type: str,
    before: dict | None = None,
    after: dict | None = None,
    property_id: int | None = None,
    actor_user=None,
) -> None:
    logger = get_audit_logger()
    context = _build_audit_context(request, org_id, property_id=property_id, actor_user=actor_user)
    logger.log_entity_change(
        entity_type=entity_type,
        entity_id=str(entity_id),
        change_type=change_type,
        before=before or {},
        after=after or {},
        context=context,
    )


@extend_schema(
    request=SignupSerializer,
    responses={
        201: OpenApiResponse(
            response=SignupJWTResponseSerializer,
            examples=[
                OpenApiExample(
                    "SignupSuccess",
                    value={
                        "user_id": 42,
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
                        "access_expires_at": "2026-04-15T10:30:00Z",
                        "refresh_expires_at": "2026-05-15T09:30:00Z",
                    },
                )
            ],
        )
    },
)
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
            tokens = _issue_tokens(user)

        return Response(
            {
                "user_id": user.id,
                **tokens,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            response=JWTPairResponseSerializer,
            examples=[
                OpenApiExample(
                    "LoginSuccess",
                    value={
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
                        "access_expires_at": "2026-04-15T10:30:00Z",
                        "refresh_expires_at": "2026-05-15T09:30:00Z",
                    },
                )
            ],
        )
    },
)
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

        tokens = _issue_tokens(user)
        return Response(
            {
                **tokens,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(request=None)
class LogoutView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def post(self, request):
        if request.user and getattr(request.user, "id", None):
            RefreshTokenModel.objects.filter(
                user=request.user,
                revoked_at__isnull=True,
            ).update(revoked_at=timezone.now())
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request=RefreshSerializer,
    responses={
        200: OpenApiResponse(
            response=JWTPairResponseSerializer,
            examples=[
                OpenApiExample(
                    "RefreshSuccess",
                    value={
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.new_access",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.new_refresh",
                        "access_expires_at": "2026-04-15T11:30:00Z",
                        "refresh_expires_at": "2026-05-15T09:30:00Z",
                    },
                )
            ],
        )
    },
)
class RefreshView(APIView):
    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_key = serializer.validated_data["refresh_token"]

        try:
            refresh = SimpleJWTRefreshToken(refresh_key)
        except Exception:
            return Response({"detail": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

        user_id = refresh.get("user_id")
        jti = refresh.get("jti")
        if not user_id or not jti:
            return Response({"detail": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
        record = RefreshTokenModel.objects.filter(
            user=user,
            key=jti,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()
        if not record:
            return Response({"detail": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

        rotated_refresh = _rotate_refresh_token(refresh, user)
        if rotated_refresh != refresh:
            record.revoked_at = timezone.now()
            record.save(update_fields=["revoked_at"])
        access = rotated_refresh.access_token if rotated_refresh != refresh else refresh.access_token
        return Response(
            {
                "access": str(access),
                "refresh": str(rotated_refresh),
                "access_expires_at": _token_exp_to_iso(access.get("exp")),
                "refresh_expires_at": _token_exp_to_iso(rotated_refresh.get("exp")),
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
        permissions = list(
            RolePermission.objects.filter(role__user_roles__user=user)
            .select_related("permission")
            .values_list("permission__code", flat=True)
            .distinct()
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
                "permissions": permissions,
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

        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

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
        _audit_entity_change(
            request,
            org_id=user.org_id,
            entity_type="user",
            entity_id=str(user.id),
            change_type="create",
            after={
                "email": user.email,
                "display_name": user.display_name,
                "phone": user.phone,
                "status": user.status,
                "roles": roles,
            },
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=user.org_id,
            action="user.created",
            target_type="user",
            target_id=str(user.id),
            metadata={"email": user.email},
            actor_user=request.user,
        )
        if role_name:
            _audit_action(
                request,
                org_id=user.org_id,
                action="user.role_assigned",
                target_type="user",
                target_id=str(user.id),
                metadata={"role": role_name},
                actor_user=request.user,
            )
        if user.status == "invited":
            _audit_action(
                request,
                org_id=user.org_id,
                action="user.invited",
                target_type="user",
                target_id=str(user.id),
                metadata={"email": user.email},
                actor_user=request.user,
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
        if not _has_permission(request.user, "users.view"):
            return Response({"detail": "Permission required: users.view"}, status=status.HTTP_403_FORBIDDEN)
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
        if not _has_permission(request.user, "roles.view"):
            return Response({"detail": "Permission required: roles.view"}, status=status.HTTP_403_FORBIDDEN)

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

        if not _has_permission(request.user, "roles.manage"):
            return Response({"detail": "Permission required: roles.manage"}, status=status.HTTP_403_FORBIDDEN)

        try:
            role = Role.objects.create(
                org_id=data["org_id"],
                name=data["name"],
                description=data.get("description", ""),
            )
        except IntegrityError:
            return Response({"detail": "Role already exists"}, status=status.HTTP_409_CONFLICT)

        _audit_entity_change(
            request,
            org_id=role.org_id,
            entity_type="role",
            entity_id=str(role.id),
            change_type="create",
            after={"name": role.name, "description": role.description},
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=role.org_id,
            action="role.created",
            target_type="role",
            target_id=str(role.id),
            metadata={"name": role.name},
            actor_user=request.user,
        )

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
        if not _has_permission(request.user, "roles.view"):
            return Response({"detail": "Permission required: roles.view"}, status=status.HTTP_403_FORBIDDEN)
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
        if not _has_permission(request.user, "roles.manage"):
            return Response({"detail": "Permission required: roles.manage"}, status=status.HTTP_403_FORBIDDEN)

        before = {"name": role.name, "description": role.description}
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

        _audit_entity_change(
            request,
            org_id=role.org_id,
            entity_type="role",
            entity_id=str(role.id),
            change_type="update",
            before=before,
            after={"name": role.name, "description": role.description},
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=role.org_id,
            action="role.updated",
            target_type="role",
            target_id=str(role.id),
            metadata={"name": role.name},
            actor_user=request.user,
        )

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
        if not _has_permission(request.user, "roles.manage"):
            return Response({"detail": "Permission required: roles.manage"}, status=status.HTTP_403_FORBIDDEN)
        try:
            role.delete()
        except IntegrityError:
            return Response({"detail": "Role is in use"}, status=status.HTTP_409_CONFLICT)

        _audit_entity_change(
            request,
            org_id=role.org_id,
            entity_type="role",
            entity_id=str(role_id),
            change_type="delete",
            before={"name": role.name, "description": role.description},
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=role.org_id,
            action="role.deleted",
            target_type="role",
            target_id=str(role_id),
            metadata={"name": role.name},
            actor_user=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class PermissionListCreateView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(responses=PermissionResponseSerializer(many=True))
    def get(self, request):
        if not _has_permission(request.user, "permissions.view"):
            return Response({"detail": "Permission required: permissions.view"}, status=status.HTTP_403_FORBIDDEN)

        perms = Permission.objects.all()
        query = request.query_params.get("q")
        if query:
            perms = perms.filter(models.Q(code__icontains=query) | models.Q(description__icontains=query))

        sort_by = request.query_params.get("sort_by", "id")
        sort_dir = request.query_params.get("sort_dir", "asc")
        allowed_sorts = {"id", "code"}
        if sort_by not in allowed_sorts:
            sort_by = "id"
        prefix = "-" if sort_dir == "desc" else ""

        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), 100)
        total = perms.count()
        offset = (page - 1) * page_size
        perms = perms.order_by(f"{prefix}{sort_by}")[offset:offset + page_size]

        return Response(
            {
                "results": [
                    {
                        "id": perm.id,
                        "code": perm.code,
                        "description": perm.description,
                    }
                    for perm in perms
                ],
                "count": total,
                "page": page,
                "page_size": page_size,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=PermissionCreateSerializer, responses=PermissionResponseSerializer)
    def post(self, request):
        if not _has_permission(request.user, "permissions.manage"):
            return Response({"detail": "Permission required: permissions.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = PermissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            perm = Permission.objects.create(
                code=data["code"],
                description=data.get("description", ""),
            )
        except IntegrityError:
            return Response({"detail": "Permission already exists"}, status=status.HTTP_409_CONFLICT)

        _audit_entity_change(
            request,
            org_id=request.user.org_id,
            entity_type="permission",
            entity_id=str(perm.id),
            change_type="create",
            after={"code": perm.code, "description": perm.description},
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=request.user.org_id,
            action="permission.created",
            target_type="permission",
            target_id=str(perm.id),
            metadata={"code": perm.code},
            actor_user=request.user,
        )
        return Response(
            {
                "id": perm.id,
                "code": perm.code,
                "description": perm.description,
            },
            status=status.HTTP_201_CREATED,
        )


class PermissionDetailView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(responses=PermissionResponseSerializer)
    def get(self, request, permission_id: int):
        perm = Permission.objects.filter(id=permission_id).first()
        if not perm:
            return Response({"detail": "Permission not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "permissions.view"):
            return Response({"detail": "Permission required: permissions.view"}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            {
                "id": perm.id,
                "code": perm.code,
                "description": perm.description,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=PermissionUpdateSerializer, responses=PermissionResponseSerializer)
    def patch(self, request, permission_id: int):
        perm = Permission.objects.filter(id=permission_id).first()
        if not perm:
            return Response({"detail": "Permission not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "permissions.manage"):
            return Response({"detail": "Permission required: permissions.manage"}, status=status.HTTP_403_FORBIDDEN)

        before = {"code": perm.code, "description": perm.description}
        serializer = PermissionUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "code" in data:
            perm.code = data["code"]
        if "description" in data:
            perm.description = data["description"]
        try:
            perm.save()
        except IntegrityError:
            return Response({"detail": "Permission already exists"}, status=status.HTTP_409_CONFLICT)

        _audit_entity_change(
            request,
            org_id=request.user.org_id,
            entity_type="permission",
            entity_id=str(perm.id),
            change_type="update",
            before=before,
            after={"code": perm.code, "description": perm.description},
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=request.user.org_id,
            action="permission.updated",
            target_type="permission",
            target_id=str(perm.id),
            metadata={"code": perm.code},
            actor_user=request.user,
        )
        return Response(
            {
                "id": perm.id,
                "code": perm.code,
                "description": perm.description,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=None, responses=None)
    def delete(self, request, permission_id: int):
        perm = Permission.objects.filter(id=permission_id).first()
        if not perm:
            return Response({"detail": "Permission not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "permissions.manage"):
            return Response({"detail": "Permission required: permissions.manage"}, status=status.HTTP_403_FORBIDDEN)
        try:
            perm.delete()
        except IntegrityError:
            return Response({"detail": "Permission is in use"}, status=status.HTTP_409_CONFLICT)
        _audit_entity_change(
            request,
            org_id=request.user.org_id,
            entity_type="permission",
            entity_id=str(permission_id),
            change_type="delete",
            before={"code": perm.code, "description": perm.description},
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=request.user.org_id,
            action="permission.deleted",
            target_type="permission",
            target_id=str(permission_id),
            metadata={"code": perm.code},
            actor_user=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class RolePermissionListCreateView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(responses=None)
    def get(self, request, role_id: int):
        role = Role.objects.filter(id=role_id).first()
        if not role:
            return Response({"detail": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "roles.manage"):
            return Response({"detail": "Permission required: roles.manage"}, status=status.HTTP_403_FORBIDDEN)

        permissions = (
            RolePermission.objects.filter(role=role)
            .select_related("permission")
            .order_by("permission__code")
        )
        data = [
            {
                "permission_id": rp.permission_id,
                "code": rp.permission.code,
                "description": rp.permission.description,
            }
            for rp in permissions
        ]
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(request=RolePermissionAssignSerializer, responses=None)
    def post(self, request, role_id: int):
        role = Role.objects.filter(id=role_id).first()
        if not role:
            return Response({"detail": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "roles.manage"):
            return Response({"detail": "Permission required: roles.manage"}, status=status.HTTP_403_FORBIDDEN)

        serializer = RolePermissionAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        perm = Permission.objects.filter(id=data["permission_id"]).first()
        if not perm:
            return Response({"detail": "Permission not found"}, status=status.HTTP_404_NOT_FOUND)

        RolePermission.objects.get_or_create(role=role, permission=perm)
        _audit_action(
            request,
            org_id=role.org_id,
            action="role.permission_assigned",
            target_type="role",
            target_id=str(role.id),
            metadata={"permission": perm.code},
            actor_user=request.user,
        )
        return Response(
            {
                "permission_id": perm.id,
                "code": perm.code,
                "description": perm.description,
            },
            status=status.HTTP_201_CREATED,
        )


class RolePermissionDetailView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def delete(self, request, role_id: int, permission_id: int):
        role = Role.objects.filter(id=role_id).first()
        if not role:
            return Response({"detail": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "roles.manage"):
            return Response({"detail": "Permission required: roles.manage"}, status=status.HTTP_403_FORBIDDEN)

        rel = RolePermission.objects.filter(role=role, permission_id=permission_id).first()
        if not rel:
            return Response({"detail": "Mapping not found"}, status=status.HTTP_404_NOT_FOUND)
        rel.delete()
        _audit_action(
            request,
            org_id=role.org_id,
            action="role.permission_removed",
            target_type="role",
            target_id=str(role.id),
            metadata={"permission_id": permission_id},
            actor_user=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuditLogListView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def get(self, request):
        org_id = request.query_params.get("org_id")
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not _has_permission(request.user, "audit.view"):
            return Response({"detail": "Permission required: audit.view"}, status=status.HTTP_403_FORBIDDEN)

        logs = AuditLog.objects.filter(org_id=org_id)
        property_id = request.query_params.get("property_id")
        if property_id:
            logs = logs.filter(property_id=property_id)
        actor_user_id = request.query_params.get("actor_user_id")
        if actor_user_id:
            logs = logs.filter(actor_user_id=actor_user_id)
        action = request.query_params.get("action")
        if action:
            logs = logs.filter(action__icontains=action)
        target_type = request.query_params.get("target_type")
        if target_type:
            logs = logs.filter(target_type__icontains=target_type)
        target_id = request.query_params.get("target_id")
        if target_id:
            logs = logs.filter(target_id=str(target_id))
        date_from = request.query_params.get("date_from")
        if date_from:
            parsed = parse_date(date_from)
            if parsed:
                logs = logs.filter(created_at__date__gte=parsed)
        date_to = request.query_params.get("date_to")
        if date_to:
            parsed = parse_date(date_to)
            if parsed:
                logs = logs.filter(created_at__date__lte=parsed)
        query = request.query_params.get("q")
        if query:
            logs = logs.filter(
                models.Q(action__icontains=query)
                | models.Q(target_type__icontains=query)
                | models.Q(target_id__icontains=query)
                | models.Q(metadata_json__icontains=query)
            )

        sort_by = request.query_params.get("sort_by", "created_at")
        sort_dir = request.query_params.get("sort_dir", "desc")
        allowed_sorts = {"created_at", "action", "target_type"}
        if sort_by not in allowed_sorts:
            sort_by = "created_at"
        prefix = "-" if sort_dir == "desc" else ""

        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), 100)
        total = logs.count()
        offset = (page - 1) * page_size
        logs = logs.order_by(f"{prefix}{sort_by}")[offset:offset + page_size]

        return Response(
            {
                "results": [
                    {
                        "id": log.id,
                        "org_id": log.org_id,
                        "property_id": log.property_id,
                        "actor_user_id": log.actor_user_id,
                        "action": log.action,
                        "target_type": log.target_type,
                        "target_id": log.target_id,
                        "metadata": log.metadata_json,
                        "ip_address": log.ip_address,
                        "user_agent": log.user_agent,
                        "created_at": log.created_at,
                    }
                    for log in logs
                ],
                "count": total,
                "page": page,
                "page_size": page_size,
            },
            status=status.HTTP_200_OK,
        )


class OrganizationListCreateView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(responses=OrganizationResponseSerializer(many=True))
    def get(self, request):
        if not _has_permission(request.user, "org.view"):
            return Response({"detail": "Permission required: org.view"}, status=status.HTTP_403_FORBIDDEN)
        orgs = Organization.objects.all()
        query = request.query_params.get("q")
        if query:
            orgs = orgs.filter(models.Q(name__icontains=query) | models.Q(legal_name__icontains=query))

        sort_by = request.query_params.get("sort_by", "id")
        sort_dir = request.query_params.get("sort_dir", "asc")
        allowed_sorts = {"id", "name", "legal_name", "status", "created_at"}
        if sort_by not in allowed_sorts:
            sort_by = "id"
        prefix = "-" if sort_dir == "desc" else ""

        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), 100)
        total = orgs.count()
        offset = (page - 1) * page_size
        orgs = orgs.order_by(f"{prefix}{sort_by}")[offset:offset + page_size]

        return Response(
            {
                "results": [
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
                "count": total,
                "page": page,
                "page_size": page_size,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=OrganizationCreateSerializer, responses=OrganizationResponseSerializer)
    def post(self, request):
        if not _has_permission(request.user, "org.manage"):
            return Response({"detail": "Permission required: org.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        org = Organization.objects.create(
            name=data["name"],
            legal_name=data["legal_name"],
            status=data.get("status", "active"),
        )
        _audit_entity_change(
            request,
            org_id=org.id,
            entity_type="organization",
            entity_id=str(org.id),
            change_type="create",
            after={"name": org.name, "legal_name": org.legal_name, "status": org.status},
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=org.id,
            action="organization.created",
            target_type="organization",
            target_id=str(org.id),
            metadata={"name": org.name},
            actor_user=request.user,
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
        if not _has_permission(request.user, "org.view"):
            return Response({"detail": "Permission required: org.view"}, status=status.HTTP_403_FORBIDDEN)
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
        if not _has_permission(request.user, "org.manage"):
            return Response({"detail": "Permission required: org.manage"}, status=status.HTTP_403_FORBIDDEN)
        before = {"name": org.name, "legal_name": org.legal_name, "status": org.status}
        serializer = OrganizationUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        for field in ["name", "legal_name", "status"]:
            if field in data:
                setattr(org, field, data[field])
        org.save()
        _audit_entity_change(
            request,
            org_id=org.id,
            entity_type="organization",
            entity_id=str(org.id),
            change_type="update",
            before=before,
            after={"name": org.name, "legal_name": org.legal_name, "status": org.status},
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=org.id,
            action="organization.updated",
            target_type="organization",
            target_id=str(org.id),
            metadata={"name": org.name},
            actor_user=request.user,
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
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=None, responses=None)
    def delete(self, request, org_id: int):
        org = Organization.objects.filter(id=org_id).first()
        if not org:
            return Response({"detail": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "org.manage"):
            return Response({"detail": "Permission required: org.manage"}, status=status.HTTP_403_FORBIDDEN)
        org.delete()
        _audit_entity_change(
            request,
            org_id=org_id,
            entity_type="organization",
            entity_id=str(org_id),
            change_type="delete",
            before={"name": org.name, "legal_name": org.legal_name, "status": org.status},
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=org_id,
            action="organization.deleted",
            target_type="organization",
            target_id=str(org_id),
            metadata={"name": org.name},
            actor_user=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class PropertyListCreateView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(request=PropertyCreateSerializer, responses=PropertyResponseSerializer)
    def post(self, request):
        serializer = PropertyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not _has_permission(request.user, "properties.manage"):
            return Response({"detail": "Permission required: properties.manage"}, status=status.HTTP_403_FORBIDDEN)

        prop = Property.objects.create(
            org_id=data["org_id"],
            code=data["code"],
            name=data["name"],
            timezone=data["timezone"],
            address_line1=data["address_line1"],
            address_line2=data.get("address_line2", ""),
            city=data["city"],
            state=data.get("state", ""),
            postal_code=data.get("postal_code", ""),
            country=data["country"],
        )
        _audit_entity_change(
            request,
            org_id=prop.org_id,
            property_id=prop.id,
            entity_type="property",
            entity_id=str(prop.id),
            change_type="create",
            after={
                "code": prop.code,
                "name": prop.name,
                "timezone": prop.timezone,
                "city": prop.city,
                "country": prop.country,
            },
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=prop.org_id,
            property_id=prop.id,
            action="property.created",
            target_type="property",
            target_id=str(prop.id),
            metadata={"code": prop.code, "name": prop.name},
            actor_user=request.user,
        )

        return Response(
            {
                "id": prop.id,
                "org_id": prop.org_id,
                "code": prop.code,
                "name": prop.name,
                "timezone": prop.timezone,
                "address_line1": prop.address_line1,
                "address_line2": prop.address_line2,
                "city": prop.city,
                "state": prop.state,
                "postal_code": prop.postal_code,
                "country": prop.country,
                "created_at": prop.created_at,
                "updated_at": prop.updated_at,
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(responses=PropertyResponseSerializer(many=True))
    def get(self, request):
        org_id = request.query_params.get("org_id")
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not _has_permission(request.user, "properties.view"):
            return Response({"detail": "Permission required: properties.view"}, status=status.HTTP_403_FORBIDDEN)
        props = Property.objects.filter(org_id=org_id)
        query = request.query_params.get("q")
        if query:
            props = props.filter(
                models.Q(code__icontains=query)
                | models.Q(name__icontains=query)
                | models.Q(city__icontains=query)
                | models.Q(country__icontains=query)
            )

        sort_by = request.query_params.get("sort_by", "id")
        sort_dir = request.query_params.get("sort_dir", "asc")
        allowed_sorts = {"id", "code", "name", "city", "country", "created_at"}
        if sort_by not in allowed_sorts:
            sort_by = "id"
        prefix = "-" if sort_dir == "desc" else ""

        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), 100)
        total = props.count()
        offset = (page - 1) * page_size
        props = props.order_by(f"{prefix}{sort_by}")[offset:offset + page_size]

        return Response(
            {
                "results": [
                    {
                        "id": prop.id,
                        "org_id": prop.org_id,
                        "code": prop.code,
                        "name": prop.name,
                        "timezone": prop.timezone,
                        "address_line1": prop.address_line1,
                        "address_line2": prop.address_line2,
                        "city": prop.city,
                        "state": prop.state,
                        "postal_code": prop.postal_code,
                        "country": prop.country,
                        "created_at": prop.created_at,
                        "updated_at": prop.updated_at,
                    }
                    for prop in props
                ],
                "count": total,
                "page": page,
                "page_size": page_size,
            },
            status=status.HTTP_200_OK,
        )


class PropertyDetailView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(responses=PropertyResponseSerializer)
    def get(self, request, property_id: int):
        prop = Property.objects.filter(id=property_id).first()
        if not prop:
            return Response({"detail": "Property not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "properties.view"):
            return Response({"detail": "Permission required: properties.view"}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            {
                "id": prop.id,
                "org_id": prop.org_id,
                "code": prop.code,
                "name": prop.name,
                "timezone": prop.timezone,
                "address_line1": prop.address_line1,
                "address_line2": prop.address_line2,
                "city": prop.city,
                "state": prop.state,
                "postal_code": prop.postal_code,
                "country": prop.country,
                "created_at": prop.created_at,
                "updated_at": prop.updated_at,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=PropertyUpdateSerializer, responses=PropertyResponseSerializer)
    def patch(self, request, property_id: int):
        prop = Property.objects.filter(id=property_id).first()
        if not prop:
            return Response({"detail": "Property not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "properties.manage"):
            return Response({"detail": "Permission required: properties.manage"}, status=status.HTTP_403_FORBIDDEN)
        before = {
            "code": prop.code,
            "name": prop.name,
            "timezone": prop.timezone,
            "city": prop.city,
            "country": prop.country,
        }
        serializer = PropertyUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        for field in [
            "code",
            "name",
            "timezone",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
        ]:
            if field in data:
                setattr(prop, field, data[field])
        prop.save()
        _audit_entity_change(
            request,
            org_id=prop.org_id,
            property_id=prop.id,
            entity_type="property",
            entity_id=str(prop.id),
            change_type="update",
            before=before,
            after={
                "code": prop.code,
                "name": prop.name,
                "timezone": prop.timezone,
                "city": prop.city,
                "country": prop.country,
            },
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=prop.org_id,
            property_id=prop.id,
            action="property.updated",
            target_type="property",
            target_id=str(prop.id),
            metadata={"code": prop.code, "name": prop.name},
            actor_user=request.user,
        )
        return Response(
            {
                "id": prop.id,
                "org_id": prop.org_id,
                "code": prop.code,
                "name": prop.name,
                "timezone": prop.timezone,
                "address_line1": prop.address_line1,
                "address_line2": prop.address_line2,
                "city": prop.city,
                "state": prop.state,
                "postal_code": prop.postal_code,
                "country": prop.country,
                "created_at": prop.created_at,
                "updated_at": prop.updated_at,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=None, responses=None)
    def delete(self, request, property_id: int):
        prop = Property.objects.filter(id=property_id).first()
        if not prop:
            return Response({"detail": "Property not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "properties.manage"):
            return Response({"detail": "Permission required: properties.manage"}, status=status.HTTP_403_FORBIDDEN)
        prop.delete()
        _audit_entity_change(
            request,
            org_id=prop.org_id,
            property_id=prop.id,
            entity_type="property",
            entity_id=str(property_id),
            change_type="delete",
            before={
                "code": prop.code,
                "name": prop.name,
                "timezone": prop.timezone,
                "city": prop.city,
                "country": prop.country,
            },
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=prop.org_id,
            property_id=prop.id,
            action="property.deleted",
            target_type="property",
            target_id=str(property_id),
            metadata={"code": prop.code, "name": prop.name},
            actor_user=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class DepartmentListCreateView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(request=DepartmentCreateSerializer, responses=DepartmentResponseSerializer)
    def post(self, request):
        serializer = DepartmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not _has_permission(request.user, "departments.manage"):
            return Response({"detail": "Permission required: departments.manage"}, status=status.HTTP_403_FORBIDDEN)

        property_id = data.get("property_id")
        if property_id:
            prop = Property.objects.filter(id=property_id, org_id=data["org_id"]).first()
            if not prop:
                return Response({"detail": "Property not found"}, status=status.HTTP_404_NOT_FOUND)

        dept = Department.objects.create(
            org_id=data["org_id"],
            property_id=property_id,
            name=data["name"],
            description=data.get("description", ""),
        )
        _audit_entity_change(
            request,
            org_id=dept.org_id,
            property_id=dept.property_id,
            entity_type="department",
            entity_id=str(dept.id),
            change_type="create",
            after={"name": dept.name, "description": dept.description, "property_id": dept.property_id},
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=dept.org_id,
            property_id=dept.property_id,
            action="department.created",
            target_type="department",
            target_id=str(dept.id),
            metadata={"name": dept.name},
            actor_user=request.user,
        )

        return Response(
            {
                "id": dept.id,
                "org_id": dept.org_id,
                "property_id": dept.property_id,
                "name": dept.name,
                "description": dept.description,
                "created_at": dept.created_at,
                "updated_at": dept.updated_at,
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(responses=DepartmentResponseSerializer(many=True))
    def get(self, request):
        org_id = request.query_params.get("org_id")
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not _has_permission(request.user, "departments.view"):
            return Response({"detail": "Permission required: departments.view"}, status=status.HTTP_403_FORBIDDEN)

        departments = Department.objects.filter(org_id=org_id)
        property_id = request.query_params.get("property_id")
        if property_id:
            departments = departments.filter(property_id=property_id)

        query = request.query_params.get("q")
        if query:
            departments = departments.filter(
                models.Q(name__icontains=query) | models.Q(description__icontains=query)
            )

        sort_by = request.query_params.get("sort_by", "id")
        sort_dir = request.query_params.get("sort_dir", "asc")
        allowed_sorts = {"id", "name", "created_at"}
        if sort_by not in allowed_sorts:
            sort_by = "id"
        prefix = "-" if sort_dir == "desc" else ""

        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), 100)
        total = departments.count()
        offset = (page - 1) * page_size
        departments = departments.order_by(f"{prefix}{sort_by}")[offset:offset + page_size]

        return Response(
            {
                "results": [
                    {
                        "id": dept.id,
                        "org_id": dept.org_id,
                        "property_id": dept.property_id,
                        "name": dept.name,
                        "description": dept.description,
                        "created_at": dept.created_at,
                        "updated_at": dept.updated_at,
                    }
                    for dept in departments
                ],
                "count": total,
                "page": page,
                "page_size": page_size,
            },
            status=status.HTTP_200_OK,
        )


class DepartmentDetailView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(responses=DepartmentResponseSerializer)
    def get(self, request, department_id: int):
        dept = Department.objects.filter(id=department_id).first()
        if not dept:
            return Response({"detail": "Department not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "departments.view"):
            return Response({"detail": "Permission required: departments.view"}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            {
                "id": dept.id,
                "org_id": dept.org_id,
                "property_id": dept.property_id,
                "name": dept.name,
                "description": dept.description,
                "created_at": dept.created_at,
                "updated_at": dept.updated_at,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=DepartmentUpdateSerializer, responses=DepartmentResponseSerializer)
    def patch(self, request, department_id: int):
        dept = Department.objects.filter(id=department_id).first()
        if not dept:
            return Response({"detail": "Department not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "departments.manage"):
            return Response({"detail": "Permission required: departments.manage"}, status=status.HTTP_403_FORBIDDEN)

        before = {
            "name": dept.name,
            "description": dept.description,
            "property_id": dept.property_id,
        }
        serializer = DepartmentUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "property_id" in data:
            prop_id = data.get("property_id")
            if prop_id:
                prop = Property.objects.filter(id=prop_id, org_id=dept.org_id).first()
                if not prop:
                    return Response({"detail": "Property not found"}, status=status.HTTP_404_NOT_FOUND)
            dept.property_id = prop_id
        if "name" in data:
            dept.name = data["name"]
        if "description" in data:
            dept.description = data["description"]
        dept.save()
        _audit_entity_change(
            request,
            org_id=dept.org_id,
            property_id=dept.property_id,
            entity_type="department",
            entity_id=str(dept.id),
            change_type="update",
            before=before,
            after={"name": dept.name, "description": dept.description, "property_id": dept.property_id},
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=dept.org_id,
            property_id=dept.property_id,
            action="department.updated",
            target_type="department",
            target_id=str(dept.id),
            metadata={"name": dept.name},
            actor_user=request.user,
        )

        return Response(
            {
                "id": dept.id,
                "org_id": dept.org_id,
                "property_id": dept.property_id,
                "name": dept.name,
                "description": dept.description,
                "created_at": dept.created_at,
                "updated_at": dept.updated_at,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=None, responses=None)
    def delete(self, request, department_id: int):
        dept = Department.objects.filter(id=department_id).first()
        if not dept:
            return Response({"detail": "Department not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "departments.manage"):
            return Response({"detail": "Permission required: departments.manage"}, status=status.HTTP_403_FORBIDDEN)
        dept.delete()
        _audit_entity_change(
            request,
            org_id=dept.org_id,
            property_id=dept.property_id,
            entity_type="department",
            entity_id=str(department_id),
            change_type="delete",
            before={"name": dept.name, "description": dept.description, "property_id": dept.property_id},
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=dept.org_id,
            property_id=dept.property_id,
            action="department.deleted",
            target_type="department",
            target_id=str(department_id),
            metadata={"name": dept.name},
            actor_user=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses=UserResponseSerializer)
class UserDetailView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def get(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "users.view"):
            return Response({"detail": "Permission required: users.view"}, status=status.HTTP_403_FORBIDDEN)

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
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        before = {
            "email": user.email,
            "display_name": user.display_name,
            "phone": user.phone,
            "status": user.status,
        }
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
            UserRole.objects.get_or_create(user=user, role=role)

        _audit_entity_change(
            request,
            org_id=user.org_id,
            entity_type="user",
            entity_id=str(user.id),
            change_type="update",
            before=before,
            after={
                "email": user.email,
                "display_name": user.display_name,
                "phone": user.phone,
                "status": user.status,
            },
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=user.org_id,
            action="user.updated",
            target_type="user",
            target_id=str(user.id),
            metadata={"email": user.email},
            actor_user=request.user,
        )
        if role_name:
            _audit_action(
                request,
                org_id=user.org_id,
                action="user.role_assigned",
                target_type="user",
                target_id=str(user.id),
                metadata={"role": role_name},
                actor_user=request.user,
            )

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
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        before = {
            "email": user.email,
            "display_name": user.display_name,
            "phone": user.phone,
            "status": user.status,
        }
        target_is_super = _is_super_admin(user, user.org_id)
        requester_is_super = _is_super_admin(request.user, user.org_id)
        if target_is_super and not requester_is_super:
            return Response({"detail": "Super admin required to delete this user"}, status=status.HTTP_403_FORBIDDEN)

        # clean protected relations before deleting user
        UserRole.objects.filter(user=user).delete()
        UserDepartment.objects.filter(user=user).delete()
        UserProperty.objects.filter(user=user).delete()
        PasswordResetToken.objects.filter(user=user).delete()
        RefreshTokenModel.objects.filter(user=user).delete()
        UserCredential.objects.filter(user=user).delete()
        user.delete()
        _audit_entity_change(
            request,
            org_id=user.org_id,
            entity_type="user",
            entity_id=str(user_id),
            change_type="delete",
            before=before,
            actor_user=request.user,
        )
        _audit_action(
            request,
            org_id=user.org_id,
            action="user.deleted",
            target_type="user",
            target_id=str(user_id),
            metadata={"email": before.get("email")},
            actor_user=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=None, responses=None)
class UserPropertyListCreateView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(responses=None)
    def get(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        assignments = (
            UserProperty.objects.filter(user=user)
            .select_related("property")
            .order_by("property__name")
        )
        data = [
            {
                "property_id": assignment.property_id,
                "code": assignment.property.code,
                "name": assignment.property.name,
                "is_primary": assignment.is_primary,
                "assigned_at": assignment.assigned_at,
            }
            for assignment in assignments
        ]
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(request=UserPropertyAssignSerializer, responses=None)
    def post(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserPropertyAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        prop = Property.objects.filter(id=data["property_id"], org_id=user.org_id).first()
        if not prop:
            return Response({"detail": "Property not found"}, status=status.HTTP_404_NOT_FOUND)

        is_primary = data.get("is_primary", False)
        try:
            with transaction.atomic():
                assignment, created = UserProperty.objects.get_or_create(
                    user=user,
                    property=prop,
                    defaults={"is_primary": is_primary},
                )
                if not created:
                    assignment.is_primary = is_primary
                    assignment.save(update_fields=["is_primary"])
                if is_primary:
                    UserProperty.objects.filter(user=user).exclude(id=assignment.id).update(is_primary=False)
        except IntegrityError:
            return Response({"detail": "Property already assigned"}, status=status.HTTP_400_BAD_REQUEST)

        _audit_action(
            request,
            org_id=user.org_id,
            property_id=prop.id,
            action="user.property_assigned",
            target_type="user",
            target_id=str(user.id),
            metadata={"property_id": prop.id, "is_primary": assignment.is_primary},
            actor_user=request.user,
        )
        return Response(
            {
                "property_id": assignment.property_id,
                "code": prop.code,
                "name": prop.name,
                "is_primary": assignment.is_primary,
                "assigned_at": assignment.assigned_at,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(request=None, responses=None)
class UserPropertyDetailView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def delete(self, request, user_id: int, property_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        assignment = UserProperty.objects.filter(user=user, property_id=property_id).first()
        if not assignment:
            return Response({"detail": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
        assignment.delete()
        _audit_action(
            request,
            org_id=user.org_id,
            property_id=property_id,
            action="user.property_unassigned",
            target_type="user",
            target_id=str(user.id),
            metadata={"property_id": property_id},
            actor_user=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=None, responses=None)
class UserDepartmentListCreateView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    @extend_schema(responses=None)
    def get(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        assignments = (
            UserDepartment.objects.filter(user=user)
            .select_related("department")
            .order_by("department__name")
        )
        data = [
            {
                "department_id": assignment.department_id,
                "name": assignment.department.name,
                "property_id": assignment.department.property_id,
                "is_primary": assignment.is_primary,
            }
            for assignment in assignments
        ]
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(request=UserDepartmentAssignSerializer, responses=None)
    def post(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserDepartmentAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        dept = Department.objects.filter(id=data["department_id"], org_id=user.org_id).first()
        if not dept:
            return Response({"detail": "Department not found"}, status=status.HTTP_404_NOT_FOUND)

        is_primary = data.get("is_primary", False)
        assignment, created = UserDepartment.objects.get_or_create(
            user=user,
            department=dept,
            defaults={"is_primary": is_primary},
        )
        if not created:
            assignment.is_primary = is_primary
            assignment.save(update_fields=["is_primary"])
        if is_primary:
            UserDepartment.objects.filter(user=user).exclude(id=assignment.id).update(is_primary=False)
        _audit_action(
            request,
            org_id=user.org_id,
            property_id=dept.property_id,
            action="user.department_assigned",
            target_type="user",
            target_id=str(user.id),
            metadata={"department_id": dept.id, "is_primary": assignment.is_primary},
            actor_user=request.user,
        )
        return Response(
            {
                "department_id": assignment.department_id,
                "name": dept.name,
                "property_id": dept.property_id,
                "is_primary": assignment.is_primary,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(request=None, responses=None)
class UserDepartmentDetailView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def delete(self, request, user_id: int, department_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        assignment = UserDepartment.objects.filter(user=user, department_id=department_id).first()
        if not assignment:
            return Response({"detail": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
        department_property_id = assignment.department.property_id if assignment.department_id else None
        assignment.delete()
        _audit_action(
            request,
            org_id=user.org_id,
            property_id=department_property_id,
            action="user.department_unassigned",
            target_type="user",
            target_id=str(user.id),
            metadata={"department_id": department_id},
            actor_user=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=None, responses=None)
class UserRoleListCreateView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def get(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        roles = (
            UserRole.objects.filter(user=user)
            .select_related("role")
            .order_by("role__name")
        )
        data = [
            {
                "role_id": ur.role_id,
                "name": ur.role.name,
            }
            for ur in roles
        ]
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(request=UserRoleAssignSerializer, responses=None)
    def post(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserRoleAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        role = Role.objects.filter(id=data["role_id"], org_id=user.org_id).first()
        if not role:
            return Response({"detail": "Role not found"}, status=status.HTTP_404_NOT_FOUND)

        UserRole.objects.get_or_create(user=user, role=role)
        _audit_action(
            request,
            org_id=user.org_id,
            action="user.role_assigned",
            target_type="user",
            target_id=str(user.id),
            metadata={"role": role.name},
            actor_user=request.user,
        )
        return Response(
            {
                "role_id": role.id,
                "name": role.name,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(request=None, responses=None)
class UserRoleDetailView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def delete(self, request, user_id: int, role_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        assignment = UserRole.objects.filter(user=user, role_id=role_id).first()
        if not assignment:
            return Response({"detail": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
        role_name = assignment.role.name
        assignment.delete()
        _audit_action(
            request,
            org_id=user.org_id,
            action="user.role_removed",
            target_type="user",
            target_id=str(user.id),
            metadata={"role": role_name},
            actor_user=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=None, responses=UserResponseSerializer)
class UserInviteView(APIView):
    authentication_classes = [BearerTokenAuthentication]

    def post(self, request, user_id: int):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        user.status = "invited"
        user.save(update_fields=["status", "updated_at"])
        invite_token = _create_invite_token(user)
        _send_invite_email(user, invite_token)
        _audit_action(
            request,
            org_id=user.org_id,
            action="user.invited",
            target_type="user",
            target_id=str(user.id),
            metadata={"email": user.email},
            actor_user=request.user,
        )

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
        if not _has_permission(request.user, "users.manage"):
            return Response({"detail": "Permission required: users.manage"}, status=status.HTTP_403_FORBIDDEN)

        user.status = "suspended"
        user.save(update_fields=["status", "updated_at"])
        _audit_action(
            request,
            org_id=user.org_id,
            action="user.suspended",
            target_type="user",
            target_id=str(user.id),
            metadata={"email": user.email},
            actor_user=request.user,
        )

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
        _audit_action(
            request,
            org_id=user.org_id,
            action="user.reactivated",
            target_type="user",
            target_id=str(user.id),
            metadata={"email": user.email},
            actor_user=request.user,
        )

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
