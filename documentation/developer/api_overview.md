
Current specs live in `documentation/`:
- `pecha-auth-api.yaml`
- `pecha-core-api.yaml`
- `cms-openapi.yaml`
- `openapi.yaml`

The API root path is `/api/v1` (see `pecha_api/app.py`).

### Module to Router Map

Routers are included in `pecha_api/app.py`:
- Auth: `pecha_api/auth/auth_views.py`
- Core: texts, groups, segments, mappings, topics, users, collections, terms, sheets
- Search: `pecha_api/search/search_views.py`
- Plans: public, users, CMS, items, tasks, featured
- Share: `pecha_api/share/share_views.py`
- Uploading: text uploader, cataloger, metadata
- Recitations: recitations APIs

### Utility Endpoints

- `GET /health`
- `GET /props`

### Response Models

Response models are defined per module and exposed via `response_model` in
routes. Common locations:

- Texts: `pecha_api/texts/texts_response_models.py`
- Users: `pecha_api/users/user_response_models.py`
- Plans media uploads: `pecha_api/plans/media/media_response_models.py`

Standard message strings live in `pecha_api/plans/response_message.py`.
