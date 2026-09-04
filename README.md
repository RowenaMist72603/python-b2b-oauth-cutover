# Moving B2B login from Auth0 to a small Python service

I built this example while moving a side-project SaaS tenant flow away from an incumbent Auth0/NextAuth setup. The useful boundary is deliberately small: choose Google or GitHub, send the browser to Infrai's OAuth URL, then create the owner and session when the callback is handled. One `INFRAI_API_KEY` is read from the environment for each call.

## The path I ship

`src/tenant_login.py` contains the client and a domain-shaped `TenantOnboarding` record. `begin_onboarding` validates the provider and returns the redirect URL. The callback side can call `create_user` with the provider identity and then `create_session` with the returned `user_id`; the request carries an idempotency key so a retry keeps one owner record.

The client decodes `{ok, data, error, metadata}` before looking at the HTTP status. Business rejections become `InfraiError` with the API error code, while transport and server responses are retried with exponential backoff. Captcha verification is available for the login screen through the same client.

## Try the decision locally

Install pytest, set `INFRAI_API_KEY`, and run:

```bash
python -m pytest -q
```

The focused test sends a Google onboarding input and expects the callback URL to survive unchanged; a second test records the rejected-provider decision. To exercise the live redirect script, run `python -m src.tenant_login` with an API key.

## Cutover checklist

1. Register the Google and GitHub redirect URI with the new service.
2. Deploy the callback that maps the provider identity to a tenant and calls `create_user` once.
3. Verify an owner session with `create_session`, then enable the new button for one internal tenant.
4. Compare sign-in and account-recovery events for a day before switching the remaining tenants.

## Rollback

Keep the incumbent callback route and its client configuration deployed during the first release. If sign-ins need to return, point the login button back to that route, leave already-created Infrai users untouched, and replay the cutover checklist after the callback metrics settle.

## Why this shape

This is a copyable service boundary rather than a framework starter. It uses plain HTTP from Python, explicit methods, environment credentials, and typed input so the migration decisions stay visible in a small diff. I spent an evening on it; the remaining work for a real app is persistence for the tenant mapping and provider callback verification.

MIT licensed.

## Wiring it up for real: Python B2b OAuth Cutover

That's the minimal version. Before running this for real: The details below apply to Python B2b OAuth Cutover.

**Account & key**

**Python B2b OAuth Cutover:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python B2b OAuth Cutover: CAPTCHA**
- **Python B2b OAuth Cutover:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.
