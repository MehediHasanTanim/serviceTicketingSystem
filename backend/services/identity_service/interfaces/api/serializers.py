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
