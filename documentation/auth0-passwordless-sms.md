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
4. Enable Authorization Code with PKCE and the `webuddhist-backend` API
   audience.
5. Add the following Post Login Action to the Login flow. Change the audience
   guard if the API identifier differs by environment. This Action covers both
   SMS passwordless and Google social login claims.

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const audience = "webuddhist-backend";
  const namespace = "https://webuddhist.com";

  if (event.resource_server?.identifier !== audience) {
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
subject, namespaced phone claims, and issue time all pass validation. Phone
numbers must be in E.164 form.

## Backend environment

```dotenv
AUTH0_SMS_DOMAIN=tenant.example.auth0.com
AUTH0_SMS_AUDIENCE=webuddhist-backend
AUTH0_SMS_PHONE_CLAIM=https://webuddhist.com/phone_number
AUTH0_SMS_PHONE_VERIFIED_CLAIM=https://webuddhist.com/phone_number_verified
AUTH0_SMS_TOKEN_MAX_AGE_SECONDS=300
```

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
  const audience = "webuddhist-backend";
  const namespace = "https://webuddhist.com";

  if (event.resource_server?.identifier !== audience) {
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
