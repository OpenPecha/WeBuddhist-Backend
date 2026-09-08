# Daily Chant Progress — Recitation Collections

Tracks which chants a user completed each day, for both **group** recitation
collections and individual **user** recitation collections. Same design,
mirrored across two tables so each stays scoped to its own collection type.

## How it works

One row is logged per `(user, chant item, day)` when a chant is marked done.
No separate streak/counter table — "day count" and "today's chants" are
computed on the fly from these log rows.

| | Group collections | User collections |
|---|---|---|
| Completion table | `user_chant_completion` | `recitation_collection_chant_completions` |
| Model | [`UserChantCompletion`](../pecha_api/group_recitation_collection/user_chant_completion_models.py) | [`RecitationCollectionChantCompletion`](../pecha_api/plans/users/recitation_collection/recitation_collection_completion_models.py) |
| Router prefix | `/users/me/groups/recitation-collections/{collection_id}/complete` | `/users/me/recitation-collections/{collection_id}/complete` |
| Ownership check | collection's group must exist and be published | collection's `user_id` must match the caller |

## Endpoints (identical shape for both)

- `POST {prefix}` — body `{ "chant_id": "<uuid>" }` → `204`. Logs today's chant as done. Calling it again the same day for the same chant is a no-op (idempotent).
- `GET {prefix}/today` — `{ "completed_chant_ids": [...], "date": "YYYY-MM-DD" }`.
- `GET {prefix}/days-count` — `{ "collection_id": "...", "day_count": N }`, the count of distinct days with ≥1 completed chant.

## Steps to add this to a new collection type

1. **Model**: new table with `id`, `user_id → users.id`, `chant_id → <items>.id`, `collection_id → <collections>.id`, `completion_date DATE`, `created_at`. Unique on `(user_id, chant_id, completion_date)`; index on `(user_id, completion_date)` and on `collection_id`.
2. **Migration**: `op.create_table(...)` guarded by `table_exists`/`index_exists` from `migrations/idempotency.py`; chain `down_revision` to the current `alembic heads` output.
3. **Repository**: 4 functions — `get_user_completions_today`, `count_unique_completion_days`, `check_completion_exists`, `create_chant_completion`.
4. **Response models**: `CreateChantCompletionRequest`, `TodayChantCompletionsResponse`, `ChantCompletionDayCountResponse`.
5. **Service**: `_get_collection_or_404` (ownership check specific to the collection type) + `get_today_completions_service`, `get_completion_day_count_service`, `create_chant_completion_service` (validates the chant belongs to the collection, then inserts idempotently).
6. **Router**: 3 endpoints under `{collection_prefix}/{collection_id}/complete` as listed above.
7. **Wire up**: import + `api.include_router(...)` in [`pecha_api/app.py`](../pecha_api/app.py).

## Reference implementation (user recitation collections)

- [recitation_collection_completion_models.py](../pecha_api/plans/users/recitation_collection/recitation_collection_completion_models.py)
- [recitation_collection_completion_repository.py](../pecha_api/plans/users/recitation_collection/recitation_collection_completion_repository.py)
- [recitation_collection_completion_response_models.py](../pecha_api/plans/users/recitation_collection/recitation_collection_completion_response_models.py)
- [recitation_collection_completion_service.py](../pecha_api/plans/users/recitation_collection/recitation_collection_completion_service.py)
- [recitation_collection_completion_views.py](../pecha_api/plans/users/recitation_collection/recitation_collection_completion_views.py)
- Migration: [b9dd872a530c_add_recitation_collection_chant_completion.py](../migrations/versions/b9dd872a530c_add_recitation_collection_chant_completion.py)
- Tests: [test_recitation_collection_completion_service.py](../tests/plans/users/recitation_collection/test_recitation_collection_completion_service.py)
