# Pecha Backend API Mapping

This document maps the **Pecha Backend APIs** (served to the frontend) to the **OpenPecha External APIs** (upstream data source).

---

## Overview

The Pecha Backend acts as a middleware that:
1. Fetches data from the OpenPecha external API
2. Transforms and enriches the data
3. Serves it to the frontend in the desired format

**Backend Base URL:** `/api/v1`  
**OpenPecha External API:** `https://api-aq25662yyq-uc.a.run.app/v2`

---

## API Mapping Table

| Backend Endpoint           | Method | OpenPecha API Used                        | Description                    |
|----------------------------|--------|-------------------------------------------|--------------------------------|
| `/collections`             | GET    | `/v2/categories`                                                         | Get collections/categories     |
| `/texts`                   | GET    | `/v2/categories/{id}/texts`                                              | Get texts by collection        |
| `/texts/{id}/versions`     | GET    | `/v2/texts/{id}/related-by-work`, `/v2/texts`                            | Get text versions              |
| `/texts/{id}/commentaries` | GET    | `/v2/texts/{id}/related-by-work`, `/v2/texts`                            | Get text commentaries          |
| `/texts/{id}/details`      | POST   | `/v2/texts/{id}/instances`, `/v2/instances/{id}`, `/v2/annotations/{id}`, `/v2/instances/{id}/content` | Get text content details       |
| `/segments/{id}/info`      | GET    | `/v2/segments/{id}/related`                                              | Get segment info               |

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
GET /v2/categories?application=webuddhist&language={language}&offset={skip}&limit={limit}
```

**Parameter Mapping:**

| Backend Param | OpenPecha Param | Notes                          |
|---------------|-----------------|--------------------------------|
| `language`    | `language`      | Direct mapping                 |
| `skip`        | `offset`        | Renamed parameter              |
| `limit`       | `limit`         | Direct mapping                 |
| -             | `application`   | Hardcoded as `webuddhist`      |

**Response Mapping:**

| Backend Response Field              | OpenPecha Response Field | Notes                                              |
|-------------------------------------|--------------------------|----------------------------------------------------|
| `collections[].id`                  | `categories[].id`        | Direct mapping                                     |
| `collections[].pecha_collection_id` | -                        | Will be deprecated since it will be same as id     |
| `collections[].title`               | `categories[].title`     | Direct mapping                                     |
| `collections[].description`         | -                        | Will be deprecated                                 |
| `collections[].language`            | -                        | Backend-only field (from request)                  |
| `collections[].slug`                | -                        | Will be deprecated                                 |
| `collections[].has_child`           | `categories[].has_child` | Direct mapping                                     |
| `pagination.total`                  | `total`                  | Nested under `pagination`                          |
| `pagination.skip`                   | `offset`                 | Renamed and nested                                 |
| `pagination.limit`                  | `limit`                  | Nested under `pagination`                          |

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
GET /v2/categories/{category_id}/texts?language={language}&offset={skip}&limit={limit}
```

**Parameter Mapping:**

| Backend Param   | OpenPecha Param | Notes                       |
|-----------------|-----------------|------------------------------|
| `collection_id` | `{category_id}` | Path parameter in OpenPecha  |
| `language`      | `language`      | Direct mapping               |
| `skip`          | `offset`        | Renamed parameter            |
| `limit`         | `limit`         | Direct mapping               |

**Response Mapping:**

