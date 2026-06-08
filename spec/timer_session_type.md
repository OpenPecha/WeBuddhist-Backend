# TIMER Session Type

## Summary

A routine time block holds an ordered list of **sessions**. Until now a session was always one of two types, each pointing at an existing entity through `source_id`:

- `PLAN` → `source_id` references a `Plan`
- `RECITATION` → `source_id` references a `Text`

We added a third type, `TIMER`. A timer does **not** reference any entity — it is just a duration the user wants to spend (e.g. 15 minutes). It will later back an audio feature, but for now it only carries a length. In the UI it appears alongside "Add plan" / "Add recitation" as "Add timer".

## The core design decision

Because a timer has no entity to point at, it cannot reuse `source_id` (a `UUID` column). Instead:

- `source_id` is now **nullable** and stays `NULL` for timers.
- A new **`duration_ms`** column stores the timer length.

### Why milliseconds?

`duration_ms` is an integer in **milliseconds**, matching the existing audio/media convention across the codebase (`audio_duration_ms`, `start_ms`, `end_ms`, `duration_ms`). When the timer is wired to audio later, the value lines up with those fields with zero conversion. Durations are always stored as an integer base unit — never a float or a formatted string.

### Shape of a session row

| `session_type` | `source_id` | `duration_ms` | `display_order` |
|----------------|-------------|---------------|-----------------|
| `PLAN`         | required    | `NULL`        | int             |
| `RECITATION`   | required    | `NULL`        | int             |
| `TIMER`        | `NULL`      | required (> 0)| int             |

## Changes by layer

### 1. Enum — `pecha_api/routines/routines_enums.py`
Added `TIMER = "TIMER"` to `SessionType`.

### 2. Model — `pecha_api/routines/routines_models.py`
On `RoutineSession`:
- `source_id` changed to `nullable=True`.
- Added `duration_ms = Column(Integer, nullable=True)`.

### 3. Request / Response models — `pecha_api/routines/routines_response_models.py`
- `SessionRequest`: `source_id` is now `Optional[UUID]`; added `duration_ms: Optional[int]`.
- `SessionDTO`: `source_id`, `title`, and `language` are now `Optional` (a timer has none); added `duration_ms: Optional[int]`.

### 4. Service — `pecha_api/routines/routines_service.py`
- `_validate_time_block_request` validates each session: a `TIMER` must have a positive `duration_ms`; a `PLAN`/`RECITATION` must have a `source_id`.
- `build_session_models` now persists `duration_ms`.
- New `_resolve_timer_sessions` builds the DTO directly from the row — no DB or Mongo lookup, since there is nothing external to resolve.
- `_resolve_sessions` now buckets `TIMER` sessions and merges them in, still ordered by `display_order`.
- Plan-specific logic (duplicate checks, auto enroll/unenroll) already filters on `SessionType.PLAN`, so timers are naturally ignored.

### 5. Migration — `migrations/versions/c5e7a9b1d3f2_add_timer_session_type.py`
- `ALTER TYPE sessiontype ADD VALUE 'TIMER'` inside an `autocommit_block` (Postgres cannot add an enum value inside a transaction).
- Adds the `duration_ms` column.
- Drops the `NOT NULL` constraint on `source_id`.
- Downgrade removes timer rows, restores `source_id NOT NULL`, drops `duration_ms`, and recreates the enum without `TIMER`.

## API examples

### Create a time block with a timer session

```json
POST /routines/{routine_id}/time-blocks
{
  "time": "07:30",
  "time_int": 730,
  "notification_enabled": true,
  "sessions": [
    { "session_type": "PLAN",      "source_id": "…uuid…", "display_order": 0 },
    { "session_type": "TIMER",     "duration_ms": 900000, "display_order": 1 }
  ]
}
```

`duration_ms: 900000` = 15 minutes.

### Timer session in the response

```json
{
  "id": "…uuid…",
  "session_type": "TIMER",
  "source_id": null,
  "title": null,
  "language": null,
  "duration_ms": 900000,
  "image_url": null,
  "display_order": 1
}
```

## Validation rules

- `TIMER` → `duration_ms` is required and must be `> 0`; `source_id` is ignored.
- `PLAN` / `RECITATION` → `source_id` is required; `duration_ms` is ignored.
- Other existing rules (at least one session, valid `HH:MM` time, no duplicate plan across the routine) are unchanged.
