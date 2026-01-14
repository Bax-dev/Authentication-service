
import random
import string
import time
from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from apps.core.status_codes import (
    SuccessResponses, ErrorResponses, HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST, HTTP_423_LOCKED
)
from rest_framework_simplejwt.views import TokenObtainPairView
from apps.accounts.models import User
from apps.accounts.serializers import (
    UserSerializer, OTPSerializer, OTPVerifySerializer,
    LoginSerializer, TokenSerializer
)
from apps.core.tasks import send_email_task
from apps.core.logger import auth_logger


@extend_schema(
    summary="User Registration",
    description="Register a new user account. An email will be sent asynchronously.",
    request=UserSerializer,
    responses={
        201: UserSerializer,
        400: "Bad Request - Validation errors",
        429: "Rate Limited"
    },
    examples=[
        OpenApiExample(
            "Registration Example",
            value={
                "email": "chioma@example.com",
                "first_name": "Chioma",
                "last_name": "Okoro",
                "password": "securepassword123",
                "password_confirm": "securepassword123"
            }
        )
    ]
)
class RegisterView(generics.CreateAPIView):
   
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        auth_logger.info(f"New user registered: {user.email}")
        send_email_task.delay(
            subject="Welcome to TSES App",
            message=f"Welcome {user.first_name or user.email}! Your account has been created.",
            recipient_list=[user.email]
        )


