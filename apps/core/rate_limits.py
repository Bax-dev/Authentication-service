
import time
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
from apps.core.status_codes import ErrorResponses


class RateLimitExceeded(Exception):
    pass


class RedisRateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm and atomic counters.
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client or cache._cache.get_client()

    def is_rate_limited(self, key, max_requests, window_seconds):
      
        current_time = time.time()
        window_start = current_time - window_seconds

        self.redis.zremrangebyscore(key, 0, window_start)

        request_count = self.redis.zcard(key)

        if request_count >= max_requests:
            return True

        self.redis.zadd(key, {current_time: current_time})

        self.redis.expire(key, window_seconds * 2)

        return False

    def get_remaining_requests(self, key, max_requests, window_seconds):

        current_time = time.time()
        window_start = current_time - window_seconds

        self.redis.zremrangebyscore(key, 0, window_start)

        request_count = self.redis.zcard(key)

        return max(0, max_requests - request_count)

    def get_reset_time(self, key, window_seconds):

        oldest_timestamp = self.redis.zrange(key, 0, 0, withscores=True)
        if oldest_timestamp:
            reset_time = oldest_timestamp[0][1] + window_seconds - time.time()
            return max(0, int(reset_time))
        return 0

    def increment_counter(self, key, expire_seconds=None):

        new_value = self.redis.incr(key)

        if new_value == 1 and expire_seconds:
            self.redis.expire(key, expire_seconds)

        return new_value

    def get_counter(self, key):

        value = self.redis.get(key)
        return int(value) if value else 0

    def reset_counter(self, key):

        self.redis.delete(key)

    def set_with_expiry(self, key, value, expire_seconds):

        return self.redis.setex(key, expire_seconds, value)


class RateLimitMiddleware(MiddlewareMixin):
    RATE_LIMIT_CONFIG = {
        'otp_request': {
            'email': settings.RATE_LIMITS.get('otp_request_email', {'requests': 3, 'window': 600}),
            'ip': settings.RATE_LIMITS.get('otp_request_ip', {'requests': 10, 'window': 3600}),
        },
        'otp_verify': settings.RATE_LIMITS.get('otp_verify', {'requests': 10, 'window': 300}),
        'login': settings.RATE_LIMITS.get('login', {'requests': 10, 'window': 300}),
        'register': settings.RATE_LIMITS.get('register', {'requests': 3, 'window': 3600}),
        'token_refresh': settings.RATE_LIMITS.get('token_refresh', {'requests': 20, 'window': 300}),
    }

    def __init__(self, get_response):
        self.get_response = get_response
        self.limiter = RedisRateLimiter()

    def __call__(self, request):
        endpoint = self._get_endpoint_type(request)

        if endpoint and endpoint in self.RATE_LIMIT_CONFIG:
            config = self.RATE_LIMIT_CONFIG[endpoint]

            if endpoint == 'otp_request':
                email_key = self._get_rate_limit_key(request, 'otp_request', 'email')
                email_config = config['email']
                if self.limiter.is_rate_limited(email_key, email_config['requests'], email_config['window']):
                    reset_time = self.limiter.get_reset_time(email_key, email_config['window'])
                    response_data, status_code = ErrorResponses.rate_limit_exceeded(
                        "Too many OTP requests for this email. Try again later.",
                        reset_time,
                        "email"
                    )
                    return JsonResponse(response_data, status=status_code, headers={'Retry-After': str(reset_time)})

                # Check IP rate limit
                ip_key = self._get_rate_limit_key(request, 'otp_request', 'ip')
                ip_config = config['ip']
                if self.limiter.is_rate_limited(ip_key, ip_config['requests'], ip_config['window']):
                    reset_time = self.limiter.get_reset_time(ip_key, ip_config['window'])
                    response_data, status_code = ErrorResponses.rate_limit_exceeded(
                        "Too many OTP requests from this IP. Try again later.",
                        reset_time,
                        "ip"
                    )
                    return JsonResponse(response_data, status=status_code, headers={'Retry-After': str(reset_time)})

            else:

                key = self._get_rate_limit_key(request, endpoint)
                if self.limiter.is_rate_limited(key, config['requests'], config['window']):
                    reset_time = self.limiter.get_reset_time(key, config['window'])

                    response_data, status_code = ErrorResponses.rate_limit_exceeded(
                        f'Too many requests. Try again in {reset_time} seconds.',
                        reset_time
                    )
                    return JsonResponse(response_data, status=status_code, headers={'Retry-After': str(reset_time)})

        response = self.get_response(request)
        return response

    def _get_endpoint_type(self, request):
        path = request.path

        if '/otp/request/' in path:
            return 'otp_request'
        elif '/otp/verify/' in path:
            return 'otp_verify'
        elif '/login/' in path:
            return 'login'
        elif '/register/' in path:
            return 'register'
        elif '/token/refresh/' in path:
            return 'token_refresh'

        return None

    def _get_rate_limit_key(self, request, endpoint, limit_type=None):

        if limit_type == 'email':

            return f"ratelimit:{endpoint}:email:pending"
        elif limit_type == 'ip':
            identifier = self._get_client_ip(request)
            return f"ratelimit:{endpoint}:ip:{identifier}"
        else:

            if request.user.is_authenticated:
                identifier = request.user.email
            else:
                identifier = self._get_client_ip(request)
            return f"ratelimit:{endpoint}:{identifier}"

    def _get_client_ip(self, request):

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
