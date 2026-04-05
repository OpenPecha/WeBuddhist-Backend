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

| Backend Endpoint           | Method | OpenPecha API Used                                                                                                                                                | Description                    |
|----------------------------|--------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|
| `/collections`             | GET    | `/v2/categories`                                                                                                                                                  | Get collections/categories     |
| `/texts`                   | GET    | `/v2/texts?limit=20&offset=0&category_id=text_category_id`                                                                                                        | Get texts by collection        |
| `/texts/{id}/versions`     | GET    | `/v2/texts/{text_id}`                                                                                                                                             | Get text versions              |
| `/texts/{id}/commentaries` | GET    | `/v2/texts/{text_id}`                                                                                                                                             | Get text commentaries          |
| `/texts/{id}/details`      | POST   | `/v2/texts/{text_id}/editions?edition_type=critical'`, `/v2/editions/{text_id}/annotations?type=segmentation&type=durchen'`, `/v2/editions/{edition_id}/content'` | Get text content details       |
| `/segments/{id}/info`      | GET    | `/v2/segments/{segment_id}/related`,  `/v2/segments/{segment_id}/content`                                                                                         | Get segment info               |

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
GET /v2/categories?application=webuddhist&language={language}
```

**Parameter Mapping:**

| Backend Param | OpenPecha Param | Notes                          |
|---------------|-----------------|--------------------------------|
| `language`    | `language`      | Direct mapping                 |
| `skip`        | -               | Deprecated                     |
| `limit`       | -               | Deprecated                     |
| -             | `application`   | Hardcoded as `webuddhist`      |

**Response Mapping:**

| Backend Response Field              | OpenPecha Response Field | Notes                                              |
|-------------------------------------|--------------------------|----------------------------------------------------|
| `collections[].id`                  | `categories[].id`        | Direct mapping                                     |
| `collections[].pecha_collection_id` | -                        | Will be deprecated since it will be same as id     |
| `collections[].title`               | `categories[].title`     | Get all titles (en, bo, zh)                        |
| `collections[].description`         | `categories[].description` | Dirrect mapping                                  |
| `collections[].language`            | -                        | Backend-only field (from request)                  |
| `collections[].slug`                | -                        | Will be deprecated                                 |
| `collections[].has_child`           | `categories[].childern ` | Direct mapping                                     |
| `pagination.total`                  | -                        | Will be deprecated                                 |
| `pagination.skip`                   | -                        | Will be deprecated                                 |
| `pagination.limit`                  | -                        | Will be deprecated                                 |
| -                                   | `categories[].parent_id` | Direct mapping                                     |

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
GET /v2/texts?language={language}&category_id={category_id}&limit=20&offset=0
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
| `collection.id`                    | -`text[].category_id`               | Mapped with pecha_collection_id       |
| `collection.pecha_collection_id`   | -                                   | Deprecated                            |
| `collection.title`                 | -                                   | Deprecated                            | 
|                                    | `v2/texts/{text_id}/editions`Response |Get text editions                    | 
| `texts[].id`                       | `editions[].id`                     | Maps to OpenPecha text ID             |
| `texts[].pecha_text_id`            | -                                   | Deprecated                            |
| `texts[].title`                    | `texts[].title`                     | Direct mapping                        |
| `texts[].language`                 | `texts[].language`                  | Direct mapping                        |
| `texts[].type`                     | -                                   | Direct mapping                        |
| `texts[].group_id`                 | -                                   | Need clarification                    |
| `texts[].summary`                  | -                                   | Deprecated since we don't use it      |
| `texts[].is_published`             | -                                   | To be removed                         |
| `texts[].created_date`             | -                                   | To be removed                         |
| `texts[].updated_date`             | -                                   | To be removed                         |
| `texts[].published_date`           | `texts[].date`                      | Direct mapping                        |
| `texts[].published_by`             | `texts[].contributions[]`           | List of contributator                 |
| `texts[].categories`               | `texts[].category_id`               | Direct mapping                        |
| `texts[].views`                    | -                                   | Backend-only field                    |
| `texts[].likes`                    | -                                   | Backend-only field                    |
| `texts[].source_link`              |`editions[].source`                  |                                       |
| `texts[].ranking`                  | -                                   | To be removed                         |
| `texts[].license`                  | `texts[].license`                   | Direct mapping                        |
| `total`                            | -                                   | Deprecated                            |
| `skip`                             | -                                   | Deprecated                            |
| `limit`                            | -                                   | Deprecated                            |
| -                                  | `text[].commentary_of`              | New field                             |
| -                                  | `texts[].commentaries[]`            | New field                             |
| -                                  | `texts[].translation_of`            | New field                             |
| -                                  | `texts[].translations`              | New field                             |
| -                                  | `texts[].wiki`                      | New field                             |
| -                                  | `texts[].bdrc`                      | New field                             |

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

**Response Mapping:**

| Backend Response Field             | OpenPecha Response Field            | Notes                                 |
|------------------------------------|-------------------------------------|---------------------------------------|
| `collection.id`                    | -`text[].category_id`               | Mapped with pecha_collection_id       |
| `collection.pecha_collection_id`   | -                                   | Deprecated                            |
| `collection.title`                 | -                                   | Deprecated                            | 
|                                    | `v2/texts/{text_id}/editions`Response |Get text editions                    | 
| `texts[].id`                       | `editions[].id`                     | Maps to OpenPecha text ID             |
| `texts[].pecha_text_id`            | -                                   | Deprecated                            |
| `texts[].title`                    | `texts[].title`                     | Direct mapping                        |
| `texts[].language`                 | `texts[].language`                  | Direct mapping                        |
| `texts[].type`                     | -                                   | Direct mapping                        |
| `texts[].group_id`                 | -                                   | Need clarification                    |
| `texts[].summary`                  | -                                   | Deprecated since we don't use it      |
| `texts[].is_published`             | -                                   | To be removed                         |
| `texts[].created_date`             | -                                   | To be removed                         |
| `texts[].updated_date`             | -                                   | To be removed                         |
| `texts[].published_date`           | `texts[].date`                      | Direct mapping                        |
| `texts[].published_by`             | `texts[].contributions[]`           | List of contributator                 |
| `texts[].categories`               | `texts[].category_id`               | Direct mapping                        |
| `texts[].views`                    | -                                   | Backend-only field                    |
| `texts[].likes`                    | -                                   | Backend-only field                    |
| `texts[].source_link`              |`editions[].source`                  |                                       |
| `texts[].ranking`                  | -                                   | To be removed                         |
| `texts[].license`                  | `texts[].license`                   | Direct mapping                        |
| `total`                            | -                                   | Deprecated                            |
| `skip`                             | -                                   | Deprecated                            |
| `limit`                            | -                                   | Deprecated                            |
| -                                  | `text[].commentary_of`              | New field                             |
| -                                  | `texts[].commentaries[]`            | New field                             |
| -                                  | `texts[].translation_of`            | New field                             |
| -                                  | `texts[].translations`              | New field                             |
| -                                  | `texts[].wiki`                      | New field                             |
| -                                  | `texts[].bdrc`                      | New field                             |

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

| Backend Response Field             | OpenPecha Response Field            | Notes                                 |
|------------------------------------|-------------------------------------|---------------------------------------|
| `collection.id`                    | -`text[].category_id`               | Mapped with pecha_collection_id       |
| `collection.pecha_collection_id`   | -                                   | Deprecated                            |
| `collection.title`                 | -                                   | Deprecated                            | 
|                                    | `v2/texts/{text_id}/editions`Response |Get text editions                    | 
| `texts[].id`                       | `editions[].id`                     | Maps to OpenPecha text ID             |
| `texts[].pecha_text_id`            | -                                   | Deprecated                            |
| `texts[].title`                    | `texts[].title`                     | Direct mapping                        |
| `texts[].language`                 | `texts[].language`                  | Direct mapping                        |
| `texts[].type`                     | -                                   | Direct mapping                        |
| `texts[].group_id`                 | -                                   | Need clarification                    |
| `texts[].summary`                  | -                                   | Deprecated since we don't use it      |
| `texts[].is_published`             | -                                   | To be removed                         |
| `texts[].created_date`             | -                                   | To be removed                         |
| `texts[].updated_date`             | -                                   | To be removed                         |
| `texts[].published_date`           | `texts[].date`                      | Direct mapping                        |
| `texts[].published_by`             | `texts[].contributions[]`           | List of contributator                 |
| `texts[].categories`               | `texts[].category_id`               | Direct mapping                        |
| `texts[].views`                    | -                                   | Backend-only field                    |
| `texts[].likes`                    | -                                   | Backend-only field                    |
| `texts[].source_link`              |`editions[].source`                  |                                       |
| `texts[].ranking`                  | -                                   | To be removed                         |
| `texts[].license`                  | `texts[].license`                   | Direct mapping                        |
| `total`                            | -                                   | Deprecated                            |
| `skip`                             | -                                   | Deprecated                            |
| `limit`                            | -                                   | Deprecated                            |
| -                                  | `text[].commentary_of`              | New field                             |
| -                                  | `texts[].commentaries[]`            | New field                             |
| -                                  | `texts[].translation_of`            | New field                             |
| -                                  | `texts[].translations`              | New field                             |
| -                                  | `texts[].wiki`                      | New field                             |
| -                                  | `texts[].bdrc`                      | New field                             |

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
**Maps to OpenPecha APIs:**
```
1. GET /v2/texts/{text_id}/editions?edition_type=critical                 → get edition ID
2. GET /v2/editions/{text_id}/annotations?type=segmentation&type=durchen  → get segmentation with segment spans and note/durchan span
3. GET /v2/editions/{edition_id}/content                                  → get text content
4. Base on Edition content and segmentation span we can generate segment's content 
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
   - Call `/v2/editions/{text_id}/annotations?type=segmentation&type=durchen`
   - Response contains:
     ```json
     {
       "segmentations": [{
         "id": "segmentation_id",
         "segments": [
           { "id": "seg1", "manifestation_id": "...", "text_id": "...", "lines": [{ "start": 0, "end": 51 }] },
           ...
         ]
       }],
       "durchen_notes": [
              {
            "id": "r1erhbb7CkkBlFd2vR7OR",
            "span": {
              "end": 501,
              "start": 494
            },
            "text": "དམར་མོ་] ༼སྣར་༽༼པེ་༽དམར་པོ་"
          }
       ]
     }
     ```

