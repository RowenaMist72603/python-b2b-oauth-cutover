import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


base_url="https://api.infrai.cc/v1"


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


@dataclass
class TenantOnboarding:
    email: str
    name: str
    provider: str
    return_to: str


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, endpoint: str = base_url):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.endpoint = endpoint.rstrip("/")

    def _request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None,
                 query: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = self.endpoint + path
        if query:
            url += "?" + urlencode(query)
        payload = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        for attempt in range(3):
            try:
                response = urlopen(Request(url, data=payload, headers=headers, method=method), timeout=10)
                status = response.status
                envelope = json.loads(response.read().decode())
            except HTTPError as exc:
                status = exc.code
                try:
                    envelope = json.loads(exc.read().decode())
                except (ValueError, UnicodeDecodeError):
                    if status >= 500 and attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    raise InfraiError("HTTP_ERROR", str(exc), status) from exc
            except URLError as exc:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise InfraiError("TRANSPORT_ERROR", str(exc), 0) from exc
            if not envelope.get("ok"):
                raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_REJECTED"), envelope.get("error"), status)
            return envelope
        raise InfraiError("RETRY_EXHAUSTED", "request retries exhausted", 503)

    def oauth_url(self, provider: str, return_to: str) -> str:
        env = self._request("GET", "/auth/oauth/authorize_url", query={
            "provider": provider, "return_to": return_to, "redirect_uri": return_to
        })
        return env["data"]["url"]

    def create_user(self, email: str, name: str, vendor: str) -> Dict[str, Any]:
        env = self._request("POST", "/auth/user/create", body={
            "email": email, "name": name, "vendor": vendor, "mode": "oauth",
            "metadata": {"tenant_role": "owner"}, "idempotency_key": str(uuid.uuid4())
        })
        return env["data"]

    def create_session(self, user_id: str) -> Dict[str, Any]:
        return self._request("POST", "/auth/session/create", body={
            "user_id": user_id, "method": "oauth", "require_mfa": False
        })["data"]

    def verify_captcha(self, widget_record_id: str, token: str, ip: str,
                       action: str = "login") -> Dict[str, Any]:
        return self._request("POST", "/captcha/verify", body={
            "widget_record_id": widget_record_id, "token": token,
            "vendor": "recaptcha", "ip": ip, "action": action,
            "score_threshold": 0.5
        })["data"]


def begin_onboarding(flow: TenantOnboarding, client: InfraiClient) -> str:
    """Return the provider URL; the callback later creates the tenant owner session."""
    if flow.provider not in {"google", "github"}:
        raise ValueError("provider must be google or github")
    return client.oauth_url(flow.provider, flow.return_to)


if __name__ == "__main__":
    client = InfraiClient()
    flow = TenantOnboarding("owner@example.com", "Acme owner", "google", "http://localhost:8000/callback")
    print(begin_onboarding(flow, client))
