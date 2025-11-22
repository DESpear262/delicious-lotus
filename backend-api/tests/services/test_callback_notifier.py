"""
Unit tests for Callback Notifier Service.

Tests HTTP callbacks, retry logic, signature verification, and error handling.
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from services.callback_notifier import (
    CallbackNotifier,
)


class TestCallbackNotifier:
    """Test cases for CallbackNotifier."""

    @pytest.fixture
    def notifier(self):
        """Create CallbackNotifier instance for testing."""
        with patch("services.callback_notifier.get_settings") as mock_settings:
            mock_settings.return_value.webhook_secret = None

            return CallbackNotifier(
                max_retries=3,
                timeout=30.0,
                base_retry_delay=0.1,  # Shorter for testing
            )

    @pytest.fixture
    def notifier_with_secret(self):
        """Create CallbackNotifier with webhook secret."""
        with patch("services.callback_notifier.get_settings") as mock_settings:
            mock_settings.return_value.webhook_secret = "test-secret"

            return CallbackNotifier(
                webhook_secret="test-secret-key",
                max_retries=3,
                timeout=30.0,
                base_retry_delay=0.1,
            )

    def test_notifier_initialization(self, notifier):
        """Test notifier initializes correctly."""
        assert notifier.max_retries == 3
        assert notifier.timeout == 30.0
        assert notifier.base_retry_delay == 0.1

    @patch("httpx.Client")
    def test_send_callback_success(self, mock_client_class, notifier):
        """Test successful callback delivery on first attempt."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.post.return_value = mock_response

        mock_client_class.return_value = mock_client

        # Send callback
        payload = {"status": "completed", "result": "success"}
        result = notifier.send_callback(
            callback_url="https://example.com/callback",
            payload=payload,
            request_id="req-123",
        )

        assert result.success is True
        assert len(result.attempts) == 1
        assert result.attempts[0].success is True
        assert result.attempts[0].status_code == 200
        assert result.final_status_code == 200

    @patch("httpx.Client")
    def test_send_callback_retry_then_success(self, mock_client_class, notifier):
        """Test callback succeeds after retry."""
        # First call fails, second succeeds
        call_count = [0]

        def post_side_effect(*args, **kwargs):
            call_count[0] += 1
            response = MagicMock()
            if call_count[0] == 1:
                response.status_code = 500
                response.text = "Internal Server Error"
            else:
                response.status_code = 200
                response.text = "OK"
            return response

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.post.side_effect = post_side_effect

        mock_client_class.return_value = mock_client

        payload = {"status": "completed"}
        result = notifier.send_callback(
            callback_url="https://example.com/callback",
            payload=payload,
        )

        assert result.success is True
        assert len(result.attempts) == 2
        assert result.attempts[0].success is False
        assert result.attempts[0].status_code == 500
        assert result.attempts[1].success is True
        assert result.attempts[1].status_code == 200

    @patch("httpx.Client")
    def test_send_callback_all_attempts_fail(self, mock_client_class, notifier):
        """Test callback fails after all retry attempts."""
        # All attempts fail
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.post.return_value = mock_response

        mock_client_class.return_value = mock_client

        payload = {"status": "completed"}
        result = notifier.send_callback(
            callback_url="https://example.com/callback",
            payload=payload,
        )

        assert result.success is False
        assert len(result.attempts) == 3  # max_retries
        assert all(not attempt.success for attempt in result.attempts)
        assert result.error is not None
        assert "Failed after 3 attempts" in result.error

    @patch("httpx.Client")
    def test_send_callback_timeout(self, mock_client_class, notifier):
        """Test timeout handling."""
        import httpx

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.post.side_effect = httpx.TimeoutException("Request timeout")

        mock_client_class.return_value = mock_client

        payload = {"status": "completed"}
        result = notifier.send_callback(
            callback_url="https://example.com/callback",
            payload=payload,
        )

        assert result.success is False
        assert len(result.attempts) == 3
        assert all("timed out" in attempt.error.lower() for attempt in result.attempts)

    @patch("httpx.Client")
    def test_send_callback_http_error(self, mock_client_class, notifier):
        """Test HTTP error handling."""
        import httpx

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.post.side_effect = httpx.HTTPError("Connection failed")

        mock_client_class.return_value = mock_client

        payload = {"status": "completed"}
        result = notifier.send_callback(
            callback_url="https://example.com/callback",
            payload=payload,
        )

        assert result.success is False
        assert all("HTTP error" in attempt.error for attempt in result.attempts)

    @patch("httpx.Client")
    def test_send_callback_with_signature(self, mock_client_class, notifier_with_secret):
        """Test callback with webhook signature."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.post.return_value = mock_response

        mock_client_class.return_value = mock_client

        payload = {"status": "completed"}
        result = notifier_with_secret.send_callback(
            callback_url="https://example.com/callback",
            payload=payload,
        )

        assert result.success is True

        # Verify signature was included in headers
        call_args = mock_client.post.call_args
        headers = call_args.kwargs["headers"]
        assert "X-Webhook-Signature" in headers
        assert headers["X-Webhook-Signature"].startswith("sha256=")

    def test_generate_signature(self, notifier_with_secret):
        """Test signature generation."""
        payload = {"key": "value", "number": 123}
        signature = notifier_with_secret._generate_signature(payload)

        assert signature.startswith("sha256=")
        assert len(signature) == 71  # "sha256=" + 64 hex chars

    def test_verify_signature_valid(self):
        """Test signature verification with valid signature."""
        secret = "test-secret"
        payload = {"key": "value"}

        # Generate signature
        notifier = CallbackNotifier(webhook_secret=secret)
        signature = notifier._generate_signature(payload)

        # Verify signature
        is_valid = CallbackNotifier.verify_signature(payload, signature, secret)
        assert is_valid is True

    def test_verify_signature_invalid(self):
        """Test signature verification with invalid signature."""
        secret = "test-secret"
        payload = {"key": "value"}

        # Invalid signature
        invalid_signature = "sha256=invalid_signature_hash"

        is_valid = CallbackNotifier.verify_signature(payload, invalid_signature, secret)
        assert is_valid is False

    def test_verify_signature_wrong_format(self):
        """Test signature verification with wrong format."""
        secret = "test-secret"
        payload = {"key": "value"}

        # Wrong format (no "sha256=" prefix)
        wrong_format = "just_a_hash"

        is_valid = CallbackNotifier.verify_signature(payload, wrong_format, secret)
        assert is_valid is False

    def test_verify_signature_tampered_payload(self):
        """Test signature verification with tampered payload."""
        secret = "test-secret"
        original_payload = {"key": "value"}

        # Generate signature for original
        notifier = CallbackNotifier(webhook_secret=secret)
        signature = notifier._generate_signature(original_payload)

        # Tamper with payload
        tampered_payload = {"key": "different_value"}

        # Verification should fail
        is_valid = CallbackNotifier.verify_signature(tampered_payload, signature, secret)
        assert is_valid is False

    def test_calculate_retry_delay(self, notifier):
        """Test exponential backoff calculation."""
        # First retry
        delay1 = notifier._calculate_retry_delay(0)
        assert 0.075 <= delay1 <= 0.125  # 0.1 ± 25%

        # Second retry (should be ~2x)
        delay2 = notifier._calculate_retry_delay(1)
        assert 0.15 <= delay2 <= 0.25  # 0.2 ± 25%

        # Third retry (should be ~4x)
        delay3 = notifier._calculate_retry_delay(2)
        assert 0.3 <= delay3 <= 0.5  # 0.4 ± 25%

    def test_retry_delay_max_cap(self):
        """Test that retry delay is capped at 60 seconds."""
        notifier = CallbackNotifier(base_retry_delay=30.0)

        # High retry count should be capped
        delay = notifier._calculate_retry_delay(10)
        assert delay <= 60.0

    @patch("httpx.Client")
    def test_send_processing_complete_callback(self, mock_client_class, notifier):
        """Test sending processing complete callback."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.post.return_value = mock_response

        mock_client_class.return_value = mock_client

        results = [
            {"clip_id": "clip-1", "status": "completed", "url": "https://example.com/1.mp4"},
            {"clip_id": "clip-2", "status": "completed", "url": "https://example.com/2.mp4"},
            {"clip_id": "clip-3", "status": "failed", "error": "Processing failed"},
        ]

        result = notifier.send_processing_complete_callback(
            callback_url="https://example.com/callback",
            request_id="req-123",
            results=results,
        )

        assert result.success is True

        # Verify payload structure
        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]

        assert payload["request_id"] == "req-123"
        assert payload["total_successful"] == 2
        assert payload["total_failed"] == 1
        assert len(payload["results"]) == 3
        assert "completed_at" in payload

    @patch("httpx.Client")
    def test_callback_includes_request_id_header(self, mock_client_class, notifier):
        """Test that request ID is included in headers."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.post.return_value = mock_response

        mock_client_class.return_value = mock_client

        payload = {"status": "completed"}
        result = notifier.send_callback(
            callback_url="https://example.com/callback",
            payload=payload,
            request_id="req-456",
        )

        assert result.success is True

        # Verify request ID header
        call_args = mock_client.post.call_args
        headers = call_args.kwargs["headers"]
        assert headers["X-Request-ID"] == "req-456"

    @patch("httpx.Client")
    def test_callback_retry_timing(self, mock_client_class, notifier):
        """Test that retries happen with proper delay."""
        # All attempts fail to test retry timing
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.post.return_value = mock_response

        mock_client_class.return_value = mock_client

        start_time = time.time()

        payload = {"status": "completed"}
        result = notifier.send_callback(
            callback_url="https://example.com/callback",
            payload=payload,
        )

        elapsed_time = time.time() - start_time

        # Should have taken at least the retry delays
        # (0.1 + 0.2 with jitter ≈ 0.3+ seconds minimum)
        assert elapsed_time >= 0.2  # At least some delay
        assert result.success is False
        assert len(result.attempts) == 3

    @patch("httpx.Client")
    def test_callback_with_various_status_codes(self, mock_client_class, notifier):
        """Test handling of various HTTP status codes."""
        status_codes = [200, 201, 204, 400, 404, 500, 503]

        for status_code in status_codes:
            mock_response = MagicMock()
            mock_response.status_code = status_code
            mock_response.text = f"Status {status_code}"

            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response

            mock_client_class.return_value = mock_client

            payload = {"test": "data"}
            result = notifier.send_callback(
                callback_url="https://example.com/callback",
                payload=payload,
            )

            # 2xx should succeed, others should fail
            if 200 <= status_code < 300:
                assert result.success is True
                assert len(result.attempts) == 1
            else:
                assert result.success is False
                # Should retry for non-2xx
                assert len(result.attempts) == notifier.max_retries
