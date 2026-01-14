
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_email_task(subject, message, recipient_list, from_email=None):

    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False,
    )
    return f"Email sent to {recipient_list}"


@shared_task
def send_otp_email(email, otp):
    print(f"SENDING OTP EMAIL:")
    print(f"To: {email}")
    print(f"Subject: Your OTP Code")
    print(f"Body: Your verification code is: {otp}")
    print(f"This code will expire in 5 minutes.")
    print("-" * 50)

    return f"OTP email sent to {email}"


@shared_task
def write_audit_log(event, email, ip, meta):

    from apps.audit.models import AuditLog

    try:
        AuditLog.objects.create(
            event=event,
            email=email,
            ip_address=ip or '',
            user_agent='',
            metadata=meta or {}
        )
        print(f"AUDIT LOG: {event} - {email}")
        return f"Audit log written: {event}"
    except Exception as e:
        print(f"Failed to write audit log: {e}")
        return f"Failed to write audit log: {e}"


@shared_task
def log_system_event(event_type, message, metadata=None):
    print(f"System Event: {event_type} - {message}")
    if metadata:
        print(f"Metadata: {metadata}")

    return f"Logged event: {event_type}"


@shared_task
def cleanup_expired_data():
    print("Running cleanup task...")
    return "Cleanup completed"
