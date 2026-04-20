# OpenPecha API v2 - Change Request Document

**Date:** April 5, 2026  
**Version:** 2.1.0  
**Status:** Proposed Changes  
**API Specification:** [openpecha_suggested_api.yaml](./openpecha_suggested_api.yaml)

---

## Overview

This document outlines the proposed changes to the OpenPecha API v2 specification. These changes aim to improve API consistency, extensibility, and developer experience.

---

## 1. Categories API Changes

### 1.1 Add GET Category by ID Endpoint

**Endpoint:** `GET /v2/categories/{category_id}`

**Change:** New endpoint added to retrieve a single category by its ID.

**Why Required:**
- Allows fetching specific category details without retrieving the entire list
- Reduces bandwidth and improves performance for single-item lookups
- Follows RESTful best practices for resource retrieval

**Response:** Returns `CategoryOutput` directly (no wrapper object for single items)

---

### 1.2 Wrap List Response in JSON Object

**Endpoint:** `GET /v2/categories`

**Change:** Response changed from raw JSON array to wrapped JSON object with pagination metadata.

**Before:**
```json
[
    { "id": "CAT123", "title": {...} },
    { "id": "CAT456", "title": {...} }
]
```

**After:**
```json
{
    "categories": [
        { "id": "CAT123", "title": {...} },
        { "id": "CAT456", "title": {...} }
    ],
    "total": 50,
    "limit": 20,
    "offset": 0
}
```

**Why Required:**
- **Extensibility:** Allows adding metadata fields (pagination, filters applied, etc.) without breaking changes
- **Consistency:** Establishes a standard pattern for all list endpoints
- **Pagination Support:** Enables proper pagination with total count for UI pagination controls
- **Future-proofing:** Raw arrays cannot be extended; objects can accommodate new fields

---

### 1.3 Add Pagination Parameters

**Endpoint:** `GET /v2/categories`

**Change:** Added `limit` and `offset` query parameters.

**Parameters:**
- `limit` (integer, default: 20, max: 100) - Number of results per page
- `offset` (integer, default: 0) - Number of results to skip

**Why Required:**
- Prevents performance issues with large datasets
- Enables efficient data loading in UI applications
- Standard pagination pattern for REST APIs

---

## 2. Texts API Changes

### 2.1 Wrap List Response in JSON Object

**Endpoint:** `GET /v2/texts`

**Change:** Response changed from raw JSON array to wrapped JSON object.

**After:**
```json
{
    "texts": [
        { "id": "T123", "title": {...}, "audio_url": "..." },
        { "id": "T456", "title": {...}, "audio_url": "..." }
    ],
    "total": 100,
    "limit": 20,
    "offset": 0
}
```

**Why Required:**
- Same reasons as Categories API (extensibility, consistency, pagination support)

---

### 2.2 Add Audio URL Field

**Schema:** `ExpressionOutput`

**Change:** Added `audio_url` field to the text output schema.

**Field Definition:**
```yaml
audio_url:
    type: string
    format: uri
    nullable: true
    description: CloudFront URL for the audio file (S3-backed)
    example: "https://d1234abcd.cloudfront.net/audio/T12345678.mp3"
```

**Why Required:**
- Texts have associated audio content stored in S3
- Audio is served via CloudFront CDN for performance
- Frontend applications need the URL to play audio content

---

### 2.3 Fix API Tags for Text Editions Endpoints

**Endpoints:**
- `GET /v2/texts/{text_id}/editions`
- `POST /v2/texts/{text_id}/editions`

**Change:** Moved from `Editions` tag to `Texts` tag.

**Why Required:**
- These endpoints operate on editions *belonging to a specific text*
- Logically grouped under Texts for better API documentation organization
- Improves discoverability in API documentation (Swagger/OpenAPI viewers)

---

### 2.4 Reorder Endpoints in Specification

**Change:** Moved `/v2/texts/{text_id}/editions` to appear after `/v2/texts/{text_id}` in the spec.

**Why Required:**
- Logical grouping of related endpoints
- Improves readability of API documentation
- All text-related endpoints are now consecutive

---

### 2.5 Wrap Editions List Response with Pagination

**Endpoint:** `GET /v2/texts/{text_id}/editions`

**Change:** 
1. Response wrapped in JSON object with `editions` array
2. Added pagination parameters (`limit`, `offset`)
3. Added pagination metadata in response (`total`, `limit`, `offset`)

**After:**
```json
{
    "editions": [
        { "id": "E123", "type": "diplomatic", ... },
        { "id": "E456", "type": "critical", ... }
    ],
    "total": 5,
    "limit": 20,
    "offset": 0
}
```

**Why Required:**
- Consistency with other list endpoints
- Pagination support for texts with many editions
- Extensibility for future metadata fields

---

## Summary of New Schemas Added

| Schema Name | Purpose |
|-------------|---------|
| `CategoriesListResponse` | Wrapper for paginated categories list |
| `TextsListResponse` | Wrapper for paginated texts list |
| `EditionsListResponse` | Wrapper for paginated editions list |

---

## Breaking Changes

| Endpoint | Change Type | Impact |
|----------|-------------|--------|
| `GET /v2/categories` | Response structure | Clients must access `.categories` array instead of root array |
| `GET /v2/texts` | Response structure | Clients must access `.texts` array instead of root array |
| `GET /v2/texts/{text_id}/editions` | Response structure | Clients must access `.editions` array instead of root array |

---

## Migration Guide for Frontend Developers

### Before (Old Response)
```javascript
const response = await fetch('/v2/texts');
const texts = await response.json();
texts.forEach(text => console.log(text.title));
```

### After (New Response)
```javascript
const response = await fetch('/v2/texts');
const data = await response.json();
data.texts.forEach(text => console.log(text.title));

// Pagination info available
console.log(`Showing ${data.texts.length} of ${data.total} texts`);
```

---

## Notes

- The `nullable` property warnings in the OpenAPI spec are pre-existing (OpenAPI 3.1 uses `type: ["string", "null"]` syntax instead). These should be addressed in a separate cleanup task.
- All single-item GET endpoints (e.g., `GET /v2/texts/{text_id}`) return the resource directly without a wrapper object.
