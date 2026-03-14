"""Tests for exceptions."""

import pytest
from sayd_ai.exceptions import (
    SaydError,
    AuthenticationError,
    RateLimitError,
    SubscriptionError,
    SessionError,
)


class TestExceptions:
    def test_sayd_error(self):
        err = SaydError("something broke", 500)
        assert str(err) == "something broke"
        assert err.status_code == 500
        assert err.message == "something broke"

    def test_sayd_error_no_status(self):
        err = SaydError("oops")
        assert err.status_code is None

    def test_authentication_error(self):
        err = AuthenticationError()
        assert err.status_code == 401
        assert "API key" in str(err)

    def test_authentication_error_custom(self):
        err = AuthenticationError("Token expired")
        assert str(err) == "Token expired"
        assert err.status_code == 401

    def test_rate_limit_error(self):
        err = RateLimitError()
        assert err.status_code == 429
        assert err.retry_after is None

    def test_rate_limit_error_with_retry(self):
        err = RateLimitError(retry_after=30.0)
        assert err.retry_after == 30.0

    def test_subscription_error(self):
        err = SubscriptionError()
        assert err.status_code == 403

    def test_session_error_inherits(self):
        err = SessionError("session died")
        assert isinstance(err, SaydError)

    def test_all_inherit_from_sayd_error(self):
        assert issubclass(AuthenticationError, SaydError)
        assert issubclass(RateLimitError, SaydError)
        assert issubclass(SubscriptionError, SaydError)
        assert issubclass(SessionError, SaydError)
