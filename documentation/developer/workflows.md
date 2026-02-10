## Workflows

### Add a New Endpoint

1. Define request and response models
2. Implement route in `*_views.py`
3. Add business logic in `*_services.py`
4. Add tests
5. Update OpenAPI spec and developer docs

### Local Development Loop

1. Start services:
   ```sh
   cd local_setup
   docker-compose up -d
   ```
2. Run the API:
   ```sh
   ./dev/start_dev.sh
   ```

### Add a New Feature Module

1. Create module folder
2. Add `*_views.py`, `*_services.py`, `*_models.py`
3. Register router in app startup
4. Add docs under `documentation/`

### Database Migrations

Create:

```sh
poetry run alembic revision --autogenerate -m "add feature"
```

Apply:

```sh
poetry run alembic upgrade head
```

### Release Checklist

- Run tests
- Run linters
- Update version and changelog
- Deploy
