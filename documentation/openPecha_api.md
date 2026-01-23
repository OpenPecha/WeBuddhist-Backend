# OpenPecha API Documentation

> **Note:** This document describes the **external/upstream OpenPecha API** that the Pecha backend consumes as a data source. The backend fetches data from these endpoints, transforms it, and serves it to the frontend in the desired format.

This document provides usage examples for the OpenPecha API endpoints.

**Base URL:** `https://api-aq25662yyq-uc.a.run.app`

**API Version:** `v2` - All endpoints are prefixed with `/v2`. This version includes pagination support, language filtering, and improved response structures.

---

## Table of Contents

- [Categories](#categories)
  - [Get Categories](#get-categories)
  - [Get Texts by Category](#get-texts-by-category)
- [Texts](#texts)
  - [Get Texts](#get-texts)
  - [Get Related Texts by Work](#get-related-texts-by-work)
- [Instances](#instances)
  - [Get Instance](#get-instance)
  - [Get Instance Content](#get-instance-content)
- [Annotations](#annotations)
  - [Get Annotation](#get-annotation)
- [Segments](#segments)
  - [Get Related Segments](#get-related-segments)

---

## Categories

### Get Categories

Retrieves a list of categories for a specific application.

**Endpoint:** `GET /v2/categories`

**Query Parameters:**

| Parameter     | Type    | Required  | Description                                                                    |
|---------------|---------|-----------|--------------------------------------------------------------------------------|
| `application` | string  | Yes       | The application identifier (e.g., `webuddhist`)                                |
| `language`    | string  | No        | Language code for title translation (e.g., `bo`, `en`, `zh`). Defaults to `bo` |
| `offset`      | integer | No        | Number of records to skip for pagination. Defaults to `0`                      |
| `limit`       | integer | No        | Maximum number of records to return. Defaults to `10`, max `100`               |

**Headers:**

| Header   | Value              |
|----------|--------------------|
| `Accept` | `application/json` |

**Example Request:**

```bash
curl -X 'GET' \
  'https://api-aq25662yyq-uc.a.run.app/v2/categories?application=webuddhist&language=bo&offset=0&limit=10' \
  -H 'accept: application/json'
```

**Example Response:**

```json
{
  "categories": [
    {
      "id": "rw8oWUd1WtwqeD2x0ZMSm",
      "parent": null,
      "title": "མདོ་སྡེ།",
      "has_child": false
    },
    {
      "id": "D91TlgRqpZGCOfywaHRvV",
      "parent": null,
      "title": "ཤེར་ཕྱིན།",
      "has_child": false
    },
    {
      "id": "kj8dljKGdBUuL4GkkVXbB",
      "parent": null,
      "title": "དབུ་མ།",
      "has_child": false
    }
  ],
  "total": 15,
  "offset": 0,
  "limit": 10
}
```

**Response Schema:**

| Field        | Type    | Description                          |
|--------------|---------|--------------------------------------|
| `categories` | array   | Array of category objects            |
| `total`      | integer | Total number of categories available |
| `offset`     | integer | Number of records skipped            |
| `limit`      | integer | Maximum records returned per request |

**Category Object:**

| Field       | Type           | Description                                             |
|-------------|----------------|---------------------------------------------------------|
| `id`        | string         | Unique identifier for the category                      |
| `parent`    | string \| null | Parent category ID (null for root categories)           |
| `title`     | string         | Category title (translated based on language parameter) |
| `has_child` | boolean        | Whether the category has child categories               |

**Response Codes:**

| Code  | Description                                            |
|-------|--------------------------------------------------------|
| `200` | Successful response with categories list               |
| `400` | Bad request - missing or invalid application parameter |
| `500` | Internal server error                                  |

---

### Get Texts by Category

Retrieves a list of texts belonging to a specific category.

**Endpoint:** `GET /v2/categories/{category_id}/texts`

**Path Parameters:**

| Parameter     | Type   | Required  | Description                           |
|---------------|--------|-----------|---------------------------------------|
| `category_id` | string | Yes       | The unique identifier of the category |

**Query Parameters:**

| Parameter      | Type    | Required | Description                                                      |
|----------------|---------|----------|------------------------------------------------------------------|
| `edition_type` | string  | No       | Filter by edition type (e.g., `critical`)                        |
| `type`         | string  | No       | Filter by text type (e.g., `translation`, `root`)                |
| `language`     | string  | No       | Language code for text titles (e.g., `bo`, `en`, `zh`)           |
| `offset`       | integer | No       | Number of records to skip for pagination. Defaults to `0`        |
| `limit`        | integer | No       | Maximum number of records to return. Defaults to `20`, max `100` |

**Headers:**

| Header   | Value              |
|----------|--------------------|
| `Accept` | `application/json` |

**Example Request:**

```bash
curl -X 'GET' \
  'https://api-aq25662yyq-uc.a.run.app/v2/categories/kj8dljKGdBUuL4GkkVXbB/texts?limit=20&offset=0&edition_type=critical' \
  -H 'accept: application/json'
```

**Example Response:**

```json
{
  "texts": [
    {
      "text_metadata": {
        "id": "rAEGbNlKaD8VxNO6qP4d2",
        "bdrc": null,
        "wiki": null,
        "type": "translation",
        "contributions": [],
        "date": null,
        "title": {
          "en": "The Way of the Bodhisattva"
        },
        "alt_titles": null,
        "language": "en",
        "target": "PqT7jXsnVDBWUJIUtPXw9",
        "category_id": "kj8dljKGdBUuL4GkkVXbB",
        "copyright": "Public domain",
        "license": "unknown"
      },
      "instance_metadata": [
        {
          "id": "XVqq55pnANEKri9536Wa4",
          "bdrc": null,
          "copyright": null,
          "incipit_title": null,
          "type": "critical",
          "wiki": null,
          "alt_incipit_titles": null,
          "colophon": null
        }
      ]
    }
  ],
  "total": 100,
  "offset": 0,
  "limit": 20
}
```

**Response Schema:**

| Field    | Type    | Description                                      |
|----------|---------|--------------------------------------------------|
| `texts`  | array   | Array of text objects containing metadata        |
| `total`  | integer | Total number of texts available in this category |
| `offset` | integer | Number of records skipped                        |
| `limit`  | integer | Maximum records returned per request             |

**Text Object:**

| Field               | Type   | Description                           |
|---------------------|--------|---------------------------------------|
| `text_metadata`     | object | Metadata about the text               |
| `instance_metadata` | array  | Array of edition/instance information |

**Text Metadata Object:**

| Field           | Type           | Description                                          |
|-----------------|----------------|------------------------------------------------------|
| `id`            | string         | Unique identifier for the text                       |
| `bdrc`          | string \| null | Buddhist Digital Resource Center identifier          |
| `wiki`          | string \| null | Wikipedia/Wikidata identifier                        |
| `type`          | string         | Type of text (e.g., `translation`, `root`)           |
| `contributions` | array          | List of contributors                                 |
| `date`          | string \| null | Date of the text                                     |
| `title`         | object         | Title in different languages (e.g., `{"en": "..."}`) |
| `alt_titles`    | array \| null  | Alternative titles                                   |
| `language`      | string         | Primary language of the text                         |
| `target`        | string         | Target text ID (for translations)                    |
| `category_id`   | string         | Category this text belongs to                        |
| `copyright`     | string         | Copyright status                                     |
| `license`       | string         | License type                                         |

**Instance Metadata Object:**

| Field                | Type           | Description                                   |
|----------------------|----------------|-----------------------------------------------|
| `id`                 | string         | Unique identifier for the instance            |
| `bdrc`               | string \| null | BDRC identifier for this instance             |
| `copyright`          | string \| null | Copyright for this instance                   |
| `incipit_title`      | string \| null | Opening title of the text                     |
| `type`               | string         | Edition type (e.g., `critical`, `diplomatic`) |
| `wiki`               | string \| null | Wikipedia/Wikidata identifier                 |
| `alt_incipit_titles` | array \| null  | Alternative incipit titles                    |
| `colophon`           | string \| null | Colophon text                                 |

**Response Codes:**

| Code  | Description                         |
|-------|-------------------------------------|
| `200` | Successful response with texts list |
| `400` | Bad request - invalid parameters    |
| `404` | Category not found                  |
| `500` | Internal server error               |

---

## Texts

### Get Texts

Retrieves a list of texts with optional filtering.

**Endpoint:** `GET /v2/texts`

**Query Parameters:**

| Parameter      | Type    | Required  | Description                                                      |
|----------------|---------|-----------|------------------------------------------------------------------|
| `ids`          | string  | No        | Comma-separated list of text IDs to retrieve specific texts      |
| `type`         | string  | No        | Filter by text type (e.g., `root`, `translation`)                |
| `edition_type` | string  | No        | Filter by edition type (e.g., `critical`)                        |
| `language`     | string  | No        | Language code for text titles (e.g., `bo`, `en`, `zh`)           |
| `offset`       | integer | No        | Number of records to skip for pagination. Defaults to `0`        |
| `limit`        | integer | No        | Maximum number of records to return. Defaults to `20`, max `100` |

**Headers:**

| Header   | Value              |
|----------|--------------------|
| `Accept` | `application/json` |

**Example Request:**

```bash
curl -X 'GET' \
  'https://api-aq25662yyq-uc.a.run.app/v2/texts?limit=20&offset=0&type=root' \
  -H 'accept: application/json'
```

**Example Response:**

```json
{
  "texts": [
    {
      "id": "SuEjB3HRx4X1FM5fgBOsQ",
      "bdrc": "WA0RT3427",
      "wiki": null,
      "type": "root",
      "contributions": [
        {
          "person_id": "He26LwRnoXfLyNBoFuAKg",
          "person_bdrc_id": "P6119",
          "role": "author",
          "person_name": {
            "bo": "སློབ་དཔོན་དབྱིག་གཉེན།",
            "sa": "Vasubandhu",
            "lzh": "世亲"
          }
        },
        {
          "person_id": "8M3R5xSmyUFdMETyGVgkA",
          "person_bdrc_id": "P8182",
          "role": "translator",
          "person_name": {
            "bo": "སྐ་བ་དཔལ་བརྩེགས།"
          }
        }
      ],
      "date": null,
      "title": {
        "bo": "ཆོས་མངོན་པའི་མཛོད་ཀྱི་ཚིག་ལེའུར་བྱས་པ།"
      },
      "alt_titles": null,
      "language": "bo",
      "target": null,
      "category_id": "iGzbJ0D6zdyccIv2gnXeI",
      "copyright": "Public domain",
      "license": "Public Domain Mark"
    },
    {
      "id": "GK2A903wttoFBI5pgeZV1",
      "bdrc": "WA0RT3206",
      "wiki": null,
      "type": "root",
      "contributions": [],
      "date": "2025-11-23",
      "title": {
        "bo": "དབུ་མ་ལ་འཇུག་པ།"
      },
      "alt_titles": null,
      "language": "bo",
      "target": null,
      "category_id": "kj8dljKGdBUuL4GkkVXbB",
      "copyright": "Public domain",
      "license": "Public Domain Mark"
    }
  ],
  "total": 100,
  "offset": 0,
  "limit": 20
}
```

**Response Schema:**

| Field    | Type    | Description                          |
|----------|---------|--------------------------------------|
| `texts`  | array   | Array of text objects                |
| `total`  | integer | Total number of texts available      |
| `offset` | integer | Number of records skipped            |
| `limit`  | integer | Maximum records returned per request |

**Text Object:**

| Field           | Type           | Description                                          |
|-----------------|----------------|------------------------------------------------------|
| `id`            | string         | Unique identifier for the text                       |
| `bdrc`          | string \| null | Buddhist Digital Resource Center identifier          |
| `wiki`          | string \| null | Wikipedia/Wikidata identifier                        |
| `type`          | string         | Type of text (e.g., `root`, `translation`)           |
| `contributions` | array          | List of contributor objects                          |
| `date`          | string \| null | Date of the text (YYYY-MM-DD format)                 |
| `title`         | object         | Title in different languages (e.g., `{"bo": "..."}`) |
| `alt_titles`    | array \| null  | Alternative titles                                   |
| `language`      | string         | Primary language of the text                         |
| `target`        | string \| null | Target text ID (for translations)                    |
| `category_id`   | string         | Category this text belongs to                        |
| `copyright`     | string         | Copyright status                                     |
| `license`       | string         | License type                                         |

**Contribution Object:**

| Field            | Type   | Description                                            |
|------------------|--------|--------------------------------------------------------|
| `person_id`      | string | Unique identifier for the person                       |
| `person_bdrc_id` | string | BDRC identifier for the person                         |
| `role`           | string | Role of the contributor (e.g., `author`, `translator`) |
| `person_name`    | object | Person's name in different languages                   |

**Response Codes:**

| Code  | Description                         |
|-------|-------------------------------------|
| `200` | Successful response with texts list |
| `400` | Bad request - invalid parameters    |
| `500` | Internal server error               |

---

### Get Related Texts by Work

Retrieves texts that are related to a specific text by the same work (e.g., translations, commentaries).

**Endpoint:** `GET /v2/texts/{text_id}/related-by-work`

**Path Parameters:**

| Parameter | Type   | Required  | Description                       |
|-----------|--------|-----------|-----------------------------------|
| `text_id` | string | Yes       | The unique identifier of the text |

**Query Parameters:**

| Parameter  | Type   | Required  | Description                                                 |
|------------|--------|-----------|-------------------------------------------------------------|
| `relation` | string | No        | Filter by relation type (e.g., `translation`, `commentary`) |

**Headers:**

| Header   | Value              |
|----------|--------------------|
| `Accept` | `application/json` |

**Example Request:**

```bash
curl -X 'GET' \
  'https://api-aq25662yyq-uc.a.run.app/v2/texts/rAEGbNlKaD8VxNO6qP4d2/related-by-work' \
  -H 'accept: application/json'
```

**Example Response:**

```json
{
  "a6kVAbs74KEWUzIoE6KKi": {
    "relation": "translation",
    "expression_ids": [
      "PqT7jXsnVDBWUJIUtPXw9",
      "NSukXByxqZ5NHWX6Hn7N5",
      "A1GtsbjzMNrviRmbMKZSp"
    ]
  },
  "kCPgJ1syyO9rem9QOi33O": {
    "relation": "commentary",
    "expression_ids": [
      "5gIFi6oktaLtjFBAY8kPS"
    ]
  },
  "XtViTJQFjTK1u0oCNd4UW": {
    "relation": "commentary",
    "expression_ids": [
      "1WXaEiw8IZIp8zJUwcHQj"
    ]
  }
}
```

**Response Schema:**

The response is an object where each key is a work ID, and the value contains relation information.

| Field       | Type   | Description                                      |
|-------------|--------|--------------------------------------------------|
| `{work_id}` | object | Key is the work ID, value is the relation object |

**Relation Object:**

| Field            | Type   | Description                                          |
|------------------|--------|------------------------------------------------------|
| `relation`       | string | Type of relation (e.g., `translation`, `commentary`) |
| `expression_ids` | array  | List of expression/text IDs related to this work     |

**Response Codes:**

| Code  | Description                            |
|-------|----------------------------------------|
| `200` | Successful response with related texts |
| `404` | Text not found                         |
| `500` | Internal server error                  |

---

## Instances

### Get Instance

Retrieves instance details including optional annotation and content data.

**Endpoint:** `GET /v2/instances/{instance_id}`

**Path Parameters:**

| Parameter     | Type   | Required  | Description                            |
|---------------|--------|-----------|----------------------------------------|
| `instance_id` | string | Yes       | The unique identifier of the instance  |

**Query Parameters:**

| Parameter    | Type    | Required  | Description                                              |
|--------------|---------|-----------|----------------------------------------------------------|
| `annotation` | boolean | No        | Include annotation data in response. Defaults to `false` |
| `content`    | boolean | No        | Include content data in response. Defaults to `false`    |

**Headers:**

| Header   | Value              |
|----------|--------------------|
| `Accept` | `application/json` |

**Example Request:**

```bash
curl -X 'GET' \
  'https://api-aq25662yyq-uc.a.run.app/v2/instances/XVqq55pnANEKri9536Wa4?annotation=true&content=true' \
  -H 'accept: application/json'
```

**Example Response:**

```json
{
  "metadata": {
    "id": "XVqq55pnANEKri9536Wa4",
    "type": "critical",
    "source": "openpecha.org",
    "bdrc": null,
    "wiki": null,
    "colophon": null,
    "incipit_title": null,
    "alt_incipit_titles": null
  },
  "content": "Content here",
  "annotations": [
    {
      "annotation_id": "ulMr4AUAYMLhr3s0ZddVB",
      "type": "segmentation"
    },
    {
      "annotation_id": "0II1SGf0Obzxxp1Gxx80f",
      "type": "bibliography"
    },
    {
      "annotation_id": "zyLeUVLOeZnQCH1IFBaWc",
      "type": "search_segmentation"
    }
  ]
}
```

**Response Schema:**

| Field         | Type  | Description                              |
|---------------|-------|------------------------------------------|
| `metadata`    | object| Instance metadata information            |
| `annotations` | array | Array of annotation references           |

**Metadata Object:**

| Field              | Type           | Description                                   |
|--------------------|----------------|-----------------------------------------------|
| `id`               | string         | Unique identifier for the instance            |
| `type`             | string         | Edition type (e.g., `critical`, `diplomatic`) |
| `source`           | string         | Source of the instance                        |
| `bdrc`             | string \| null | BDRC identifier                               |
| `wiki`             | string \| null | Wikipedia/Wikidata identifier                 |
| `colophon`         | string \| null | Colophon text                                 |
| `incipit_title`    | string \| null | Opening title of the text                     |
| `alt_incipit_titles` | array \| null | Alternative incipit titles                   |

**Annotation Reference Object:**

| Field           | Type   | Description                                          |
|-----------------|--------|------------------------------------------------------|
| `annotation_id` | string | Unique identifier for the annotation                 |
| `type`          | string | Type of annotation (e.g., `segmentation`, `bibliography`) |

**Response Codes:**

| Code  | Description                           |
|-------|---------------------------------------|
| `200` | Successful response with instance     |
| `404` | Instance not found                    |
| `500` | Internal server error                 |

---


## Annotations

### Get Annotation

Retrieves annotation details for a specific text or segment.

**Endpoint:** `GET /v2/annotations/{annotation_id}`

**Path Parameters:**

| Parameter       | Type   | Required  | Description                             |
|-----------------|--------|-----------|-----------------------------------------|
| `annotation_id` | string | Yes       | The unique identifier of the annotation |

**Query Parameters:**

| Parameter  | Type    | Required  | Description                                                       |
|------------|---------|-----------|-------------------------------------------------------------------|
| `offset`   | integer | No        | Number of segments to skip for pagination. Defaults to `0`        |
| `limit`    | integer | No        | Maximum number of segments to return. Defaults to `20`, max `100` |

**Headers:**

| Header   | Value              |
|----------|--------------------|
| `Accept` | `application/json` |

**Example Request:**

```bash
curl -X 'GET' \
  'https://api-aq25662yyq-uc.a.run.app/v2/annotations/pncablMmrIJBpo0aDi7a3?offset=0&limit=20' \
  -H 'accept: application/json'
```

**Example Response:**

```json
{
  "id": "pncablMmrIJBpo0aDi7a3",
  "type": "segmentation",
  "data": [
    {
      "id": "fHtnFBd02Qfw4xKmvMq0y",
      "span": {
        "start": 0,
        "end": 51
      }
    },
    {
      "id": "C5KNoy6WHiEoytrIfQ6ip",
      "span": {
        "start": 51,
        "end": 145
      }
    },
    {
      "id": "nKLmwCFlCzigPBHkEabgJ",
      "span": {
        "start": 145,
        "end": 196
      }
    }
  ],
  "total": 100,
  "offset": 0,
  "limit": 20
}
```

**Response Schema:**

| Field    | Type    | Description                                   |
|----------|---------|-----------------------------------------------|
| `id`     | string  | Unique identifier for the annotation          |
| `type`   | string  | Type of annotation (e.g., `segmentation`)     |
| `data`   | array   | Array of annotation segment objects (ordered by span) |
| `total`  | integer | Total number of segments available            |
| `offset` | integer | Number of segments skipped                    |
| `limit`  | integer | Maximum segments returned per request         |

**Annotation Segment Object:**

| Field   | Type    | Description                                                |
|---------|---------|------------------------------------------------------------|
| `id`    | string  | Unique identifier for the segment                          |
| `span`  | object  | Character span information (defines order by start position)|

**Span Object:**

| Field   | Type    | Description                          |
|---------|---------|--------------------------------------|
| `start` | integer | Start character position (0-indexed) |
| `end`   | integer | End character position               |

**Response Codes:**

| Code  | Description                                 |
|-------|---------------------------------------------|
| `200` | Successful response with annotation details |
| `404` | Annotation not found                        |
| `500` | Internal server error                       |

---

### Get Instance Content

Retrieves a portion of the instance content based on character span.

**Endpoint:** `GET /v2/instances/{instance_id}/content`

**Path Parameters:**

| Parameter     | Type   | Required | Description                       |
|---------------|--------|----------|-----------------------------------|
| `instance_id` | string | Yes      | The unique identifier of instance |

**Query Parameters:**

| Parameter | Type    | Required | Description                        |
|-----------|---------|----------|------------------------------------|
| `start`   | integer | No       | Start character position (0-based) |
| `end`     | integer | No       | End character position             |

**Headers:**

| Header   | Value              |
|----------|--------------------|
| `Accept` | `application/json` |

**Example Request:**

```bash
curl -X 'GET' \
  'https://api-aq25662yyq-uc.a.run.app/v2/instances/XVqq55pnANEKri9536Wa4/content?start=0&end=200' \
  -H 'accept: application/json'
```

**Example Response:**

```json
{
    "id": "XVqq55pnANEKri9536Wa4",
    "content": "Content here",
    "span": {
        "start": 0,
        "end": 200
    }
}
```

**Response Schema:**

| Field         | Type    | Description                    |
|---------------|---------|--------------------------------|
| `id`          | string  | Instance ID                    |
| `content`     | string  | Text content within the span   |
| `span`        | object  | Character span object          |
| `span.start`  | integer | Start character position       |
| `span.end`    | integer | End character position         |

**Response Codes:**

| Code  | Description                              |
|-------|------------------------------------------|
| `200` | Successful response with content         |
| `404` | Instance not found                       |
| `500` | Internal server error                    |

---

## Segments

### Get Related Segments

Retrieves segments that are related to a specific segment (e.g., parallel translations, aligned texts).

**Endpoint:** `GET /v2/segments/{segment_id}/related`

**Path Parameters:**

| Parameter    | Type   | Required  | Description                          |
|--------------|--------|-----------|--------------------------------------|
| `segment_id` | string | Yes       | The unique identifier of the segment |

**Headers:**

| Header   | Value              |
|----------|--------------------|
| `Accept` | `application/json` |

**Example Request:**

```bash
curl -X 'GET' \
  'https://api-aq25662yyq-uc.a.run.app/v2/segments/fHtnFBd02Qfw4xKmvMq0y/related' \
  -H 'accept: application/json'
```

**Example Response:**

```json
{
  "targets": [
    {
      "instance": {
        "id": "M12345678",
        "type": "critical",
        "source": "S12345678"
      },
      "text": {
        "id": "E12345678",
        "type": "translation",
        "title": {
          "en": "Translation of the Text"
        },
        "language": "en"
      },
      "segments": [
        {
          "id": "SEG001",
          "span": {
            "start": 0,
            "end": 100
          }
        },
        {
          "id": "SEG002",
          "span": {
            "start": 100,
            "end": 200
          }
        }
      ]
    }
  ],
  "sources": []
}
```

**Response Schema:**

| Field     | Type  | Description                             |
|-----------|-------|-----------------------------------------|
| `targets` | array | Array of target related segment objects |
| `sources` | array | Array of source related segment objects |

**Target/Source Object:**

| Field      | Type   | Description                         |
|------------|--------|-------------------------------------|
| `instance` | object | Instance metadata                   |
| `text`     | object | Text metadata                       |
| `segments` | array  | Array of segment objects with spans |

**Instance Object:**

| Field    | Type   | Description                        |
|----------|--------|------------------------------------|
| `id`     | string | Unique identifier for the instance |
| `type`   | string | Edition type (e.g., `critical`)    |
| `source` | string | Source identifier                  |

**Text Object (in Related Segments):**

| Field      | Type   | Description                        |
|------------|--------|------------------------------------|
| `id`       | string | Unique identifier for the text     |
| `type`     | string | Type of text (e.g., `translation`) |
| `title`    | object | Title in different languages       |
| `language` | string | Language of the text               |

**Segment Object:**

| Field   | Type   | Description                                     |
|---------|--------|-------------------------------------------------|
| `id`    | string | Unique identifier for the segment               |
| `span`  | object | Character span with `start` and `end` positions |

**Response Codes:**

| Code  | Description                               |
|-------|-------------------------------------------|
| `200` | Successful response with related segments |
| `404` | Segment not found                         |
| `500` | Internal server error                     |

---
