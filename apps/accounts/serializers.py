
import random
import string
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import User
from apps.core.tasks import send_email_task


class UserSerializer(serializers.ModelSerializer):
 
    password = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'is_email_verified',
            'password', 'password_confirm', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    def validate(self, attrs):
        if 'password' in attrs:
            if attrs['password'] != attrs.get('password_confirm'):
                raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)

        user = User(**validated_data)
        if password:
            user.set_password(password)

        user.save()
        return user

    def update(self, instance, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class OTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):

    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits")
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")

        attrs['user'] = user
        return attrs


class TokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    user = UserSerializer(read_only=True)

    @classmethod
    def get_token(cls, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }
