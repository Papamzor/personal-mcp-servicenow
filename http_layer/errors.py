"""Typed read-path failures for the ServiceNow HTTP layer (v4.4 Tier 0.3).

Before this module, a GET that failed returned ``None`` — indistinguishable
from "the table has no matching rows". Consumers then reported HTTP 200 +
``{"result": []}`` and a 30-second timeout with the same "not found" message,
so a transport failure silently looked like a business answer.

``ServiceNowRequestError`` carries the three things a consumer needs to react
correctly:

    code        one of the seven ``ErrorCode`` values — the whole vocabulary,
                nothing else. Consumers switch on this, never on message text.
    status_code the HTTP status when there was one, else ``None``.
    retryable   whether retrying the identical request could plausibly succeed.

Classification lives here rather than in the dispatcher so the mapping is
unit-testable without an HTTP stack, and so every consumer migrated in PRs 2-7
reads the same table.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

import httpx

from oauth.exceptions import (
    ServiceNowAuthenticationError,
    ServiceNowAuthorizationError,
    ServiceNowConnectionError,
)


class ErrorCode:
    """The complete failure vocabulary. Adding a code is a contract change."""

    VALIDATION = "VALIDATION"
    NOT_FOUND = "NOT_FOUND"
    AUTH = "AUTH"
    FORBIDDEN = "FORBIDDEN"
    TIMEOUT = "TIMEOUT"
    HTTP = "HTTP"
    INTERNAL = "INTERNAL"


ALL_ERROR_CODES = frozenset({
    ErrorCode.VALIDATION,
    ErrorCode.NOT_FOUND,
    ErrorCode.AUTH,
    ErrorCode.FORBIDDEN,
    ErrorCode.TIMEOUT,
    ErrorCode.HTTP,
    ErrorCode.INTERNAL,
})

# Message templates. Kept here rather than in constants.py because constants.py
# is import-cycle-free of httpx and these are HTTP-layer diagnostics, not
# user-facing tool copy.
MSG_HTTP_STATUS = "ServiceNow returned HTTP {status}"
MSG_TIMEOUT = "ServiceNow request timed out"
MSG_TRANSPORT = "Could not reach ServiceNow ({detail})"
MSG_DECODE = "ServiceNow returned a response that is not valid JSON"
MSG_OAUTH_AUTH = "ServiceNow OAuth authentication failed: {detail}"
MSG_OAUTH_FORBIDDEN = "ServiceNow OAuth authorization denied: {detail}"
MSG_OAUTH_CONNECTION = "Could not reach the ServiceNow OAuth endpoint: {detail}"
MSG_INTERNAL = "Unexpected {exc_type} during ServiceNow request: {detail}"


class ServiceNowRequestError(Exception):
    """A ServiceNow request failed. Never raised to mean "no matching rows"."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: Optional[int] = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable

    def to_error_dict(self) -> dict[str, Any]:
        """The §3.1 failure shape. Consumers return this straight to the client."""
        return {"error": {"code": self.code, "message": self.message}}

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"ServiceNowRequestError(code={self.code!r}, status_code={self.status_code!r}, "
            f"retryable={self.retryable!r}, message={self.message!r})"
        )


# HTTP status -> (code, retryable). Anything absent falls back to HTTP, with
# 5xx treated as retryable and other 4xx as not.
_STATUS_MAP: dict[int, tuple[str, bool]] = {
    400: (ErrorCode.VALIDATION, False),
    401: (ErrorCode.AUTH, False),
    403: (ErrorCode.FORBIDDEN, False),
    404: (ErrorCode.NOT_FOUND, False),
    408: (ErrorCode.TIMEOUT, True),
    429: (ErrorCode.HTTP, True),
}


def _from_status_error(exc: httpx.HTTPStatusError) -> ServiceNowRequestError:
    status = exc.response.status_code
    code, retryable = _STATUS_MAP.get(status, (ErrorCode.HTTP, status >= 500))
    return ServiceNowRequestError(
        code,
        MSG_HTTP_STATUS.format(status=status),
        status_code=status,
        retryable=retryable,
    )


