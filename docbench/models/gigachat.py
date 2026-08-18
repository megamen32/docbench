"""GigaChat REST adapter with OAuth access-token refresh and CA-bundle support."""
from __future__ import annotations

import time
import uuid

import requests

from .openai_compat import OpenAICompatRunner


class GigaChatRunner(OpenAICompatRunner):
    """Use the long-lived authorization key only to mint a short-lived token.

    The token is kept in process memory and refreshed before it expires.  The
    provider needs the Russian Trusted Root CA; callers may set the configured
    CA bundle path, or rely on an OS trust store that already contains it.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._access_token: str | None = None
        self._access_token_expires_at = 0.0
        self._verify = self.spec.ca_bundle or True

    def _request_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token()}",
                "Content-Type": "application/json",
                "Accept": "application/json"}

    def _request_options(self) -> dict[str, object]:
        return {"verify": self._verify}

    def _token(self) -> str:
        # Refresh with one minute of headroom, without persisting the token.
        if self._access_token and time.time() < self._access_token_expires_at - 60:
            return self._access_token
        if not self.spec.oauth_url or not self.spec.oauth_scope:
            raise RuntimeError(f"{self.model_key}: incomplete GigaChat OAuth configuration")
        try:
            response = requests.post(
                self.spec.oauth_url,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "RqUID": str(uuid.uuid4()),
                    "Authorization": f"Basic {self._api_key}",
                },
                data={"scope": self.spec.oauth_scope},
                timeout=self.timeout,
                verify=self._verify,
            )
        except requests.exceptions.SSLError as exc:
            hint = (f"; set {self.spec.ca_bundle_env} to the Russian Trusted Root CA bundle"
                    if self.spec.ca_bundle_env else "")
            raise RuntimeError(f"{self.model_key}: GigaChat TLS verification failed{hint}") from exc
        if response.status_code != 200:
            raise RuntimeError(f"{self.model_key}: GigaChat OAuth HTTP {response.status_code}")
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise RuntimeError(f"{self.model_key}: GigaChat OAuth response has no access_token")
        expires_at = payload.get("expires_at")
        try:
            expiry = float(expires_at)
            # The documented endpoint returns Unix seconds; tolerate millis.
            if expiry > 10_000_000_000:
                expiry /= 1000
        except (TypeError, ValueError):
            expiry = time.time() + 25 * 60
        self._access_token = token
        self._access_token_expires_at = expiry
        return token
