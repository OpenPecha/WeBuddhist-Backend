# Accumulator System API Documentation

Complete API reference for the Accumulator system, enabling individual and group-based counting/tracking functionality (e.g., mantra recitations, practice sessions).

---

## Table of Contents

1. [Conceptual Overview](#conceptual-overview)
2. [Data Models](#data-models)
3. [Individual Accumulator APIs](#individual-accumulator-apis)
4. [Group Accumulator APIs (User)](#group-accumulator-apis-user)
5. [CMS Group Accumulator APIs](#cms-group-accumulator-apis)
6. [Request/Response Schemas](#requestresponse-schemas)
7. [Common Workflows](#common-workflows)
8. [Error Handling](#error-handling)

---

## Conceptual Overview

### What is an Accumulator?

An **Accumulator** is a counter that tracks cumulative counts (e.g., mantra recitations, prostrations). The system supports two main use cases:

1. **Individual Accumulators** - Personal counters for a user's own practice
2. **Group Accumulators** - Shared counters where multiple group members contribute toward a collective goal

### Key Concepts

#### Presets vs User Accumulators

| Type | Description | Created By |
|------|-------------|------------|
| `PRESET` | Template accumulators available to all users. Users "tap" a preset to create their own copy. | CMS/Admin |
| `USER` | Personal accumulator created from a preset. Tracks individual progress. | User (from preset) |

#### Accumulator Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                        PRESET                                │
│  (Public template with mantra, target, mala image)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ User taps preset
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    USER ACCUMULATOR                          │
│  (Personal copy with own current_count, history)            │
│  - parent_id → links back to PRESET                         │
│  - user_id → owner                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Each count update
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  ACCUMULATOR HISTORY                         │
│  (Individual session records with count deltas)             │
└─────────────────────────────────────────────────────────────┘
```

#### Group Accumulator Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                      AUTHOR GROUP                            │
│  (Community/organization with members)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Group creates accumulator
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   GROUP ACCUMULATOR                          │
│  (Shared counter for group practice)                        │
│  - group_id → owning group                                  │
│  - accumulator_id → optional link to preset                 │
│  - target_count, start_date, end_date                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Members contribute
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              GROUP ACCUMULATOR HISTORY                       │
│  (Per-user contribution records)                            │
│  - user_id → contributor                                    │
│  - count → delta contributed                                │
└─────────────────────────────────────────────────────────────┘
```

### Mala Images

A **Mala Image** is a visual representation (bead counter image) that can be associated with an accumulator. Users can customize their accumulator's mala image from a catalog.

### Metadata

Accumulators support **multi-language metadata** with `name` and `description` fields per language code (e.g., `EN`, `BO`, `ZH`).

---

## Data Models

### Accumulator

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID? | Owner (null for presets) |
| `group_id` | UUID? | Associated group (if any) |
| `parent_id` | UUID? | Preset this was created from (null for presets) |
| `type` | enum | `preset` or `user_created` |
| `target_count` | int? | Goal count (optional) |
| `current_count` | int | Current accumulated count |
| `text_id` | UUID? | Associated text (optional) |
| `mantra_id` | UUID? | Associated mantra (optional) |
| `mala_image` | UUID? | Chosen mala image ID |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |
| `deleted_at` | datetime? | Soft delete timestamp |

### AccumulatorHistory

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `accumulator_id` | UUID | Parent accumulator |
| `user_id` | UUID | User who made this entry |
| `count` | int | Count delta (always positive) |
| `created_at` | datetime | Session timestamp |

### GroupAccumulator

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `accumulator_id` | UUID? | Linked preset (optional) |
| `group_id` | UUID | Owning group |
| `title` | string? | Display title |
| `target_count` | int? | Group goal |
| `start_date` | datetime? | Practice period start |
| `end_date` | datetime? | Practice period end |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |
| `deleted_at` | datetime? | Soft delete timestamp |

### GroupAccumulatorHistory

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `group_accumulator_id` | UUID | Parent group accumulator |
| `user_id` | UUID | Contributing user |
| `count` | int | Count delta contributed |
| `created_at` | datetime | Contribution timestamp |

---

## Individual Accumulator APIs

Base path: `/accumulators`

### GET /accumulators/presets

List all public preset accumulators available for users to add.

**Authentication**: Not required

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 20 | Max records (1-100) |
| `language` | string? | - | Language code for mantra content (e.g., `en`, `bo`) |
| `search` | string? | - | Filter by mantra text, title, or pronunciation |

**Response**: `PublicAccumulatorsResponse`

```json
{
  "accumulators": [
    {
      "id": "uuid",
      "group_id": null,
      "type": "preset",
      "target_count": 100000,
      "current_count": 0,
      "text_id": null,
      "mantra": {
        "id": "uuid",
        "mantra": "ཨོཾ་མ་ཎི་པདྨེ་ཧཱུྃ།",
        "title": "Six-Syllable Mantra",
        "pronunciation": "Om Mani Padme Hum",
        "audio_url": "https://...",
        "mala_image_id": "uuid",
        "mala_image_url": "https://presigned-s3-url..."
      },
      "mala_image_id": "uuid",
      "mala_image_url": "https://presigned-s3-url...",
      "metadata": [
        {
          "language": "EN",
          "name": "Chenrezig Mantra",
          "description": "The mantra of compassion"
        }
      ],
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 50,
  "skip": 0,
  "limit": 20
}
```

---

### GET /accumulators/user

List the authenticated user's personal accumulators.

**Authentication**: Required (Bearer token)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 20 | Max records (1-100) |

**Response**: `AccumulatorsResponse`

```json
{
  "accumulators": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "group_id": null,
      "parent_id": "preset-uuid",
      "type": "user_created",
      "target_count": 100000,
      "current_count": 1250,
      "text_id": null,
      "mantra_id": "uuid",
      "mala_image_id": "uuid",
      "mala_image_url": "https://presigned-s3-url...",
      "metadata": [...],
      "created_at": "2024-01-20T08:00:00Z",
      "updated_at": "2024-01-25T14:30:00Z"
    }
  ],
  "total": 5,
  "skip": 0,
  "limit": 20
}
```

---

### POST /accumulators/user

Create a personal accumulator from a preset. The preset's fields are copied to the new user accumulator.

**Authentication**: Required (Bearer token)

**Request Body**: `CreateAccumulatorRequest`

```json
{
  "parent_id": "preset-uuid"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `parent_id` | UUID | Yes | ID of the preset to create from |

**Response**: `201 Created` - `AccumulatorDTO`

```json
{
  "id": "new-uuid",
  "user_id": "user-uuid",
  "group_id": null,
  "parent_id": "preset-uuid",
  "type": "user_created",
  "target_count": 100000,
  "current_count": 0,
  "text_id": null,
  "mantra_id": "uuid",
  "mala_image_id": "uuid",
  "mala_image_url": "https://presigned-s3-url...",
  "metadata": [...],
  "created_at": "2024-01-25T10:00:00Z",
  "updated_at": "2024-01-25T10:00:00Z"
}
```

**Errors**:
- `404 NOT_FOUND` - Preset not found
- `409 CONFLICT` - User already has an accumulator from this preset

---

### PUT /accumulators/user/{accumulator_id}

Update a user's accumulator. When `current_count` increases, a history entry is automatically created.

**Authentication**: Required (Bearer token)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `accumulator_id` | UUID | Accumulator to update |

**Request Body**: `UpdateAccumulatorRequest`

```json
{
  "current_count": 1350,
  "target_count": 200000,
  "text_id": "uuid",
  "mantra_id": "uuid"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `current_count` | int | No | New absolute count (must be >= 0) |
| `target_count` | int | No | New target goal |
| `text_id` | UUID | No | Associated text |
| `mantra_id` | UUID | No | Associated mantra |

**Response**: `AccumulatorDTO`

**Behavior**:
- If `current_count` increases, a history row is created with the delta
- If `current_count` decreases or stays same, no history is created
- User's daily stats cache is invalidated on count increase

**Errors**:
- `404 NOT_FOUND` - Accumulator not found
- `403 FORBIDDEN` - Not owner or not a user-created accumulator

---

### DELETE /accumulators/user/{accumulator_id}

Soft-delete a user's accumulator. History is preserved for the user's history page.

**Authentication**: Required (Bearer token)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `accumulator_id` | UUID | Accumulator to delete |

**Response**: `204 No Content`

**Errors**:
- `404 NOT_FOUND` - Accumulator not found
- `403 FORBIDDEN` - Not owner or not a user-created accumulator

---

### PUT /accumulators/user/{accumulator_id}/mala-image

Update the mala image for an accumulator.

**Authentication**: Required (Bearer token)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `accumulator_id` | UUID | Accumulator to update |

**Request Body**: `UpdateMalaImageRequest`

```json
{
  "mala_image_id": "mala-image-uuid"
}
```

**Response**: `AccumulatorDTO`

**Errors**:
- `404 NOT_FOUND` - Accumulator or mala image not found
- `403 FORBIDDEN` - Not owner

---

### GET /accumulators/user/history

Get the authenticated user's accumulator history across all their accumulators.

**Authentication**: Required (Bearer token)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 20 | Max records (1-100) |

**Response**: `AccumulatorHistoryResponse`

```json
{
  "accumulators": [
    {
      "accumulator_id": "uuid",
      "parent_id": "preset-uuid",
      "target_count": 100000,
      "current_count": 1350,
      "total_counted": 1350,
      "mala_image_id": "uuid",
      "mala_image_url": "https://presigned-s3-url...",
      "metadata": [...],
      "sessions": [
        {
          "count": 108,
          "created_at": "2024-01-25T14:30:00Z"
        },
        {
          "count": 108,
          "created_at": "2024-01-24T09:15:00Z"
        }
      ]
    }
  ],
  "total": 5,
  "skip": 0,
  "limit": 20
}
```

---

### GET /accumulators/{parent_id}

Get the user's accumulator for a specific preset, with full session history. **Creates the accumulator if it doesn't exist.**

**Authentication**: Required (Bearer token)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `parent_id` | UUID | Preset ID |

**Response**: `AccumulatorHistoryDTO`

```json
{
  "accumulator_id": "uuid",
  "parent_id": "preset-uuid",
  "target_count": 100000,
  "current_count": 1350,
  "total_counted": 1350,
  "mala_image_id": "uuid",
  "mala_image_url": "https://presigned-s3-url...",
  "metadata": [...],
  "sessions": [
    {
      "count": 108,
      "created_at": "2024-01-25T14:30:00Z"
    }
  ]
}
```

**Behavior**:
- If user has no accumulator for this preset, one is automatically created
- Returns the accumulator with all session history

**Errors**:
- `404 NOT_FOUND` - Preset not found

---

### GET /accumulators/{accumulator_id}/groups

Get all group accumulators that use a specific accumulator (preset), with the authenticated user's contribution count for each.

**Authentication**: Required (Bearer token)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `accumulator_id` | UUID | Accumulator (preset) ID |

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 20 | Max records (1-100) |

**Response**: `AccumulatorGroupsResponse`

```json
{
  "groups": [
    {
      "group_accumulator_id": "uuid",
      "group_id": "uuid",
      "title": "100 Million Mani Retreat",
      "target_count": 100000000,
      "user_total_count": 5400,
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-12-31T23:59:59Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 3,
  "skip": 0,
  "limit": 20
}
```

---

## Group Accumulator APIs (User)

Base path: `/group-accumulators`

These endpoints are for regular users participating in group practices.

### GET /group-accumulators/{group_id}/accumulators

List all accumulators for a specific group.

**Authentication**: Not required

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | UUID | Group ID |

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 20 | Max records (1-100) |

**Response**: `GroupAccumulatorsResponse`

```json
{
  "accumulators": [
    {
      "id": "uuid",
      "accumulator_id": "preset-uuid",
      "group_id": "uuid",
      "title": "100 Million Mani Retreat",
      "target_count": 100000000,
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-12-31T23:59:59Z",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 2,
  "skip": 0,
  "limit": 20
}
```

---

### GET /group-accumulators/{group_accumulator_id}

Get details of a specific group accumulator, including total count from all contributors.

**Authentication**: Not required

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `group_accumulator_id` | UUID | Group accumulator ID |

**Response**: `GroupAccumulatorDetailDTO`

```json
{
  "id": "uuid",
  "accumulator_id": "preset-uuid",
  "group_id": "uuid",
  "title": "100 Million Mani Retreat",
  "target_count": 100000000,
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z",
  "total_count": 45678900,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-06-15T10:00:00Z"
}
```

---

### POST /group-accumulators/{group_accumulator_id}

Submit a count contribution to a group accumulator. User must be a member of the group.

**Authentication**: Required (Bearer token)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `group_accumulator_id` | UUID | Group accumulator ID |

**Request Body**: `SubmitGroupCountRequest`

```json
{
  "current_count": 5508
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `current_count` | int | Yes | User's new absolute total count (>= 0) |

**Response**: `GroupAccumulatorHistoryItemDTO`

**Status Codes**:
- `201 Created` - New history entry created (count increased)
- `200 OK` - No change (count stayed same or decreased)

```json
{
  "id": "history-uuid",
  "user_id": "user-uuid",
  "count": 108,
  "created_at": "2024-01-25T14:30:00Z"
}
```

**Behavior**:
- Calculates delta from user's previous total for this group accumulator
- Only creates history entry if delta > 0
- Returns `id: null` if no history was created

**Errors**:
- `404 NOT_FOUND` - Group accumulator not found
- `403 FORBIDDEN` - User is not a member of the group

---

### GET /group-accumulators/{group_accumulator_id}/history

Get the contribution history for a group accumulator.

**Authentication**: Not required

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `group_accumulator_id` | UUID | Group accumulator ID |

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 20 | Max records (1-100) |

**Response**: `GroupAccumulatorHistoryResponse`

```json
{
  "group_accumulator": {
    "id": "uuid",
    "accumulator_id": "preset-uuid",
    "group_id": "uuid",
    "title": "100 Million Mani Retreat",
    "target_count": 100000000,
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-12-31T23:59:59Z",
    "total_count": 45678900,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-06-15T10:00:00Z"
  },
  "history": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "count": 108,
      "created_at": "2024-01-25T14:30:00Z"
    },
    {
      "id": "uuid",
      "user_id": "uuid",
      "count": 216,
      "created_at": "2024-01-25T12:00:00Z"
    }
  ],
  "total": 1500,
  "skip": 0,
  "limit": 20
}
```

---

### DELETE /group-accumulators/{group_accumulator_id}

Soft-delete a group accumulator. Requires user to be a member of the group.

**Authentication**: Required (Bearer token)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `group_accumulator_id` | UUID | Group accumulator ID |

**Response**: `204 No Content`

**Errors**:
- `404 NOT_FOUND` - Group accumulator not found
- `403 FORBIDDEN` - User is not a member of the group

---

## CMS Group Accumulator APIs

Base path: `/cms/groups`

These endpoints are for CMS authors/admins to manage group accumulators. Requires appropriate permissions.

### POST /cms/groups/{group_id}/accumulators

Create a new group accumulator.

**Authentication**: Required (Bearer token - CMS author with create permission)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | UUID | Group ID |

**Request Body**: `CreateGroupAccumulatorRequest`

```json
{
  "accumulator_id": "preset-uuid",
  "title": "100 Million Mani Retreat 2024",
  "target_count": 100000000,
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `accumulator_id` | UUID | No | Link to a preset accumulator |
| `title` | string | No | Display title |
| `target_count` | int | No | Group goal (>= 1) |
| `start_date` | datetime | No | Practice period start |
| `end_date` | datetime | No | Practice period end |

**Response**: `201 Created` - `GroupAccumulatorDTO`

**Errors**:
- `404 NOT_FOUND` - Group not found
- `403 FORBIDDEN` - Insufficient permissions

---

### GET /cms/groups/{group_id}/accumulators

List all accumulators for a group (CMS view).

**Authentication**: Required (Bearer token - CMS author with read permission)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | UUID | Group ID |

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 20 | Max records (1-100) |

**Response**: `GroupAccumulatorsResponse`

---

### GET /cms/groups/{group_id}/accumulators/{group_accumulator_id}

Get a single group accumulator with total count.

**Authentication**: Required (Bearer token - CMS author with read permission)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | UUID | Group ID |
| `group_accumulator_id` | UUID | Group accumulator ID |

**Response**: `GroupAccumulatorDetailDTO`

**Errors**:
- `404 NOT_FOUND` - Group accumulator not found
- `403 FORBIDDEN` - Accumulator doesn't belong to this group or insufficient permissions

---

### PUT /cms/groups/{group_id}/accumulators/{group_accumulator_id}

Update a group accumulator.

**Authentication**: Required (Bearer token - CMS author with status change permission)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | UUID | Group ID |
| `group_accumulator_id` | UUID | Group accumulator ID |

**Request Body**: `UpdateGroupAccumulatorRequest`

```json
{
  "title": "Updated Title",
  "target_count": 200000000,
  "end_date": "2025-12-31T23:59:59Z"
}
```

**Response**: `GroupAccumulatorDTO`

**Errors**:
- `404 NOT_FOUND` - Group accumulator not found
- `403 FORBIDDEN` - Accumulator doesn't belong to this group or insufficient permissions

---

### DELETE /cms/groups/{group_id}/accumulators/{group_accumulator_id}

Delete a group accumulator (soft delete).

**Authentication**: Required (Bearer token - CMS author with status change permission)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | UUID | Group ID |
| `group_accumulator_id` | UUID | Group accumulator ID |

**Response**: `204 No Content`

**Errors**:
- `404 NOT_FOUND` - Group accumulator not found
- `403 FORBIDDEN` - Accumulator doesn't belong to this group or insufficient permissions

---

## Request/Response Schemas

### AccumulatorDTO

```typescript
interface AccumulatorDTO {
  id: string;                    // UUID
  user_id: string | null;        // UUID - owner (null for presets)
  group_id: string | null;       // UUID - associated group
  parent_id: string | null;      // UUID - preset this was created from
  type: "preset" | "user_created";
  target_count: number | null;   // Goal count
  current_count: number;         // Current accumulated count
  text_id: string | null;        // UUID - associated text
  mantra_id: string | null;      // UUID - associated mantra
  mala_image_id: string | null;  // UUID - chosen mala image
  mala_image_url: string | null; // Presigned S3 URL
  metadata: AccumulatorMetadataDTO[];
  created_at: string;            // ISO datetime
  updated_at: string | null;     // ISO datetime
}
```

### PublicAccumulatorDTO

```typescript
interface PublicAccumulatorDTO {
  id: string;                    // UUID - use as parent_id when creating
  group_id: string | null;       // UUID
  type: "preset" | "user_created";
  target_count: number | null;
  current_count: number;
  text_id: string | null;        // UUID
  mantra: PresetMantraDTO | null;
  mala_image_id: string | null;  // UUID
  mala_image_url: string | null; // Presigned S3 URL
  metadata: AccumulatorMetadataDTO[];
  created_at: string;            // ISO datetime
  updated_at: string | null;     // ISO datetime
}
```

### PresetMantraDTO

```typescript
interface PresetMantraDTO {
  id: string;                    // UUID
  mantra: string;                // Mantra text
  title: string | null;          // Display title
  pronunciation: string | null;  // Phonetic pronunciation
  audio_url: string | null;      // Audio file URL
  mala_image_id: string | null;  // UUID
  mala_image_url: string | null; // Presigned S3 URL
}
```

### AccumulatorMetadataDTO

```typescript
interface AccumulatorMetadataDTO {
  language: "EN" | "BO" | "ZH" | string;  // Language code
  name: string;                            // Display name
  description: string | null;              // Description
}
```

### AccumulatorHistoryDTO

```typescript
interface AccumulatorHistoryDTO {
  accumulator_id: string;        // UUID
  parent_id: string | null;      // UUID - preset reference
  target_count: number | null;
  current_count: number;
  total_counted: number;         // Sum of all history entries
  mala_image_id: string | null;  // UUID
  mala_image_url: string | null; // Presigned S3 URL
  metadata: AccumulatorMetadataDTO[];
  sessions: AccumulatorSessionDTO[];
}
```

### AccumulatorSessionDTO

```typescript
interface AccumulatorSessionDTO {
  count: number;                 // Count delta for this session
  created_at: string;            // ISO datetime
}
```

### GroupAccumulatorDTO

```typescript
interface GroupAccumulatorDTO {
  id: string;                    // UUID
  accumulator_id: string | null; // UUID - linked preset
  group_id: string;              // UUID - owning group
  title: string | null;          // Display title
  target_count: number | null;   // Group goal
  start_date: string | null;     // ISO datetime
  end_date: string | null;       // ISO datetime
  created_at: string;            // ISO datetime
  updated_at: string | null;     // ISO datetime
}
```

### GroupAccumulatorDetailDTO

```typescript
interface GroupAccumulatorDetailDTO extends GroupAccumulatorDTO {
  total_count: number;           // Sum of all contributions
}
```

### GroupAccumulatorHistoryItemDTO

```typescript
interface GroupAccumulatorHistoryItemDTO {
  id: string | null;             // UUID - null if no history created
  user_id: string;               // UUID - contributor
  count: number;                 // Count delta
  created_at: string;            // ISO datetime
}
```

### AccumulatorGroupDTO

```typescript
interface AccumulatorGroupDTO {
  group_accumulator_id: string;  // UUID
  group_id: string;              // UUID
  title: string | null;
  target_count: number | null;
  user_total_count: number;      // Authenticated user's contribution
  start_date: string | null;     // ISO datetime
  end_date: string | null;       // ISO datetime
  created_at: string;            // ISO datetime
}
```

---

## Common Workflows

### Workflow 1: User Starts Personal Practice

```
1. App displays preset list
   GET /accumulators/presets?language=en

2. User taps a preset to start practicing
   GET /accumulators/{preset_id}
   → Auto-creates user accumulator if needed
   → Returns accumulator with session history

3. User completes a counting session (e.g., 108 recitations)
   PUT /accumulators/user/{accumulator_id}
   Body: { "current_count": 108 }
   → History entry created with count=108

4. User continues practicing over time
   PUT /accumulators/user/{accumulator_id}
   Body: { "current_count": 216 }
   → History entry created with count=108 (delta)

5. User views their practice history
   GET /accumulators/user/history
```

### Workflow 2: User Joins Group Practice

```
1. User joins a group (separate API)

2. App displays group's accumulators
   GET /group-accumulators/{group_id}/accumulators

3. User views group accumulator details
   GET /group-accumulators/{group_accumulator_id}
   → Shows total_count from all contributors

4. User contributes their count
   POST /group-accumulators/{group_accumulator_id}
   Body: { "current_count": 5400 }
   → Creates history entry with delta
   → Returns 201 if new entry, 200 if no change

5. User views contribution history
   GET /group-accumulators/{group_accumulator_id}/history
```

### Workflow 3: CMS Author Creates Group Accumulator

```
1. Author authenticates via CMS

2. Author creates group accumulator for community practice
   POST /cms/groups/{group_id}/accumulators
   Body: {
     "accumulator_id": "preset-uuid",
     "title": "100 Million Mani Retreat 2024",
     "target_count": 100000000,
     "start_date": "2024-01-01T00:00:00Z",
     "end_date": "2024-12-31T23:59:59Z"
   }

3. Author monitors progress
   GET /cms/groups/{group_id}/accumulators/{id}
   → Shows total_count from all members

4. Author updates target or dates as needed
   PUT /cms/groups/{group_id}/accumulators/{id}
   Body: { "target_count": 200000000 }
```

### Workflow 4: User Checks Groups Using Their Preset

```
1. User has been practicing a specific mantra

2. User wants to see which groups are doing the same practice
   GET /accumulators/{accumulator_id}/groups
   → Returns list of group accumulators using this preset
   → Includes user's contribution count for each group
```

---

## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "detail": {
    "error": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `BAD_REQUEST` | Invalid request data |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Resource already exists |

### Specific Error Messages

| Context | Message |
|---------|---------|
| Accumulator not found | "Accumulator not found" |
| Preset not found | "Preset not found" |
| Mantra not found | "Mantra not found" |
| Mala image not found | "Mala image not found" |
| Group not found | "Group not found" |
| Group accumulator not found | "Group accumulator not found" |
| Not owner | "You are not allowed to update this accumulator" |
| Not user accumulator | "Only user-created accumulators can be updated" |
| Duplicate accumulator | "Accumulator already exists for this preset" |
| Not group member | "You must be a member of this group" |
| Wrong group | "Group accumulator does not belong to this group" |

---

## Notes for Frontend Developers

1. **Presigned URLs**: `mala_image_url` fields contain presigned S3 URLs that expire. Cache images locally but be prepared to refetch if loading fails.

2. **Count Updates**: Always send the absolute `current_count`, not the delta. The backend calculates the delta and creates history entries automatically.

3. **Auto-creation**: `GET /accumulators/{parent_id}` auto-creates a user accumulator if none exists. Use this for the "tap to start" flow.

4. **Group Membership**: Group accumulator contribution (`POST /group-accumulators/{id}`) requires the user to be a member of the group. Handle 403 errors appropriately.

5. **Pagination**: All list endpoints support `skip` and `limit` parameters. Default limit is 20, max is 100.

6. **Language Parameter**: Use `language` query param on `/accumulators/presets` to get mantra content in the user's preferred language.

7. **Soft Deletes**: Deleted accumulators are soft-deleted (`deleted_at` is set). History is preserved for the user's history page.
