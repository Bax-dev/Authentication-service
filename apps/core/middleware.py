
import uuid
import time
from django.utils.deprecation import MiddlewareMixin
from apps.core.logger import system_logger, audit_logger
from apps.audit.models import AuditLog


class RequestLoggingMiddleware(MiddlewareMixin):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())
        request.request_id = request_id

        start_time = time.time()
        system_logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                'request_id': request_id,
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )

        response = self.get_response(request)

        duration = time.time() - start_time
        system_logger.info(
            f"Request completed: {response.status_code} in {duration:.2f}s",
            extra={
                'request_id': request_id,
                'status_code': response.status_code,
                'duration': duration,
            }
        )

        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to create audit logs for sensitive operations.
    """
    AUDIT_PATHS = [
        '/api/accounts/',
        '/api/auth/',
        '/admin/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if self._should_audit(request):
            self._create_audit_log(request, response)

        return response

    def _should_audit(self, request):
        path = request.path
        return any(audit_path in path for audit_path in self.AUDIT_PATHS)

    def _create_audit_log(self, request, response):
        try:
            from apps.core.tasks import write_audit_log

            user_email = request.user.email if request.user.is_authenticated else 'anonymous'

            write_audit_log.delay(
                event=f"{request.method} {request.path}",
                email=user_email,
                ip=self._get_client_ip(request),
                meta={
                    'status_code': response.status_code,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'referer': request.META.get('HTTP_REFERER', ''),
                }
            )
        except Exception as e:
            audit_logger.error(f"Failed to write audit log: {str(e)}")

    def _get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