def _from_timeout(exc: BaseException) -> ServiceNowRequestError:
    return ServiceNowRequestError(ErrorCode.TIMEOUT, MSG_TIMEOUT, retryable=True)


def _from_transport(exc: BaseException) -> ServiceNowRequestError:
    """Connect/DNS/read errors. Not a timeout, but the same retry advice."""
    return ServiceNowRequestError(
        ErrorCode.HTTP,
        MSG_TRANSPORT.format(detail=type(exc).__name__),
        retryable=True,
    )


def _from_decode(exc: BaseException) -> ServiceNowRequestError:
    """A 200 whose body will not parse is a server-side defect, not a retry."""
    return ServiceNowRequestError(ErrorCode.INTERNAL, MSG_DECODE)


def _from_oauth_auth(exc: BaseException) -> ServiceNowRequestError:
    """Bad client credentials at the token endpoint — same meaning as a 401."""
    return ServiceNowRequestError(ErrorCode.AUTH, MSG_OAUTH_AUTH.format(detail=exc))


def _from_oauth_forbidden(exc: BaseException) -> ServiceNowRequestError:
    return ServiceNowRequestError(ErrorCode.FORBIDDEN, MSG_OAUTH_FORBIDDEN.format(detail=exc))


def _from_oauth_connection(exc: BaseException) -> ServiceNowRequestError:
    return ServiceNowRequestError(
        ErrorCode.HTTP,
        MSG_OAUTH_CONNECTION.format(detail=exc),
        retryable=True,
    )


# Ordered: the first isinstance match wins, so narrower types come first.
# httpx.TimeoutException subclasses httpx.RequestError, and json.JSONDecodeError
# subclasses ValueError — in both pairs the specific clause must precede the
# general one. httpx.HTTPStatusError is NOT a RequestError subclass (siblings),
# but stays first because a response-level failure carries the most information.
#
# The OAuth clauses matter because a token-endpoint failure means exactly what a
# 401/403 on the table API means. Without them, a wrong client secret surfaced
# as INTERNAL "unexpected error" while the identical semantic failure arriving
# as an httpx 401 mapped to AUTH.
#
# Bare ValueError is deliberately NOT paired with JSONDecodeError: the OAuth
# client raises ValueError("Missing OAuth configuration ...") before any request
# is made, and reporting that as "not valid JSON" sends whoever is fixing their
# .env in precisely the wrong direction. It falls through to INTERNAL, which
# echoes the real message.
_EXC_HANDLERS: tuple[tuple[Any, Callable[[BaseException], ServiceNowRequestError]], ...] = (
    (httpx.HTTPStatusError, _from_status_error),
    ((TimeoutError, httpx.TimeoutException), _from_timeout),
    (httpx.RequestError, _from_transport),
    (json.JSONDecodeError, _from_decode),
    (ServiceNowAuthenticationError, _from_oauth_auth),
    (ServiceNowAuthorizationError, _from_oauth_forbidden),
    (ServiceNowConnectionError, _from_oauth_connection),
)


def classify_read_failure(exc: BaseException) -> ServiceNowRequestError:
    """Map a read-path exception onto the error vocabulary.

    ``TimeoutError`` covers ``anyio.fail_after`` expiry; ``httpx.TimeoutException``
    covers the transport's own deadline. Anything unrecognised becomes INTERNAL
    rather than being guessed at — an unclassified failure must never surface as
    NOT_FOUND, which is the bug this whole tier exists to fix.
    """
    if isinstance(exc, ServiceNowRequestError):
        return exc
    for exc_types, handler in _EXC_HANDLERS:
        if isinstance(exc, exc_types):
            return handler(exc)
    return ServiceNowRequestError(
        ErrorCode.INTERNAL,
        MSG_INTERNAL.format(exc_type=type(exc).__name__, detail=exc),
    )
