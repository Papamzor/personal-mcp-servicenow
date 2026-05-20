"""OAuth-domain exception hierarchy."""
from __future__ import annotations


class ServiceNowOAuthError(Exception):
    """Base exception for ServiceNow OAuth operations."""


class ServiceNowAuthenticationError(ServiceNowOAuthError):
    """Exception raised when authentication fails."""


class ServiceNowConnectionError(ServiceNowOAuthError):
    """Exception raised when connection to ServiceNow fails."""


class ServiceNowAuthorizationError(ServiceNowOAuthError):
    """Exception raised when authorization is denied."""
