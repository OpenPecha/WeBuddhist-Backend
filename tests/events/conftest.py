"""
Pytest configuration for events tests.

Ensures all SQLAlchemy models are imported before tests run to avoid
mapper configuration errors from circular relationships.
"""
import pytest


@pytest.fixture(scope="session", autouse=True)
def _ensure_models_loaded():
    """Import all models to ensure SQLAlchemy mappers are configured."""
    # Import models that have circular relationships
    from pecha_api.plans.tasks.plan_tasks_models import PlanTask  # noqa: F401
    from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask  # noqa: F401
    from pecha_api.plans.users.plan_users_models import (  # noqa: F401
        UserTaskCompletion,
        UserSubTaskCompletion,
    )
