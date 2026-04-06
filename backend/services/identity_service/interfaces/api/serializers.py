from rest_framework import serializers


class SignupSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    display_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)


class LoginSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class RefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(max_length=64)


class ForgotPasswordSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=64)
    new_password = serializers.CharField(min_length=8, write_only=True)


class ActivateInviteSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=64)
    password = serializers.CharField(min_length=8, write_only=True)


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    org_id = serializers.IntegerField()
    email = serializers.EmailField()
    display_name = serializers.CharField(max_length=255)
    roles = serializers.ListField(child=serializers.CharField())
    is_admin = serializers.BooleanField()
    is_super_admin = serializers.BooleanField()


class UserCreateSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    email = serializers.EmailField()
    display_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["active", "suspended", "invited"], default="invited")
    role_name = serializers.CharField(max_length=255, required=False)
    password = serializers.CharField(min_length=8, required=False, write_only=True)


class UserUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    display_name = serializers.CharField(max_length=255, required=False)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["active", "suspended", "invited"], required=False)
    role_name = serializers.CharField(max_length=255, required=False)


class UserResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    org_id = serializers.IntegerField()
    email = serializers.EmailField()
    display_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=32, allow_blank=True)
    status = serializers.CharField()
    roles = serializers.ListField(child=serializers.CharField(), required=False)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class RoleCreateSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)


class RoleUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class RoleResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    org_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