| Backend Response Field             | OpenPecha Response Field            | Notes                                 |
|------------------------------------|-------------------------------------|---------------------------------------|
| `collection.id`                    | `categories.id`                     | Maps to OpenPecha collection ID       |
| `collection.pecha_collection_id`   | -                                   | Deprecated                            |
| `collection.title`                 | `categories.title`                | Direct mapping                        |
| `texts[].id`                       | `texts[].text_metadata.id`          | Maps to OpenPecha text ID             |
| `texts[].pecha_text_id`            | -                                   | Deprecated                            |
| `texts[].title`                    | `texts[].text_metadata.title`       | Direct mapping                        |
| `texts[].language`                 | `texts[].text_metadata.language`    | Direct mapping                        |
| `texts[].type`                     | `texts[].text_metadata.type`        | Direct mapping                        |
| `texts[].group_id`                 | -                                   | Need clarification                    |
| `texts[].summary`                  | -                                   | Deprecated since we don't use it      |
| `texts[].is_published`             | -                                   | To be removed                         |
| `texts[].created_date`             | -                                   | To be removed                         |
| `texts[].updated_date`             | -                                   | To be removed                         |
| `texts[].published_date`           | -                                   | To be removed                         |
| `texts[].published_by`             | -                                   | To be removed                         |
| `texts[].categories`               | `texts[].text_metadata.category_id` | Direct mapping                        |
| `texts[].views`                    | -                                   | Backend-only field                    |
| `texts[].likes`                    | -                                   | Backend-only field                    |
| `texts[].source_link`              | -                                   | To be removed                         |
| `texts[].ranking`                  | -                                   | To be removed                         |
| `texts[].license`                  | `texts[].text_metadata.license`     | Direct mapping                        |
| `total`                            | `total`                             | Direct mapping                        |
| `skip`                             | `offset`                            | Renamed                               |
| `limit`                            | `limit`                             | Direct mapping                        |

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
1. GET /v2/texts/{text_id}/related-by-work?relation=translation  → returns expression_ids
2. GET /v2/texts?ids={expression_ids}                            → get details for related texts
```

**API Call Flow:**
1. Call `/v2/texts/{text_id}/related-by-work` which returns:
   ```json
   {
     "{work_id}": {
       "relation": "translation",
       "expression_ids": ["id1", "id2", "id3"]
     }
   }
   ```
2. Filter entries where `relation` is `"translation"`
3. Extract `expression_ids` from filtered entries (values are text IDs)
4. Call `/v2/texts?ids=id1,id2,id3` with comma-separated IDs to get text details

**Parameter Mapping:**

| Backend Param | OpenPecha Param | Notes                              |
|---------------|-----------------|------------------------------------|
| `text_id`     | `{text_id}`     | Path parameter                     |
| `language`    | `language`      | Direct mapping                     |
| `skip`        | `offset`        | Renamed parameter                  |
| `limit`       | `limit`         | Direct mapping                     |

**Response Mapping:**

| Backend Response Field             | OpenPecha Response Field                 | Notes                            |
|------------------------------------|------------------------------------------|----------------------------------|
| `text`                             | `/v2/texts` response                     | To be removed                    |
| `text.id`                          | `texts[].text_metadata.id`               | To be removed                    |
| `text.pecha_text_id`               | -                                        | To be removed                    |
| `text.title`                       | `texts[].text_metadata.title`            | To be removed                    |
| `text.language`                    | `texts[].text_metadata.language`         | To be removed                    |
| `text.group_id`                    | -                                        | To be removed                    |
| `text.type`                        | `texts[].text_metadata.type`             | To be removed                    |
| `text.categories`                  | `texts[].text_metadata.category_id`      | To be removed                    |
| `text.license`                     | `texts[].text_metadata.license`          | To be removed                    |
| `versions[]`                       | `/v2/texts/{id}/related-by-work` response| Related texts as versions        |
| `versions[].id`                    | `texts[].text_metadata.id`               | Maps to OpenPecha text ID        |
| `versions[].title`                 | `texts[].text_metadata.title`            | Direct mapping                   |
| `versions[].language`              | `texts[].text_metadata.language`         | Direct mapping                   |
| `versions[].type`                  | `texts[].text_metadata.type`             | Direct mapping                   |
| `versions[].group_id`              | -                                        | Need clarification               |
| `versions[].table_of_contents`     | -                                        | Need clarification               |
| `versions[].is_published`          | -                                        | To be removed                    |
| `versions[].created_date`          | -                                        | To be removed                    |
| `versions[].updated_date`          | -                                        | To be removed                    |
| `versions[].published_date`        | -                                        | To be removed                    |
| `versions[].published_by`          | -                                        | To be removed                    |
| `versions[].source_link`           | -                                        | To be removed                    |
| `versions[].ranking`               | -                                        | To be removed                    |
| `versions[].license`               | `texts[].text_metadata.license`          | Direct mapping                   |

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
1. GET /v2/texts/{text_id}/related-by-work  → returns expression_ids
2. GET /v2/texts?ids={expression_ids}       → get details for commentaries
```

