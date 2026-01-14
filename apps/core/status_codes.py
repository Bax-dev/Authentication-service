
from rest_framework import status as drf_status


HTTP_200_OK = drf_status.HTTP_200_OK
HTTP_201_CREATED = drf_status.HTTP_201_CREATED
HTTP_202_ACCEPTED = drf_status.HTTP_202_ACCEPTED
HTTP_400_BAD_REQUEST = drf_status.HTTP_400_BAD_REQUEST
HTTP_401_UNAUTHORIZED = drf_status.HTTP_401_UNAUTHORIZED
HTTP_403_FORBIDDEN = drf_status.HTTP_403_FORBIDDEN
HTTP_404_NOT_FOUND = drf_status.HTTP_404_NOT_FOUND
HTTP_423_LOCKED = 423 
HTTP_429_TOO_MANY_REQUESTS = drf_status.HTTP_429_TOO_MANY_REQUESTS
HTTP_500_INTERNAL_SERVER_ERROR = drf_status.HTTP_500_INTERNAL_SERVER_ERROR


class ErrorCodes:
    INVALID_REQUEST = "INVALID_REQUEST"
    SERVER_ERROR = "SERVER_ERROR"

    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    EMAIL_NOT_VERIFIED = "EMAIL_NOT_VERIFIED"

    INVALID_OTP = "INVALID_OTP"
    OTP_EXPIRED = "OTP_EXPIRED"
    OTP_LOCKED = "OTP_LOCKED"
    OTP_NOT_FOUND = "OTP_NOT_FOUND"

    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    INVALID_EMAIL_FORMAT = "INVALID_EMAIL_FORMAT"
    INVALID_OTP_FORMAT = "INVALID_OTP_FORMAT"
    PASSWORDS_DO_NOT_MATCH = "PASSWORDS_DO_NOT_MATCH"


class SuccessResponses:
    @staticmethod
    def otp_requested(email: str, expires_in: int = 300):
        if expires_in == 300:
            expires_in_formatted = "5 minutes"
        else:
            minutes = expires_in // 60
            expires_in_formatted = f"{minutes} minutes"

        return {
            "success": True,
            "message": "OTP sent to your email",
            "email": email,
            "expires_in": expires_in_formatted
        }, HTTP_202_ACCEPTED

    @staticmethod
    def otp_verified(tokens: dict):
        """Response for successful OTP verification."""
        return {
            "success": True,
            "message": "OTP verified successfully",
            "tokens": tokens
        }, HTTP_200_OK

    @staticmethod
    def user_registered(email: str):
        """Response for successful user registration."""
        return {
            "success": True,
            "message": "User registered successfully",
            "email": email
        }, HTTP_201_CREATED

    @staticmethod
    def login_successful(tokens: dict):
        """Response for successful login."""
        return {
            "success": True,
            "message": "Login successful",
            "tokens": tokens
        }, HTTP_200_OK

    @staticmethod
    def profile_updated():
        """Response for successful profile update."""
        return {
            "success": True,
            "message": "Profile updated successfully"
        }, HTTP_200_OK


class ErrorResponses:
    """Standard error response templates."""

    @staticmethod
    def invalid_request(message: str = "Invalid request data"):
        """Generic invalid request error."""
        return {
            "success": False,
            "error": ErrorCodes.INVALID_REQUEST,
            "message": message
        }, HTTP_400_BAD_REQUEST

    @staticmethod
    def invalid_email_format():
        """Invalid email format error."""
        return {
            "success": False,
            "error": ErrorCodes.INVALID_EMAIL_FORMAT,
            "message": "Invalid email format"
        }, HTTP_400_BAD_REQUEST

    @staticmethod
    def invalid_otp_format():
        """Invalid OTP format error."""
        return {
            "success": False,
            "error": ErrorCodes.INVALID_OTP_FORMAT,
            "message": "OTP must be 6 digits"
        }, HTTP_400_BAD_REQUEST

    @staticmethod
    def invalid_credentials():
        """Invalid login credentials error."""
        return {
            "success": False,
            "error": ErrorCodes.INVALID_CREDENTIALS,
            "message": "Invalid email or password"
        }, HTTP_400_BAD_REQUEST

    @staticmethod
    def invalid_otp(remaining_attempts: int = None):
        """Invalid OTP error."""
        response = {
            "success": False,
            "error": ErrorCodes.INVALID_OTP,
            "message": "Invalid OTP code"
        }
        if remaining_attempts is not None:
            response["remaining_attempts"] = remaining_attempts
        return response, HTTP_400_BAD_REQUEST

    @staticmethod
    def otp_locked(unlock_in: int):
        if unlock_in < 60:
            unlock_in_formatted = f"{unlock_in} seconds"
        elif unlock_in < 3600:
            minutes = unlock_in // 60
            seconds = unlock_in % 60
            if seconds == 0:
                unlock_in_formatted = f"{minutes} minutes"
            else:
                unlock_in_formatted = f"{minutes} minutes {seconds} seconds"
        else:
            hours = unlock_in // 3600
            minutes = (unlock_in % 3600) // 60
            if minutes == 0:
                unlock_in_formatted = f"{hours} hours"
            else:
                unlock_in_formatted = f"{hours} hours {minutes} minutes"

        return {
            "success": False,
            "error": ErrorCodes.OTP_LOCKED,
            "message": f"Account locked due to too many failed attempts. Try again in {unlock_in_formatted}.",
            "unlock_in": unlock_in_formatted
        }, HTTP_423_LOCKED

    @staticmethod
    def rate_limit_exceeded(message: str, retry_after: int, limit_type: str = None):
        if retry_after < 60:
            retry_after_formatted = f"{retry_after} seconds"
        elif retry_after < 3600:
            minutes = retry_after // 60
            seconds = retry_after % 60
            if seconds == 0:
                retry_after_formatted = f"{minutes} minutes"
            else:
                retry_after_formatted = f"{minutes} minutes {seconds} seconds"
        else:
            hours = retry_after // 3600
            minutes = (retry_after % 3600) // 60
            if minutes == 0:
                retry_after_formatted = f"{hours} hours"
            else:
                retry_after_formatted = f"{hours} hours {minutes} minutes"

        response = {
            "success": False,
            "error": ErrorCodes.RATE_LIMIT_EXCEEDED,
            "message": message,
            "retry_after": retry_after_formatted
        }
        if limit_type:
            response["limit_type"] = limit_type
        return response, HTTP_429_TOO_MANY_REQUESTS

    @staticmethod
    def user_not_found():
        """User not found error."""
        return {
            "success": False,
            "error": "USER_NOT_FOUND",
            "message": "User with this email does not exist"
        }, HTTP_400_BAD_REQUEST

    @staticmethod
    def unauthorized(message: str = "Authentication required"):
        return {
            "success": False,
            "error": "UNAUTHORIZED",
            "message": message
        }, HTTP_401_UNAUTHORIZED

    @staticmethod
    def forbidden(message: str = "Access denied"):
        return {
            "success": False,
            "error": "FORBIDDEN",
            "message": message
        }, HTTP_403_FORBIDDEN

    @staticmethod
    def server_error(message: str = "Internal server error"):
        return {
            "success": False,
            "error": ErrorCodes.SERVER_ERROR,
            "message": message
        }, HTTP_500_INTERNAL_SERVER_ERROR


# Response Headers
class ResponseHeaders:
    @staticmethod
    def retry_after(seconds: int):
        return {"Retry-After": str(seconds)}

    @staticmethod
    def rate_limit_info(limit: int, remaining: int, reset_time: int):
        """Rate limit headers."""
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time)
        }
