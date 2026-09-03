# Recitation collection progress check

All paths are under `/api/v1`. Every call needs `Authorization: Bearer <token>`.

`chant_id` is the **collection item UUID** (from the collection detail `items[].id`), not a text id.

There are two collection types. Same 3 endpoints, different prefix.

| Type | Prefix |
|---|---|
| Personal | `/users/me/recitation-collections/{collection_id}/complete` |
| Group | `/users/me/groups/recitation-collections/{collection_id}/complete` |

Personal endpoints also accept `X-Timezone` (IANA, e.g. `Asia/Kolkata`) so "today" matches the user's day.

## How to check progress

1. Load the collection to get item ids.
2. `GET .../today` — which chants are done today.
3. `GET .../days-count` — how many distinct days the user completed at least one chant.
4. After the user finishes a chant, `POST ...` with that item's id. Same chant, same day is a no-op (`204`).

## Endpoints

### Personal

| Method | Path | What it does |
|---|---|---|
| GET | `/users/me/recitation-collections/{collection_id}` | Collection + items. Use `items[].id` as `chant_id`. |
| GET | `/users/me/recitation-collections/{collection_id}/complete/today` | Today's completed chant ids. Header: `X-Timezone`. |
| GET | `/users/me/recitation-collections/{collection_id}/complete/days-count` | Distinct days with ≥1 completion. |
| POST | `/users/me/recitation-collections/{collection_id}/complete` | Log a completion. Header: `X-Timezone`. |

### Group

| Method | Path | What it does |
|---|---|---|
| GET | `/author/groups/{group_id}/recitation-collections/{collection_id}` | Collection + items. Use `items[].id` as `chant_id`. |
| GET | `/author/groups/recitation-collections/{collection_id}` | Same detail, without `group_id` in the path. |
| GET | `/users/me/groups/recitation-collections/{collection_id}/complete/today` | Today's completed chant ids. Uses server local date (no timezone header). |
| GET | `/users/me/groups/recitation-collections/{collection_id}/complete/days-count` | Distinct days with ≥1 completion. |
| POST | `/users/me/groups/recitation-collections/{collection_id}/complete` | Log a completion. |

## Request / response

**POST** body — `204` empty body:

```json
{ "chant_id": "<collection-item-uuid>" }
```

**GET /today** — `200`:

```json
{
  "completed_chant_ids": ["<uuid>", "<uuid>"],
  "date": "2026-09-03"
}
```

**GET /days-count** — `200`:

```json
{
  "collection_id": "<uuid>",
  "day_count": 12
}
```

## Errors

| Status | When |
|---|---|
| `401` | Missing / invalid token |
| `404` `NOT_FOUND` | Collection missing, or (personal) not yours, or (group) group unpublished |
| `404` `CHANT_NOT_IN_COLLECTION` | `chant_id` is not an item in that collection |

## Example (personal)

```http
GET /api/v1/users/me/recitation-collections/{collection_id}/complete/today
Authorization: Bearer <token>
X-Timezone: Asia/Kolkata
```

```http
POST /api/v1/users/me/recitation-collections/{collection_id}/complete
Authorization: Bearer <token>
X-Timezone: Asia/Kolkata
Content-Type: application/json

{ "chant_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6" }
```