**API Call Flow:**
1. Call `/v2/texts/{text_id}/related-by-work` which returns:
   ```json
   {
     "{work_id}": {
       "relation": "commentary",
       "expression_ids": ["id1", "id2", "id3"]
     }
   }
   ```
2. Filter entries where `relation` is `"commentary"`
3. Extract `expression_ids` from filtered entries (values are text IDs)
4. Call `/v2/texts?ids=id1,id2,id3` with comma-separated IDs to get commentary details

**Parameter Mapping:**

| Backend Param | OpenPecha Param | Notes                              |
|---------------|-----------------|------------------------------------|
| `text_id`     | `{text_id}`     | Path parameter                     |
| `skip`        | `offset`        | Renamed parameter                  |
| `limit`       | `limit`         | Direct mapping                     |

**Response Mapping:**

| Backend Response Field                    | OpenPecha Response Field            | Notes                            |
|-------------------------------------------|-------------------------------------|----------------------------------|
| `commentaries[].id`                       | `texts[].text_metadata.id`          | Maps to OpenPecha text ID        |
| `commentaries[].pecha_text_id`            | -                                   | Deprecated                       |
| `commentaries[].title`                    | `texts[].text_metadata.title`       | Direct mapping                   |
| `commentaries[].language`                 | `texts[].text_metadata.language`    | Direct mapping                   |
| `commentaries[].group_id`                 | -                                   | Need clarification               |
| `commentaries[].type`                     | `texts[].text_metadata.type`        | Direct mapping                   |
| `commentaries[].summary`                  | -                                   | Deprecated                       |
| `commentaries[].is_published`             | -                                   | To be removed                    |
| `commentaries[].created_date`             | -                                   | To be removed                    |
| `commentaries[].updated_date`             | -                                   | To be removed                    |
| `commentaries[].published_date`           | -                                   | To be removed                    |
| `commentaries[].published_by`             | -                                   | To be removed                    |
| `commentaries[].categories`               | `texts[].text_metadata.category_id` | Direct mapping                   |
| `commentaries[].views`                    | -                                   | Backend-only field               |
| `commentaries[].likes`                    | -                                   | Backend-only field               |
| `commentaries[].source_link`              | -                                   | To be removed                    |
| `commentaries[].ranking`                  | -                                   | To be removed                    |
| `commentaries[].license`                  | `texts[].text_metadata.license`     | Direct mapping                   |

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
1. GET /v2/texts/{text_id}/instances?instance_type=critical  → get instance ID
2. GET /v2/instances/{instance_id}                           → get annotations
3. GET /v2/annotations/{annotation_id}                       → get segment span details
4. GET /v2/instances/{instance_id}/content?start={}&end={}   → get content by span
```

**API Call Flow:**

1. **Get Instance ID**
   - Call `GET /v2/texts/{text_id}/instances?instance_type=critical`
   - Extract `instance_id` from response

2. **Get Annotations List**
   - Call `GET /v2/instances/{instance_id}`
   - Extract `annotations[]` array containing annotation references with `annotation_id` and `type`
   - Filter for `type=segmentation` to get the segmentation annotation

3. **Get Segment Span Details**
   - Call `GET /v2/annotations/{annotation_id}` for the segmentation annotation
   - Response contains `data[]` array with segment objects:
     ```json
     {
       "id": "segment_id",
       "span": { "start": 0, "end": 51 }
     }
     ```
   - Use `offset` and `limit` for pagination through segments

4. **Get Content for Pagination Range**
   - Determine the starting span (`start`) from the first segment and ending span (`end`) from the last segment in the paginated response
   - Call `GET /v2/instances/{instance_id}/content?start={first_span_start}&end={last_span_end}` once to get all content for the pagination range
   - Response contains the full text content for the entire range:
     ```json
     {
       "id": "instance_id",
       "content": "Full text content for the pagination range...",
       "span": { "start": 0, "end": 500 }
     }
     ```

5. **Split Content into Segments**
   - Apply logic to split the fetched content into individual segment content using each segment's span coordinates
   - For each segment, extract substring: `content[segment.span.start - range_start : segment.span.end - range_start]`
   - Combine segment metadata with extracted content to build the final response

**Parameter Mapping:**

| Backend Param  | OpenPecha Param | Notes                                                    |
|----------------|-----------------|----------------------------------------------------------|
| `text_id`      | `{text_id}`     | Path parameter                                           |
| `content_id`   | -               | The unique identifier of table of content for the text   |
| `direction`    | -               | Backend pagination direction                             |
| `size`         | `limit`         | Maps to annotation limit                                 |

**Response Mapping:**

| Backend Response Field                         | OpenPecha Response Field           | Notes                                |
|------------------------------------------------|------------------------------------|--------------------------------------|
| `text_detail`                                  | `/v2/texts` response               | Text metadata                        |
| `text_detail.id`                               | `texts[].text_metadata.id`         | Maps to OpenPecha text ID            |
| `text_detail.pecha_text_id`                    | -                                  | Deprecated                           |
| `text_detail.title`                            | `texts[].text_metadata.title`      | Direct mapping                       |
| `text_detail.language`                         | `texts[].text_metadata.language`   | Direct mapping                       |
| `text_detail.type`                             | `texts[].text_metadata.type`       | Direct mapping                       |
| `text_detail.license`                          | `texts[].text_metadata.license`    | Direct mapping                       |
| `content`                                      | `/v2/annotations` response         | Aggregated content                   |
| `content.id`                                   | -                                  | Backend internal ID                  |
| `content.text_id`                              | -                                  | OpenPecha text ID                    |
| `content.sections[]`                           | -                                  | Backend structures annotations       |
| `content.sections[].id`                        | -                                  | Backend section ID                   |
| `content.sections[].title`                     | -                                  | Backend section title                |
| `content.sections[].section_number`            | -                                  | Backend ordering                     |
| `content.sections[].segments[]`                | `annotations[]`                    | Segment content from annotations     |
| `content.sections[].segments[].segment_id`     | `annotations[].annotation_id`      | Maps to annotation ID                |
| `content.sections[].segments[].segment_number` | `annotations[].order`              | Segment ordering                     |
| `content.sections[].segments[].content`        | `annotations[].content`            | Segment text content after splitting |
| `content.sections[].segments[].translation`    | -                                  | Need discussion                      |
| `size`                                         | `limit`                            | Page size                            |
| `pagination_direction`                         | -                                  | Backend pagination                   |
| `current_segment_position`                     | `offset`                           | Current position                     |
| `total_segments`                               | `total`                            | Total segment count                  |

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

**Maps to OpenPecha API:**
```
GET /v2/segments/{segment_id}/related
```

**Parameter Mapping:**

| Backend Param | OpenPecha Param  | Notes          |
|---------------|------------------|----------------|
| `segment_id`  | `{segment_id}`   | Path parameter |

**Response Mapping:**

| Backend Response Field              | OpenPecha Response Field | Notes                              |
|-------------------------------------|--------------------------|------------------------------------|
| `segment_info`                      | -                        | Backend wrapper object             |
| `segment_info.segment_id`           | `{segment_id}`           | From request path                  |
| `segment_info.text_id`              | -                        | OpenPecha text ID                  |
| `segment_info.translations`         | `targets[].count`        | Count where type=translation       |
| `segment_info.related_text`         | -                        | Backend aggregation                |
| `segment_info.related_text.commentaries` | `targets[].count`   | Count where type=commentary        |
| `segment_info.related_text.root_text`    | `targets[].count`   | Count where type=root_text         |
| `segment_info.resources`            | -                        | Backend-only field                 |
| `segment_info.resources.sheets`     | -                        | Backend-only field                 |

---
