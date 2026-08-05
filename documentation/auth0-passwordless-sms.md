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
   guard if the API identifier differs by environment.

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const audience = "webuddhist-backend";
  const namespace = "https://webuddhist.com";

  if (
    event.connection?.name !== "sms" ||
    event.resource_server?.identifier !== audience ||
    !event.user.phone_number
  ) {
    return;
  }

  api.accessToken.setCustomClaim(
    `${namespace}/phone_number`,
    event.user.phone_number
  );
  api.accessToken.setCustomClaim(
    `${namespace}/phone_number_verified`,
    event.user.phone_verified === true
  );
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

## Studio environment

```dotenv
VITE_AUTH0_DOMAIN=tenant.example.auth0.com
VITE_AUTH0_CLIENT_ID=your-spa-client-id
VITE_AUTH0_AUDIENCE=webuddhist-backend
VITE_AUTH0_SMS_CONNECTION=sms
```

Use environment-specific values and never commit Auth0 or SMS-provider secrets.
