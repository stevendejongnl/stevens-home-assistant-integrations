"""Async API client for Dude, Where's My Package?"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class DWMPConnectionError(Exception):
    """Raised when the DWMP instance is unreachable."""


class DWMPAuthError(Exception):
    """Raised when authentication fails (401)."""


class DWMPApiError(Exception):
    """Raised on unexpected API errors."""


class DWMPApiClient:
    """Async client for the DWMP REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        url: str,
        token: str | None = None,
    ) -> None:
        self._session = session
        self._url = url.rstrip("/")
        self._token = token

    @property
    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        auth: bool = True,
    ) -> Any:
        url = f"{self._url}{path}"
        headers = self._headers if auth else {}

        try:
            async with self._session.request(
                method, url, headers=headers, json=json, params=params
            ) as resp:
                if resp.status == 401:
                    raise DWMPAuthError("Authentication failed")
                if resp.status >= 400:
                    text = await resp.text()
                    raise DWMPApiError(
                        f"API error {resp.status}: {text}"
                    )
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise DWMPConnectionError(
                f"Cannot connect to DWMP at {self._url}"
            ) from err

    async def health(self) -> dict:
        """Check DWMP health (no auth required)."""
        return await self._request("GET", "/health", auth=False)

    async def get_token(self, password: str) -> str:
        """Exchange password for a JWT Bearer token."""
        data = await self._request(
            "POST",
            "/api/v1/auth/token",
            json={"password": password},
            auth=False,
        )
        return data["token"]

    async def list_packages(self) -> list[dict]:
        """Get all tracked packages."""
        return await self._request("GET", "/api/v1/packages")

    async def get_package(self, package_id: int) -> dict:
        """Get a single package with its event timeline."""
        return await self._request("GET", f"/api/v1/packages/{package_id}")

    async def get_unread_count(self) -> int:
        """Get the count of unread notifications."""
        data = await self._request("GET", "/api/v1/notifications/unread-count")
        return data["count"]

    async def list_notifications(self, limit: int = 20) -> list[dict]:
        """Get recent notifications."""
        return await self._request(
            "GET", "/api/v1/notifications", params={"limit": limit}
        )
