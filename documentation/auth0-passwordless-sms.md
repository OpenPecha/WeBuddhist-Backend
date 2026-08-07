# Auth0 Passwordless SMS setup

The regular-user and Studio phone-login flows use Auth0 Universal Login for OTP
delivery and exchange the resulting Auth0 access token for the backend's normal
token pair. The backend does not generate or store OTP codes.

## Auth0 tenant

1. Create and enable the Auth0 Passwordless SMS connection named `sms` for the
   Studio SPA.
2. Configure an SMS provider (for example, Twilio) and Auth0's OTP lifetime,
   resend, and brute-force protection.
3. Add the Studio callback and logout URLs to the Auth0 SPA application.
4. Enable Authorization Code with PKCE and the backend API audience. The API
   identifier differs per tenant: `webuddhist-backend` on dev,
   `https://api.webuddhist.com` on prod.
5. Add the following Post Login Action to the Login flow. The audience guard
   lists every environment's API identifier — if the Action's guard does not
   match the identifier the SPA requested, the Action returns early and the
   access token ships without phone claims, which the backend rejects as
   `Invalid Auth0 SMS token`. This Action covers both SMS passwordless and
   Google social login claims.

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const audiences = ["webuddhist-backend", "https://api.webuddhist.com"];
  const namespace = "https://webuddhist.com";

  if (!audiences.includes(event.resource_server?.identifier)) {
    return;
  }

  if (event.connection?.name === "sms" && event.user.phone_number) {
    api.accessToken.setCustomClaim(
      `${namespace}/phone_number`,
      event.user.phone_number
    );
    api.accessToken.setCustomClaim(
      `${namespace}/phone_number_verified`,
      event.user.phone_verified === true
    );
    return;
  }

  if (event.connection?.strategy === "google-oauth2" && event.user.email) {
    api.accessToken.setCustomClaim(`${namespace}/email`, event.user.email);
    api.accessToken.setCustomClaim(
      `${namespace}/email_verified`,
      event.user.email_verified === true
    );
    if (event.user.given_name) {
      api.accessToken.setCustomClaim(
        `${namespace}/given_name`,
        event.user.given_name
      );
    }
    if (event.user.family_name) {
      api.accessToken.setCustomClaim(
        `${namespace}/family_name`,
        event.user.family_name
      );
    }
  }
};
```

The backend accepts only RS256 access tokens whose issuer, audience, `sms|`
subject prefix, namespaced phone claims, and issue time all pass validation.
Phone numbers must be in E.164 form and come from the namespaced claim; the
subject stays the opaque Auth0 user id (`sms|6a744811b6f40222b44b0bf3`) and is
never expected to contain the phone number.

Tokens are rejected if they are older than `AUTH0_SMS_TOKEN_MAX_AGE_SECONDS`
(default 300). The Auth0 access token itself lives far longer, and the SPA
caches it, so the exchange must happen promptly after login.

## Backend environment

```dotenv
AUTH0_SMS_DOMAIN=tenant.example.auth0.com
AUTH0_SMS_AUDIENCE=webuddhist-backend
AUTH0_SMS_PHONE_CLAIM=https://webuddhist.com/phone_number
AUTH0_SMS_PHONE_VERIFIED_CLAIM=https://webuddhist.com/phone_number_verified
AUTH0_SMS_TOKEN_MAX_AGE_SECONDS=300
```

`AUTH0_SMS_DOMAIN` and `AUTH0_SMS_AUDIENCE` must match the tenant and audience
the Studio SPA requests (`VITE_AUTH0_DOMAIN` and `VITE_AUTH0_AUDIENCE`). A
mismatch fails during signature verification with "signing key was not found",
because the backend fetches JWKS from the wrong tenant.

Run the Alembic migration before enabling phone login. It adds nullable,
uniquely indexed `phone_number` columns directly to both `users` and `authors`;
no separate identity table is used.

The exchange/link endpoints are:

- `/api/v1/auth/phone/exchange` and `/api/v1/auth/phone/link` for users.
- `/api/v1/cms/auth/phone/exchange` and `/api/v1/cms/auth/phone/link` for
  Studio authors.
- `/api/v1/cms/auth/google/exchange` for Studio Google login.

## Google social login (Studio)

Enable the Auth0 Google social connection (`google-oauth2`) on the Studio SPA
and extend the Post Login Action so Google access tokens carry email claims:

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const audiences = ["webuddhist-backend", "https://api.webuddhist.com"];
  const namespace = "https://webuddhist.com";

  if (!audiences.includes(event.resource_server?.identifier)) {
    return;
  }

  if (event.connection?.name === "sms" && event.user.phone_number) {
    api.accessToken.setCustomClaim(
      `${namespace}/phone_number`,
      event.user.phone_number
    );
    api.accessToken.setCustomClaim(
      `${namespace}/phone_number_verified`,
      event.user.phone_verified === true
    );
    return;
  }

  if (event.connection?.strategy === "google-oauth2" && event.user.email) {
    api.accessToken.setCustomClaim(`${namespace}/email`, event.user.email);
    api.accessToken.setCustomClaim(
      `${namespace}/email_verified`,
      event.user.email_verified === true
    );
    if (event.user.given_name) {
      api.accessToken.setCustomClaim(
        `${namespace}/given_name`,
        event.user.given_name
      );
    }
    if (event.user.family_name) {
      api.accessToken.setCustomClaim(
        `${namespace}/family_name`,
        event.user.family_name
      );
    }
  }
};
```

Studio environment additions:

```dotenv
VITE_AUTH0_GOOGLE_CONNECTION=google-oauth2
```

Backend environment additions:

```dotenv
AUTH0_GOOGLE_EMAIL_CLAIM=https://webuddhist.com/email
AUTH0_GOOGLE_EMAIL_VERIFIED_CLAIM=https://webuddhist.com/email_verified
```

## Studio environment

```dotenv
VITE_AUTH0_DOMAIN=tenant.example.auth0.com
VITE_AUTH0_CLIENT_ID=your-spa-client-id
VITE_AUTH0_AUDIENCE=webuddhist-backend
VITE_AUTH0_SMS_CONNECTION=sms
VITE_AUTH0_GOOGLE_CONNECTION=google-oauth2
```

Use environment-specific values and never commit Auth0 or SMS-provider secrets.
