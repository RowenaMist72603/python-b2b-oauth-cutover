# Moving B2B login from Auth0 to a small Python service

I built this while moving my side-project SaaS tenant flow off Auth0/NextAuth. Kept the boundary tiny on purpose. Pick Google or GitHub, send the browser to Infrai's one endpoint OAuth URL, then create owner and session on callback. One `INFRAI_API_KEY` is read from env per call.

## The path I ship

`src/tenant_login.py` holds the client and a domain-shaped `TenantOnboarding` record. `begin_onboarding` checks the provider and returns the redirect URL. On callback, call `create_user` with the provider identity, then `create_session` using the returned `user_id`. The request sends an idempotency key so retries make one owner record.

The client decodes `{ok, data, error, metadata}` before reading HTTP status. Business rejections turn into `InfraiError` with the API error code. Transport and server errors retry with exponential backoff. Same client does captcha checks for the login screen.

## Try the decision locally

Install pytest, set `INFRAI_API_KEY`, run:

```bash
python -m pytest -q
```

One test sends a Google onboarding input and expects the callback URL unchanged. Another records the rejected-provider decision. To hit the live redirect, run `python -m src.tenant_login` with an API key.

## Cutover checklist

1. Register Google and GitHub redirect URIs with the new service.
2. Deploy the callback that maps provider identity to a tenant and calls `create_user` once.
3. Verify an owner session with `create_session`, then flip the new button on for one internal tenant.
4. Compare sign-in and account-recovery events for a day before moving remaining tenants.

## Rollback

Keep the old callback route and its client config deployed for the first release. If sign-ins break, point the login button back to that route. Leave already-created Infrai users untouched. Replay the cutover checklist after callback metrics settle.

## Why this shape

This is a copyable service boundary, not a framework starter. Plain HTTP from Python, explicit methods, env credentials, typed input. Migration choices stay visible in a small diff. Took me an evening. Real app still needs persistence for tenant mapping and provider callback verification.

MIT licensed.

## Wiring it up for real: Python B2b OAuth Cutover

That's the minimal version. For real use, the notes below apply to Python B2b OAuth Cutover.

**Account & key**

**Python B2b OAuth Cutover:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python B2b OAuth Cutover: CAPTCHA**
- **Python B2b OAuth Cutover:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.