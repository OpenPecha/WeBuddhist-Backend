# Pecha Backend API Mapping

This document maps the **Pecha Backend APIs** (served to the frontend) to the **OpenPecha External APIs** (upstream data source).

---

## Overview

The Pecha Backend acts as a middleware that:
1. Fetches data from the OpenPecha external API
2. Transforms and enriches the data
3. Serves it to the frontend in the desired format

**Backend Base URL:** `/api/v1`  
**OpenPecha External API:** `https://api-l25bgmwqoa-uc.a.run.app/v2`
https://api-l25bgmwqoa-uc.a.run.app/v2


---

## API Mapping Table

| Backend Endpoint           | Method | OpenPecha API Used                        | Description                    |
|----------------------------|--------|-------------------------------------------|--------------------------------|
| `/collections`             | GET    | `/v2/categories`                                                         | Get collections/categories     |
| `/texts`                   | GET    | `/v2/texts?limit=20&offset=0&category_id=text_category_id`                                                        | Get texts by collection        |
| `/texts/{id}/versions`     | GET    | `/v2/texts/{text_id}`                            | Get text versions              |
| `/texts/{id}/commentaries` | GET    | `/v2/texts/{text_id}`                            | Get text commentaries          |
| `/texts/{id}/details`      | POST   | `/v2/texts/{text_id}/editions?edition_type=critical'`, `/v2/editions/{text_id}/annotations?type=segmentation&type=durchen'`, `v2/segments/{segment_id}/content'` | Get text content details       |
| `/segments/{id}/info`      | GET    | `/v2/segments/{segment_id}/related`,  `/v2/segments/{segment_id}/content`                                              | Get segment info               |

---

## Detailed Mapping

### 1. Collections

#### GET `/collections`

**Purpose:** Get collections/categories list

**Backend Request:**
```bash
curl -X 'GET' \
  'https://webuddhist-dev-backend.onrender.com/api/v1/collections?language=bo&skip=0&limit=10' \
  -H 'accept: application/json'
```

**Query Parameters:**

| Parameter  | Type   | Required | Description                     |
|------------|--------|----------|---------------------------------|
| `language` | string | No       | Language code (e.g., `bo`, `en`)|
| `skip`     | int    | No       | Number of records to skip       |
| `limit`    | int    | No       | Number of records to return     |

**Maps to OpenPecha API:**
```
GET /v2/categories?parent_id={parent_id}&language={language}
```

**Parameter Mapping:**

| Backend Param   | OpenPecha Param | Notes                                    |
|-----------------|-----------------|------------------------------------------|
| `collection_id` | `parent_id`     | Renamed; used to browse sub-collections  |
| `language`      | `language`      | Direct mapping (default: `bo`)           |

**Response Mapping:**

| Backend Response Field       | OpenPecha Response Field   | Notes                                    |
|------------------------------|----------------------------|------------------------------------------|
| `collections[].id`           | `[].id`                    | Direct mapping                           |
| `collections[].title`        | `[].title`                 | LocalizedString (dict of lang → text)    |
| `collections[].description`  | `[].description`           | LocalizedString, nullable                |
| `collections[].parent_id`    | `[].parent_id`             | Direct mapping, nullable                 |
| `collections[].children`     | `[].children`              | List of child category IDs              |

---

### 2. Texts

#### GET `/texts`

**Purpose:** Get texts by collection ID

**Backend Request:**
```bash
curl -X 'GET' \
  'https://webuddhist-dev-backend.onrender.com/api/v1/texts?collection_id=695ba4cc18ac3cb694f37285&language=bo&skip=0&limit=10' \
  -H 'accept: application/json'
```

**Query Parameters:**

| Parameter       | Type   | Required | Description                      |
|-----------------|--------|----------|----------------------------------|
| `collection_id` | string | No       | Need to be mapped to category_id |
| `language`      | string | No       | Language code (e.g., `bo`, `en`) |
| `skip`          | int    | No       | Number of records to skip        |
| `limit`         | int    | No       | Number of records to return      |

**Maps to OpenPecha API:**
```
GET /v2/texts?category_id={collection_id}&language={language}&offset={skip}&limit={limit}
```

**Parameter Mapping:**

