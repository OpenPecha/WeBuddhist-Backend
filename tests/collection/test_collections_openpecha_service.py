import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pecha_api.collections.collections_openpecha_service import (
    get_collections_from_openpecha,
    _extract_title,
    _extract_description,
    _category_to_collection_model,
    X_APPLICATION
)
from pecha_api.collections.collections_response_models import CollectionModel, CollectionsResponse, Pagination


class MockCategoryOutputTitle:
    def to_dict(self):
        return {"en": "Test Title", "bo": "བོད་ཡིག", "zh": "中文"}


class MockCategoryOutputDescription:
    def to_dict(self):
        return {"en": "Test Description", "bo": "བོད་ཡིག་འགྲེལ་བཤད", "zh": "中文描述"}


class MockCategoryOutput:
    def __init__(self, id="cat-123", children=None, parent_id=None, has_description=True):
        self.id = id
        self.title = MockCategoryOutputTitle()
        self.children = children or []
        self.parent_id = parent_id
        self.description = MockCategoryOutputDescription() if has_description else None


class TestExtractTitle:
    def test_extract_title_english(self):
        category = MockCategoryOutput()
        result = _extract_title(category, "en")
        assert result == "Test Title"

    def test_extract_title_tibetan(self):
        category = MockCategoryOutput()
        result = _extract_title(category, "bo")
        assert result == "བོད་ཡིག"

    def test_extract_title_fallback_to_english(self):
        category = MockCategoryOutput()
        result = _extract_title(category, "fr")
        assert result == "Test Title"


class TestExtractDescription:
    def test_extract_description_english(self):
        category = MockCategoryOutput()
        result = _extract_description(category, "en")
        assert result == "Test Description"

    def test_extract_description_tibetan(self):
        category = MockCategoryOutput()
        result = _extract_description(category, "bo")
        assert result == "བོད་ཡིག་འགྲེལ་བཤད"

    def test_extract_description_none(self):
        category = MockCategoryOutput(has_description=False)
        result = _extract_description(category, "en")
        assert result == ""


class TestCategoryToCollectionModel:
    def test_basic_conversion(self):
        category = MockCategoryOutput(id="cat-456", children=["child-1", "child-2"])
        result = _category_to_collection_model(category, "en")
        
        assert isinstance(result, CollectionModel)
        assert result.id == "cat-456"
        assert result.pecha_collection_id == "cat-456"
        assert result.title == "Test Title"
        assert result.description == "Test Description"
        assert result.has_child is True
        assert result.language == "en"
        assert result.slug == "Test Title"

    def test_no_children(self):
        category = MockCategoryOutput(id="cat-789", children=[])
        result = _category_to_collection_model(category, "en")
        
        assert result.has_child is False

    def test_slug_fallback_to_id(self):
        category = MockCategoryOutput(id="cat-empty")
        category.title = MagicMock()
        category.title.to_dict.return_value = {}
        result = _category_to_collection_model(category, "en")
        
        assert result.slug == "cat-empty"


class TestGetCollectionsFromOpenpecha:
    @pytest.mark.asyncio
    @patch('pecha_api.collections.collections_openpecha_service.get_v2_categories')
    @patch('pecha_api.collections.collections_openpecha_service.get_open_pecha_client')
    async def test_get_collections_success(self, mock_get_client, mock_get_categories):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_categories = [
            MockCategoryOutput(id="cat-1", children=["child-1"]),
            MockCategoryOutput(id="cat-2", children=[]),
        ]
        mock_get_categories.asyncio = AsyncMock(return_value=mock_categories)
        
        result = await get_collections_from_openpecha(
            language="en",
            parent_id=None,
            skip=0,
            limit=10
        )
        
        assert isinstance(result, CollectionsResponse)
        assert len(result.collections) == 2
        assert result.pagination.total == 2
        assert result.pagination.skip == 0
        assert result.pagination.limit == 10
        assert result.parent is None

    @pytest.mark.asyncio
    @patch('pecha_api.collections.collections_openpecha_service.get_v2_categories')
    @patch('pecha_api.collections.collections_openpecha_service.get_open_pecha_client')
    async def test_get_collections_with_pagination(self, mock_get_client, mock_get_categories):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_categories = [
            MockCategoryOutput(id=f"cat-{i}") for i in range(5)
        ]
        mock_get_categories.asyncio = AsyncMock(return_value=mock_categories)
        
        result = await get_collections_from_openpecha(
            language="en",
            parent_id=None,
            skip=1,
            limit=2
        )
        
        assert result.pagination.total == 5
        assert len(result.collections) == 2
        assert result.collections[0].id == "cat-1"
        assert result.collections[1].id == "cat-2"

    @pytest.mark.asyncio
    @patch('pecha_api.collections.collections_openpecha_service.get_v2_categories')
    @patch('pecha_api.collections.collections_openpecha_service.get_open_pecha_client')
    async def test_get_collections_empty_response(self, mock_get_client, mock_get_categories):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_get_categories.asyncio = AsyncMock(return_value=None)
        
        result = await get_collections_from_openpecha(
            language="en",
            parent_id=None,
            skip=0,
            limit=10
        )
        
        assert len(result.collections) == 0
        assert result.pagination.total == 0

    @pytest.mark.asyncio
    @patch('pecha_api.collections.collections_openpecha_service.get_v2_categories')
    @patch('pecha_api.collections.collections_openpecha_service.get_open_pecha_client')
    async def test_get_collections_with_parent_id(self, mock_get_client, mock_get_categories):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        parent_category = MockCategoryOutput(id="parent-1")
        child_categories = [MockCategoryOutput(id="child-1")]
        
        async def mock_asyncio(*args, **kwargs):
            if kwargs.get('parent_id') == "parent-1":
                return child_categories
            return [parent_category]
        
        mock_get_categories.asyncio = mock_asyncio
        
        result = await get_collections_from_openpecha(
            language="en",
            parent_id="parent-1",
            skip=0,
            limit=10
        )
        
        assert len(result.collections) == 1
        assert result.collections[0].id == "child-1"
        assert result.parent is not None
        assert result.parent.id == "parent-1"

    @pytest.mark.asyncio
    @patch('pecha_api.collections.collections_openpecha_service.get_open_pecha_client')
    @patch('pecha_api.collections.collections_openpecha_service.get')
    async def test_default_language(self, mock_config_get, mock_get_client):
        mock_config_get.return_value = "bo"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        with patch('pecha_api.collections.collections_openpecha_service.get_v2_categories') as mock_categories:
            mock_categories.asyncio = AsyncMock(return_value=[])
            
            result = await get_collections_from_openpecha(
                language=None,
                parent_id=None,
                skip=0,
                limit=10
            )
            
            assert result.pagination.total == 0


class TestXApplicationHeader:
    def test_x_application_value(self):
        assert X_APPLICATION == "webuddhist"