3. **Get Content per Segment**
   - For each segment in the paginated response, call `GET /v2/editions/{edition_id}/content`
   - Response is the raw text string for that segment

4. **Get Segment and note content**
  - Base on Edition content and segmentation span we can generate segment's content and note

**Parameter Mapping:**

| Backend Param  | OpenPecha Param    | Notes                                          |
|----------------|--------------------|------------------------------------------------|
| `text_id`      | `{text_id}`        | Path parameter                                 |
| `content_id`   | -                  | Table-of-contents anchor; backend pagination   |
| `direction`    | -                  | Backend pagination direction (`next`/`previous`)|
| `size`         | -                  | Maps to segment pagination limit               |


**Response Mapping:**

| Backend Response Field                         | OpenPecha Response Field           | Notes                                |
|------------------------------------------------|------------------------------------|--------------------------------------|
| `text_detail`                                  | `/v2/texts/{text_id}/edition` response | Text metadata                        |
| `text_detail.id`                               | `editions[].id`                       | Maps to OpenPecha text ID            |
| `text_detail.pecha_text_id`                    | -                                  | Deprecated                           |
| `text_detail.title`                            | `texts[].title`                    | Direct mapping                       |
| `text_detail.language`                         | `texts[].language`                 | Direct mapping                       |
| `text_detail.type`                             | -                                  | Deprecated                           |
| `text_detail.license`                          | `texts[].license`                  | Direct mapping                       |
| `content`                                      | `/v2/editions/{id}/annoations` response | Character span(s) within base text                  |
| `content.id`                                   | -                                  | Backend internal ID                  |
| `content.text_id`                              | -                                  | OpenPecha text ID                    |
| `content.sections[]`                           | -                                  | Backend structures annotations       |
| `content.sections[].id`                        | -                                  | Backend section ID                   |
| `content.sections[].title`                     | -                                  | Backend section title                |
| `content.sections[].section_number`            | -                                  | Backend ordering                     |
| -                                              | `/v2/editions/{edition_id}/content` response | Get basetext                         |
| `content.sections[].segments[]`                | `annotations[]`                    | Segment content from annotations and base text|
| `content.sections[].segments[].segment_id`     | `annotations[].annotation_id`      | Maps to annotation ID                |
| `content.sections[].segments[].segment_number` | `annotations[].order`              | Segment ordering                     |
| `content.sections[].segments[].content`        | `annotations[].content`            | Segment text content after splitting |
| `content.sections[].segments[].translation`    | -                                  | Need discussion                      |
| `size`                                         | `limit`                            | Page size                            |
| `pagination_direction`                         | -                                  | Backend pagination                   |
| `current_segment_position`                     | -                                  | Current position                     |
| `total_segments`                               | -                                  | Total segment count                  |

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
| `segment_info.translations`         | `targets[].count`        | Count where type=root_text/commentaries/translation       |
| `segment_info.related_text`         | -                        | Backend aggregation                |
| `segment_info.related_text.commentaries` | `targets[].count`   | Count where type=root_text/commentaries/translation        |
| `segment_info.related_text.root_text`    | `targets[].count`   | Count where type=root_text/commentaries/translation        |
| `segment_info.resources`            | -                        | Backend-only field                 |
| `segment_info.resources.sheets`     | -                        | Backend-only field                 |

---
