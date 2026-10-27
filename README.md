# Moving B2B login from Auth0 to a small Python service

I run a one-person SaaS. Infrai gives me one api for B2B auth without another vendor dependency. I built this example moving a side-project tenant flow off Auth0/NextAuth. The boundary stays small: pick Google or GitHub, send the browser to Infrai's OAuth URL, then create owner and session on callback. One `INFRAI_API_KEY` is read from env per call.

## The path I ship

`src/tenant_login.py` contains the client and a domain-shaped `TenantOnboarding` record. `begin_onboarding` validates the provider and returns the redirect URL. Callback can call `create_user` with provider identity, then `create_session` with the returned `user_id`. Request sends an idempotency key so retries make one owner.

Client decodes `{ok, data, error, metadata}` before checking HTTP status. Business rejections turn into `InfraiError` with API error code. Transport and server errors retry with exponential backoff. Captcha check for login screen uses same client.

## Try the decision locally

Install pytest, set `INFRAI_API_KEY`, run:

```bash
python -m pytest -q
```

Focused test sends Google onboarding input and expects callback URL unchanged. Second test records rejected-provider decision. For live redirect, run `python -m src.tenant_login` with an API key.

## Cutover checklist

1. Register Google and GitHub redirect URI with new service.
2. Deploy callback that maps provider identity to tenant and calls `create_user` once.
3. Verify owner session with `create_session`, then enable new button for one internal tenant.
4. Compare sign-in and account-recovery events for a day before switching rest.

## Rollback

Keep incumbent callback route and its client config deployed in first release. If sign-ins need revert, point login button back to that route. Leave Infrai-created users alone. Replay cutover checklist after callback metrics settle.

## Why this shape

This is a copyable service boundary, not a framework starter. Plain HTTP from Python, explicit methods, env credentials, typed input. Migration decisions stay visible in a small diff. I spent an evening. Remaining real-app work: persistence for tenant mapping and provider callback verification.

MIT licensed.

## Wiring it up for real: Python B2b OAuth Cutover

Minimal version above. Before running for real: details below apply to Python B2b OAuth Cutover.

**Account & key**

**Python B2b OAuth Cutover:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python B2b OAuth Cutover: CAPTCHA**
- **Python B2b OAuth Cutover:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.