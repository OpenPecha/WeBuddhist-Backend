import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pecha_api.search.search_client import search_client, close_search_client
from pecha_api.config import get

@pytest.mark.asyncio
async def test_search_client_success():
    mock_es = MagicMock()
    mock_es_class = MagicMock(return_value=mock_es)
    with patch('elasticsearch.AsyncElasticsearch', mock_es_class):
        with patch('pecha_api.search.search_client.get', side_effect=lambda key: {
            'ELASTICSEARCH_URL': 'test_elasticsearch_url',
            'ELASTICSEARCH_API': 'test_api_key'
        }[key]):
            import pecha_api.search.search_client as search_client_module
            search_client_module._search_client = None
            client = search_client()
            assert client == mock_es
            mock_es_class.assert_called_once_with(
                hosts=['test_elasticsearch_url'],
                api_key='test_api_key'
            )

@pytest.mark.asyncio
async def test_search_client_close_success():
    mock_es = MagicMock()
    mock_es.close = AsyncMock()
    # Patch the global _search_client directly in the module
    with patch('pecha_api.search.search_client._search_client', mock_es):
        with patch('pecha_api.search.search_client.get', side_effect=lambda key: {
            'ELASTICSEARCH_URL': 'test_elasticsearch_url',
            'ELASTICSEARCH_API': 'test_api_key'
        }[key]):
            await close_search_client()
            mock_es.close.assert_awaited_once()
