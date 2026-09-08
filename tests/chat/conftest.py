from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def published_group_by_default():
    """Chat suites mock rooms and members, not groups, so the group-publication
    gate has no real row to read. Default it to published; tests that cover the
    hidden-group behaviour patch it themselves and win, since an inner patch
    applied inside the test body overrides this fixture."""
    with patch(
        "pecha_api.chat.service.is_group_id_published", return_value=True
    ), patch(
        "pecha_api.chat.message_service.is_group_id_published", return_value=True
    ):
        yield
