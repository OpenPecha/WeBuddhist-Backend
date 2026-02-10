## Local Setup

### Prerequisites

- Python 3.12
- Poetry
- Docker (for local services)

### Environment Variables

Defaults are defined in `pecha_api/config.py`, but for local development
you typically override these values:

- `DATABASE_URL`
- `MONGO_CONNECTION_STRING`
- `CACHE_CONNECTION_STRING`
- `ELASTICSEARCH_URL`
- `ELASTICSEARCH_API` (optional for local)

Optional integrations:

- `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `AWS_BUCKET_NAME`
- `DOMAIN_NAME`, `CLIENT_ID` (Auth0)
- `MAILTRAP_API_KEY`, `SENDER_EMAIL`, `SENDER_NAME`

### Install Dependencies

```sh
poetry install
```

### Database and Search

Start local services (Postgres, MongoDB, Redis/Dragonfly, Elasticsearch):

```sh
cd local_setup
docker-compose up -d
```

If you see file permission errors for local data directories:

```sh
./dev/fix_permissions.sh
```

Apply migrations:

```sh
poetry run alembic upgrade head
```

### Run the API

Recommended:

```sh
./dev/start_dev.sh
```

Or run directly:

```sh
poetry run uvicorn pecha_api.app:api --reload
```

### Tests

```sh
poetry run pytest
```

Coverage:

```sh
poetry run pytest --cov=pecha_api
poetry run coverage html
```