| Backend Param   | OpenPecha Param | Notes                       |
|-----------------|-----------------|------------------------------|
| `collection_id` | `category_id`   | Query parameter in OpenPecha |
| `language`      | `language`      | Direct mapping               |
| `skip`          | `offset`        | Renamed parameter            |
| `limit`         | `limit`         | Direct mapping               |

**Response Mapping:**

| Backend Response Field   | OpenPecha Response Field | Notes                                                          |
|--------------------------|--------------------------|----------------------------------------------------------------|
| `texts[].id`             | `[].id`                  | Direct mapping                                                 |
| `texts[].title`          | `[].title`               | LocalizedString (dict of lang → text)                          |
| `texts[].language`       | `[].language`            | Direct mapping                                                 |
| `texts[].category_id`    | `[].category_id`         | Direct mapping                                                 |
| `texts[].license`        | `[].license`             | Direct mapping                                                 |
| `texts[].commentary_of`  | `[].commentary_of`       | ID of the root text; set when this text is a commentary        |
| `texts[].translation_of` | `[].translation_of`      | ID of the root text; set when this text is a translation       |
| `texts[].translations`   | `[].translations`        | List of translation expression IDs                             |
| `texts[].commentaries`   | `[].commentaries`        | List of commentary expression IDs                              |
| `texts[].editions`       | `[].editions`            | List of manifestation IDs                                      |
| `texts[].contributions`  | `[].contributions`       | List of contributor objects (person_id/person_bdrc_id + role)  |

---

#### GET `/texts/{text_id}/versions`

**Purpose:** Get text versions/translations for a specific text

**Backend Request:**
```bash
curl -X 'GET' \
  'https://webuddhist.com/api/v1/texts/ce0a5191-ea72-4e94-a270-1923d07e4d8e/versions?language=bo&limit=10&skip=0' \
  -H 'accept: application/json'
```

**Path Parameters:**

| Parameter | Type   | Required | Description                  |
|-----------|--------|----------|------------------------------|
| `text_id` | string | Yes      | The unique identifier of text|

**Query Parameters:**

| Parameter  | Type   | Required | Description                      |
|------------|--------|----------|----------------------------------|
| `language` | string | No       | Language code (e.g., `bo`, `en`) |
| `skip`     | int    | No       | Number of records to skip        |
| `limit`    | int    | No       | Number of records to return      |

**Maps to OpenPecha APIs:**
```
1. GET /v2/texts/{text_id}          → get expression; extract translations[] IDs
2. GET /v2/texts/{version_id}       → get full details for each version ID
```

**API Call Flow:**
1. Call `GET /v2/texts/{text_id}` which returns an `ExpressionOutput`:
   ```json
   {
     "id": "text_id",
     "translations": ["id1", "id2", "id3"],
     ...
   }
   ```
2. Extract the `translations` array (list of expression IDs)
3. For each ID, call `GET /v2/texts/{id}` to get full version details

**Parameter Mapping:**

| Backend Param | OpenPecha Param | Notes                 |
|---------------|-----------------|-----------------------|
| `text_id`     | `{text_id}`     | Path parameter        |
| `language`    | `language`      | Filter on step 2 call |
| `skip`        | `offset`        | Pagination on step 2  |
| `limit`       | `limit`         | Pagination on step 2  |

**Response Mapping:**

| Backend Response Field   | OpenPecha Response Field | Notes                                           |
|--------------------------|--------------------------|-------------------------------------------------|
| `versions[].id`          | `[].id`                  | Direct mapping                                  |
| `versions[].title`       | `[].title`               | LocalizedString                                 |
| `versions[].language`    | `[].language`            | Direct mapping                                  |
| `versions[].category_id` | `[].category_id`         | Direct mapping                                  |
| `versions[].license`     | `[].license`             | Direct mapping                                  |
| `versions[].editions`    | `[].editions`            | List of manifestation IDs for this version      |
| `versions[].translation_of` | `[].translation_of`   | ID of the root text this version translates     |

---

### 4. Text Commentaries

#### GET `/texts/{text_id}/commentaries`

**Purpose:** Get commentaries for a specific text

