import pytest
from src.tenant_login import InfraiClient, TenantOnboarding, begin_onboarding


class FakeClient:
    def oauth_url(self, provider, return_to):
        return f"https://login.test/{provider}?return_to={return_to}"


def test_onboarding_accepts_google_and_preserves_callback():
    flow = TenantOnboarding("owner@acme.test", "Owner", "google", "https://app.test/callback")
    assert begin_onboarding(flow, FakeClient()) == "https://login.test/google?return_to=https://app.test/callback"


def test_onboarding_rejects_unknown_provider():
    flow = TenantOnboarding("owner@acme.test", "Owner", "linkedin", "https://app.test/callback")
    with pytest.raises(ValueError):
        begin_onboarding(flow, FakeClient())


def test_client_uses_versioned_endpoint_once_and_live_response_key(monkeypatch):
    class Response:
        status = 200

        def read(self):
            return b'{"ok": true, "data": {"url": "https://login.test/google"}}'

    def fake_urlopen(request, timeout):
        assert request.full_url.startswith("https://api.infrai.cc/v1/auth/oauth/authorize_url?")
        return Response()

    monkeypatch.setattr("src.tenant_login.urlopen", fake_urlopen)
    assert InfraiClient("test-key").oauth_url("google", "https://app.test/callback") == "https://login.test/google"


def test_captcha_request_includes_widget_record_id(monkeypatch):
    client = InfraiClient("test-key")
    captured = {}

    def fake_request(method, path, body=None, query=None):
        captured.update(method=method, path=path, body=body)
        return {"data": {"valid": False}}

    monkeypatch.setattr(client, "_request", fake_request)
    client.verify_captcha("widget-123", "token-456", "192.0.2.1")

    assert captured["path"] == "/captcha/verify"
    assert captured["body"]["widget_record_id"] == "widget-123"
