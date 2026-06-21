"""Shared pytest fixtures.

The v4.2 connection-pooling refactor introduced a process-wide pooled
``httpx.AsyncClient`` cached in ``oauth.http_pool._pooled_client``. Tests
patch ``oauth.singleton.httpx.AsyncClient`` per test; without resetting the
cache between tests, one test's mock client would leak into the next (or a
real client built during an unmocked test would persist). This autouse
fixture resets the pool before every test so each starts from a clean slate.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_http_pool():
    """Drop the cached pooled client before and after each test."""
    import oauth.http_pool as http_pool

    http_pool._pooled_client = None
    yield
    http_pool._pooled_client = None