**Backend Request:**
```bash
curl -X 'GET' \
  'https://webuddhist-dev-backend.onrender.com/api/v1/texts/ce0a5191-ea72-4e94-a270-1923d07e4d8e/commentaries?skip=0&limit=10' \
  -H 'accept: application/json'
```

**Path Parameters:**

| Parameter | Type   | Required | Description                  |
|-----------|--------|----------|------------------------------|
| `text_id` | string | Yes      | The unique identifier of text|

**Query Parameters:**

| Parameter | Type | Required | Description                 |
|-----------|------|----------|-----------------------------|
| `skip`    | int  | No       | Number of records to skip   |
| `limit`   | int  | No       | Number of records to return |

**Maps to OpenPecha APIs:**
```
1. GET /v2/texts/{text_id}           → get expression; extract commentaries[] IDs
2. GET /v2/texts/{commentary_id}     → get full details for each commentary ID
```

**API Call Flow:**
1. Call `GET /v2/texts/{text_id}` which returns an `ExpressionOutput`:
   ```json
   {
     "id": "text_id",
     "commentaries": ["id1", "id2", "id3"],
     ...
   }
   ```
2. Extract the `commentaries` array (list of expression IDs)
3. For each ID, call `GET /v2/texts/{id}` to get full commentary details

**Parameter Mapping:**

| Backend Param | OpenPecha Param | Notes                 |
|---------------|-----------------|-----------------------|
| `text_id`     | `{text_id}`     | Path parameter        |
| `skip`        | `offset`        | Pagination on step 2  |
| `limit`       | `limit`         | Pagination on step 2  |

**Response Mapping:**

| Backend Response Field          | OpenPecha Response Field | Notes                                        |
|---------------------------------|--------------------------|----------------------------------------------|
| `commentaries[].id`             | `[].id`                  | Direct mapping                               |
| `commentaries[].title`          | `[].title`               | LocalizedString                              |
| `commentaries[].language`       | `[].language`            | Direct mapping                               |
| `commentaries[].category_id`    | `[].category_id`         | Direct mapping                               |
| `commentaries[].license`        | `[].license`             | Direct mapping                               |
| `commentaries[].editions`       | `[].editions`            | List of manifestation IDs for this commentary|
| `commentaries[].commentary_of`  | `[].commentary_of`       | ID of the root text this commentary is about |

---

### 5. Text Details

#### POST `/texts/{text_id}/details`

**Purpose:** Get text content with segments (paginated)

**Backend Request:**
```bash
curl -X 'POST' \
  'https://api.webuddhist.com/api/v1/texts/ce0a5191-ea72-4e94-a270-1923d07e4d8e/details' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"content_id":"40dd0f80-8453-4a1c-b896-fba23ad598da","direction":"next","size":20}'
```

**Path Parameters:**

| Parameter | Type   | Required | Description                  |
|-----------|--------|----------|------------------------------|
| `text_id` | string | Yes      | The unique identifier of text|

**Request Body:**

| Field        | Type   | Required | Description                                |
|--------------|--------|----------|--------------------------------------------|
| `content_id` | string | No       | The unique identifier of table of content for the text |
| `direction`  | string | No       | Pagination direction (`next` or `previous`)|
| `size`       | int    | No       | Number of segments to return               |

**Maps to OpenPecha APIs:**
```
1. GET /v2/texts/{text_id}/editions?edition_type=critical   → get manifestation ID
2. GET /v2/editions/{manifestation_id}/annotations?type=segmentation  → get segmentation with segment spans
3. GET /v2/segments/{segment_id}/content                    → get text content per segment
```

**API Call Flow:**

1. **Get Edition (Manifestation) ID**
   - Call `GET /v2/texts/{text_id}/editions?edition_type=critical`
   - Response is a list of `ManifestationOutput`:
     ```json
     [{ "id": "manifestation_id", "text_id": "...", "type": "critical", ... }]
     ```
   - Extract `id` (`manifestation_id`) from the first result

2. **Get Segmentation Annotation**
   - Call `GET /v2/editions/{manifestation_id}/annotations?type=segmentation`
   - Response contains:
     ```json
     {
       "segmentations": [{
         "id": "segmentation_id",
         "segments": [
           { "id": "seg1", "manifestation_id": "...", "text_id": "...", "lines": [{ "start": 0, "end": 51 }] },
           ...
         ]
       }]
     }
     ```
   - Use `offset` and `limit` to paginate through `segments[]`

