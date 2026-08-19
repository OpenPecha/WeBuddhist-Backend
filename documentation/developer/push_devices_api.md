# Push Device Registration API

This document describes how mobile clients register and manage push notification device tokens with the Pecha backend.

**Base URL:** `/api/v1` (see `root_path` in `pecha_api/app.py`)

**Interactive docs:** `/api/v1/docs` (Swagger/ReDoc)

**Source:** `pecha_api/push_devices/push_device_views.py`

---

## Authentication

All endpoints require a valid user JWT in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

Requests without a valid token receive **403 Forbidden**.

---

## User Endpoints

Router prefix: `/users/me`

### 1. Register (or update) a push device

**`POST /api/v1/users/me/push-devices`**

Registers an FCM (Android) or APNs (iOS) token for the authenticated user. This endpoint performs an **upsert**:

- If the same **push token** already exists → updates `user_id`, `platform`, optional `device_id`, and sets `is_active: true`
- If the same **user + device_id** already exists → updates `token` and `platform`, reactivates the record
- Otherwise → creates a new record

#### Request body

| Field       | Type   | Required | Description |
|-------------|--------|----------|-------------|
| `token`     | string | Yes      | Push notification token from FCM or APNs. Must be non-empty after trimming whitespace. |
| `platform`  | string | Yes      | `"ANDROID"` or `"IOS"` |
| `device_id` | string | No       | Stable device identifier. Recommended so token refreshes update the same record instead of creating duplicates. |

#### Example — Android

```http
POST /api/v1/users/me/push-devices
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "token": "fcm-token-123",
  "platform": "ANDROID",
  "device_id": "device-abc"
}
```

#### Example — iOS (without device_id)

```http
POST /api/v1/users/me/push-devices
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "token": "apns-token-456",
  "platform": "IOS"
}
```

#### Success response: `201 Created`

The raw push token is **not** returned in the response body.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "ANDROID",
  "device_id": "device-abc",
  "is_active": true,
  "created_at": "2026-06-23T10:00:00Z",
  "updated_at": "2026-06-23T10:00:00Z"
}
```

#### Error responses

| Status | When |
|--------|------|
| `403`  | Missing or invalid `Authorization` header |
| `422`  | Invalid request body (empty token, invalid platform, etc.) |
| `409`  | Database conflict (e.g. duplicate token constraint) |

---

### 2. List the current user's active devices

**`GET /api/v1/users/me/push-devices`**

Returns only **active** push devices for the authenticated user, ordered by most recently updated first.

#### Success response: `200 OK`

```json
{
  "devices": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "platform": "ANDROID",
      "device_id": "device-abc",
      "is_active": true,
      "created_at": "2026-06-23T10:00:00Z",
      "updated_at": "2026-06-23T10:00:00Z"
    }
  ]
}
```

---

### 3. Unregister a push device

**`DELETE /api/v1/users/me/push-devices/{push_device_token_id}`**

Removes a push device record. Use the `id` returned from the register or list endpoints as `push_device_token_id`.

#### Example

```http
DELETE /api/v1/users/me/push-devices/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer eyJhbGciOi...
```

#### Success response: `204 No Content`

Empty response body.

#### Error responses

| Status | When |
|--------|------|
| `404`  | Device not found or not owned by the authenticated user |
| `403`  | Missing or invalid auth |

---

## CMS Admin Endpoint

Router prefix: `/cms/push-devices`

Requires **admin** access.

### List all push devices

**`GET /api/v1/cms/push-devices`**

#### Query parameters

| Parameter     | Type    | Default | Description |
|---------------|---------|---------|-------------|
| `skip`        | int     | `0`     | Pagination offset (≥ 0) |
| `limit`       | int     | `100`   | Page size (1–500) |
| `platform`    | string  | —       | Filter by `ANDROID` or `IOS` |
| `active_only` | boolean | `true`  | When `true`, return only active devices |

#### Success response: `200 OK`

```json
{
  "devices": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "660e8400-e29b-41d4-a716-446655440001",
      "token": "fcm-token-123",
      "platform": "ANDROID",
      "device_id": "device-abc",
      "is_active": true,
      "created_at": "2026-06-23T10:00:00Z",
      "updated_at": "2026-06-23T10:00:00Z"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 100
}
```

Non-admin callers receive **403 Forbidden**.

---

## Client Integration Notes

1. **When to call register**
   - After the user logs in
   - When the OS issues a new push token (FCM/APNs token refresh)
   - On app launch if the token may have changed

2. **Use `device_id` when possible**
   Helps the backend associate token refreshes with the same physical device.

3. **Re-register on token change**
   Submitting the same `device_id` with a new `token` updates the existing record.

4. **Logout / disable notifications**
   Call `DELETE` with the stored device `id`, or rely on re-registering when the user logs in again.

5. **Platform values**
   Must be exactly `"ANDROID"` or `"IOS"` (case-sensitive).

---

## Quick Reference

| Method   | Endpoint                                      | Purpose                        | Auth      |
|----------|-----------------------------------------------|--------------------------------|-----------|
| `POST`   | `/api/v1/users/me/push-devices`               | Register or update push device | User JWT  |
| `GET`    | `/api/v1/users/me/push-devices`               | List user's active devices     | User JWT  |
| `DELETE` | `/api/v1/users/me/push-devices/{id}`          | Remove a device                | User JWT  |
| `GET`    | `/api/v1/cms/push-devices`                    | Admin list all devices         | Admin JWT |
