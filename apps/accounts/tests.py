from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User
from unittest.mock import patch


class OTPAuthenticationTestCase(APITestCase):

    def setUp(self):

        self.test_email = "test@example.com"
        self.otp_request_url = reverse('auth:otp_request')
        self.otp_verify_url = reverse('auth:otp_verify')
        self.audit_logs_url = reverse('audit:audit-log-list')

    def test_otp_request_success(self):
        """Test successful OTP request."""
        data = {'email': self.test_email}
        response = self.client.post(self.otp_request_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'OTP sent to your email')
        self.assertEqual(response.data['email'], self.test_email)
        self.assertEqual(response.data['expires_in'], 300)

    def test_otp_request_invalid_email(self):
        data = {'email': 'invalid-email'}
        response = self.client.post(self.otp_request_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'INVALID_EMAIL_FORMAT')

    def test_otp_verify_invalid_format(self):
        """Test OTP verify with invalid format."""
        data = {'email': self.test_email, 'otp': 'invalid'}
        response = self.client.post(self.otp_verify_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'INVALID_OTP_FORMAT')

    def test_audit_logs_requires_authentication(self):
        """Test that audit logs require authentication."""
        response = self.client.get(self.audit_logs_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('apps.core.tasks.send_otp_email.delay')
    @patch('apps.core.tasks.write_audit_log.delay')
    def test_otp_request_calls_celery_tasks(self, mock_write_audit_log, mock_send_otp_email):
        """Test that OTP request calls the correct Celery tasks."""
        data = {'email': self.test_email}
        response = self.client.post(self.otp_request_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        mock_send_otp_email.assert_called_once()
        mock_write_audit_log.assert_called_once()

        mock_send_otp_email.assert_called_with(self.test_email, mock_send_otp_email.call_args[0][1])
        audit_call_args = mock_write_audit_log.call_args[0]
        self.assertEqual(audit_call_args[0], 'OTP_REQUESTED')  # event
        self.assertEqual(audit_call_args[1], self.test_email)  # email