3. **Get Content per Segment**
   - For each segment in the paginated response, call `GET /v2/segments/{segment_id}/content`
   - Response is the raw text string for that segment

**Parameter Mapping:**

| Backend Param  | OpenPecha Param    | Notes                                          |
|----------------|--------------------|------------------------------------------------|
| `text_id`      | `{text_id}`        | Path parameter                                 |
| `content_id`   | -                  | Table-of-contents anchor; backend pagination   |
| `direction`    | -                  | Backend pagination direction (`next`/`previous`)|
| `size`         | `limit`            | Maps to segment pagination limit               |

**Response Mapping:**

| Backend Response Field                         | OpenPecha Response Field                     | Notes                                    |
|------------------------------------------------|----------------------------------------------|------------------------------------------|
| `text_detail.id`                               | `ExpressionOutput.id`                        | Direct mapping                           |
| `text_detail.title`                            | `ExpressionOutput.title`                     | LocalizedString                          |
| `text_detail.language`                         | `ExpressionOutput.language`                  | Direct mapping                           |
| `text_detail.license`                          | `ExpressionOutput.license`                   | Direct mapping                           |
| `content.sections[].segments[].segment_id`     | `SegmentOutput.id`                           | Direct mapping                           |
| `content.sections[].segments[].content`        | `GET /v2/segments/{id}/content` response     | Raw text string                          |
| `content.sections[].segments[].lines`          | `SegmentOutput.lines[].{start, end}`         | Character span(s) within base text       |
| `size`                                         | `limit`                                      | Page size                                |
| `pagination_direction`                         | -                                            | Backend pagination                       |
| `current_segment_position`                     | `offset`                                     | Current position in segment list         |
| `total_segments`                               | total count from `segmentations[0].segments` | Total segment count                      |

---

### 6. Segment Info

#### GET `/segments/{segment_id}/info`

**Purpose:** Get segment information including translation count and related texts

**Backend Request:**
```bash
curl -X 'GET' \
  'https://api.webuddhist.com/api/v1/segments/9c08214d-c941-4c3d-b2a2-461d824eea57/info' \
  -H 'accept: application/json'
```

**Path Parameters:**

| Parameter    | Type   | Required | Description                     |
|--------------|--------|----------|---------------------------------|
| `segment_id` | string | Yes      | The unique identifier of segment|

**Maps to OpenPecha APIs:**
```
1. GET /v2/segments/{segment_id}/related   → get related segments from other manifestations
2. GET /v2/segments/{segment_id}/content   → get the text content of the segment
```

**Parameter Mapping:**

| Backend Param | OpenPecha Param  | Notes          |
|---------------|------------------|----------------|
| `segment_id`  | `{segment_id}`   | Path parameter |

**API Call Flow:**
1. Call `GET /v2/segments/{segment_id}/related` — returns `list[SegmentOutput]` representing aligned segments in other manifestations (translations, commentaries, etc.)
2. Call `GET /v2/segments/{segment_id}/content` — returns the raw text string for this segment

**Response Mapping:**

| Backend Response Field                    | OpenPecha Response Field              | Notes                                            |
|-------------------------------------------|---------------------------------------|--------------------------------------------------|
| `segment_info.segment_id`                 | `SegmentOutput.id`                    | From request path                                |
| `segment_info.text_id`                    | `SegmentOutput.text_id`               | Expression ID the segment belongs to             |
| `segment_info.manifestation_id`           | `SegmentOutput.manifestation_id`      | Manifestation the segment belongs to             |
| `segment_info.content`                    | `GET .../content` response            | Raw text string for this segment                 |
| `segment_info.lines`                      | `SegmentOutput.lines[].{start, end}`  | Character span(s) within the base text           |
| `segment_info.related_segments[]`         | `GET .../related` response            | Aligned segments from other manifestations       |
| `segment_info.related_segments[].id`      | `SegmentOutput.id`                    | ID of the related segment                        |
| `segment_info.related_segments[].text_id` | `SegmentOutput.text_id`               | Expression ID for the related segment's text     |
| `segment_info.resources`                  | -                                     | Backend-only field                               |

---