@extend_schema(
    summary="User Profile",
    description="Get or update the authenticated user's profile information.",
    request=UserSerializer,
    responses={
        200: UserSerializer,
        401: "Unauthorized",
        400: "Bad Request"
    }
)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    summary="Request OTP",
    description="Request a one-time password (OTP) to be sent to the user's email for authentication.",
    request=OTPSerializer,
    responses={
        202: {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "expires_in": {"type": "string", "description": "Time until OTP expires (e.g., '5 minutes')"}
            }
        },
        400: "Bad Request - Invalid email",
        429: "Rate Limited"
    },
    examples=[
        OpenApiExample(
            "OTP Request Example",
            value={"email": "user@example.com"}
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def otp_request(request):
    from apps.accounts.serializers import OTPSerializer

    serializer = OTPSerializer(data=request.data)
    if not serializer.is_valid():
        response_data, status_code = ErrorResponses.invalid_email_format()
        return Response(response_data, status=status_code)

    email = serializer.validated_data['email']

    from django.core.cache import cache

    from apps.core.rate_limits import RedisRateLimiter
    limiter = RedisRateLimiter()
    email_key = f"ratelimit:otp_request:email:{email}"
    email_config = {
        'requests': settings.RATE_LIMITS.get('otp_request_email', {'requests': 3, 'window': 600})
    }

    if limiter.is_rate_limited(email_key, email_config['requests']['requests'], email_config['requests']['window']):
        reset_time = limiter.get_reset_time(email_key, email_config['requests']['window'])
        response_data, status_code = ErrorResponses.rate_limit_exceeded(
            "Too many OTP requests for this email. Try again later.",
            reset_time,
            "email"
        )
        return Response(response_data, status=status_code, headers={'Retry-After': str(reset_time)})

    otp_code = ''.join(random.choices(string.digits, k=6))

    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"OTP generated for {email}: {otp_code}")

    otp_key = f"otp:{email}"
    cache.set(otp_key, otp_code, timeout=300) 

    limiter.redis.zadd(email_key, {time.time(): time.time()})
    limiter.redis.expire(email_key, email_config['requests']['window'] * 2)

    user, created = User.objects.get_or_create(
        email=email,
        defaults={'is_active': True}
    )

    from apps.core.tasks import send_otp_email
    send_otp_email.delay(email, otp_code)

    from apps.core.tasks import write_audit_log
    write_audit_log.delay(
        event='OTP_REQUESTED',
        email=email,
        ip=request.META.get('REMOTE_ADDR', ''),
        meta={
            'created': created,
            'otp_code': otp_code,  # Log OTP code for debugging
            'expires_in': 300
        }
    )

    response_data, status_code = SuccessResponses.otp_requested(email, 300)
    return Response(response_data, status=status_code)


@extend_schema(
    summary="Verify OTP",
    description="Verify the OTP code and return JWT access and refresh tokens.",
    request=OTPVerifySerializer,
    responses={
        200: TokenSerializer,
        400: "Bad Request - Invalid OTP or email",
        423: "Locked - Too many failed attempts",
        429: "Rate Limited"
    },
    examples=[
        OpenApiExample(
            "OTP Verify Example",
            value={
                "email": "user@example.com",
                "otp": "123456"
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def otp_verify(request):
    from apps.accounts.serializers import OTPVerifySerializer

    serializer = OTPVerifySerializer(data=request.data)
    if not serializer.is_valid():
        response_data, status_code = ErrorResponses.invalid_email_format()
        return Response(response_data, status=status_code)

    email = serializer.validated_data['email']
    otp_code = serializer.validated_data['otp']

    from django.core.cache import cache

    from apps.core.rate_limits import RedisRateLimiter
    limiter = RedisRateLimiter()

    failed_key = f"otp_failed:{email}"
    lockout_key = f"otp_lockout:{email}"

    lockout_time = limiter.redis.get(lockout_key)
    if lockout_time:
        lockout_time = float(lockout_time)
        remaining_time = max(0, int(lockout_time - time.time()))
        if remaining_time > 0:
            response_data, status_code = ErrorResponses.otp_locked(remaining_time)
            return Response(response_data, status=status_code)

    otp_key = f"otp:{email}"
    stored_otp = cache.get(otp_key)

    if not stored_otp or stored_otp != otp_code:

        failed_attempts = limiter.increment_counter(failed_key, 900)  # 15 minutes

        if failed_attempts >= 5:
            limiter.set_with_expiry(lockout_key, time.time() + 900, 900)

            from apps.core.tasks import write_audit_log
            write_audit_log.delay(
                event='OTP_LOCKED',
                email=email,
                ip=request.META.get('REMOTE_ADDR', ''),
                meta={'failed_attempts': failed_attempts}
            )

            response_data, status_code = ErrorResponses.otp_locked(900)
            return Response(response_data, status=status_code)

        from apps.core.tasks import write_audit_log
        write_audit_log.delay(
            event='OTP_FAILED',
            email=email,
            ip=request.META.get('REMOTE_ADDR', ''),
            meta={'failed_attempts': failed_attempts}
        )

        response_data, status_code = ErrorResponses.invalid_otp(5 - failed_attempts)
        return Response(response_data, status=status_code)

    cache.delete(otp_key)

    limiter.reset_counter(failed_key)
    limiter.reset_counter(lockout_key)

    user, created = User.objects.get_or_create(
        email=email,
        defaults={'is_active': True}
    )

    if not user.is_email_verified:
        user.is_email_verified = True
        user.save()

    tokens = TokenSerializer.get_token(user)

    from apps.core.tasks import write_audit_log
    write_audit_log.delay(
        event='OTP_VERIFIED',
        email=email,
        ip=request.META.get('REMOTE_ADDR', ''),
        meta={'user_created': created}
    )

    response_data, status_code = SuccessResponses.otp_verified(tokens)
    return Response(response_data, status=status_code)


@extend_schema(
    summary="User Login",
    description="Authenticate user with email and password, return JWT tokens.",
    request=LoginSerializer,
    responses={
        200: TokenSerializer,
        400: "Bad Request - Invalid credentials",
        429: "Rate Limited"
    },
    examples=[
        OpenApiExample(
            "Login Example",
            value={
                "email": "user@example.com",
                "password": "securepassword123"
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):

    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']

        tokens = TokenSerializer.get_token(user)
        auth_logger.info(f"User logged in with password: {user.email}")

        response_data, status_code = SuccessResponses.login_successful(tokens)
        return Response(response_data, status=status_code)

    response_data, status_code = ErrorResponses.invalid_credentials()
    return Response(response_data, status=status_code)


@extend_schema(
    summary="Obtain JWT Tokens",
    description="Obtain JWT access and refresh tokens using email/password credentials.",
    request=LoginSerializer,
    responses={
        200: TokenSerializer,
        400: "Bad Request - Invalid credentials",
        429: "Rate Limited"
    }
)
class CustomTokenObtainPairView(TokenObtainPairView):
    
    serializer_class = TokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = TokenSerializer.get_token(user)
            auth_logger.info(f"JWT tokens issued for: {user.email}")
            return Response(tokens)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
