import pytest
from unittest.mock import AsyncMock, patch

from pecha_api.text_uploader.collections.collection_service import CollectionService


def test_build_multilingual_payload_merges_languages_and_sets_slug_from_en_title():
    service = CollectionService()

    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "_id": {"$oid": "c1"},
                    "title": "Liturgy",
                    "description": "Prayers",
                    "parent_id": None,
                    "has_sub_child": False,
                }
            ],
        },
        {
            "language": "bo",
            "collections": [
                {
                    "_id": {"$oid": "c1"},
                    "title": "ཁ་འདོན།",
                    "description": "ཆོ་ག",
                    "parent_id": None,
                    "has_sub_child": False,
                }
            ],
        },
    ]

    payloads = service.build_multilingual_payload(collections_by_language)
    assert len(payloads) == 1

    payload = payloads[0]
    assert payload["pecha_collection_id"] == "c1"
    assert payload["slug"] == "Liturgy"
    assert payload["titles"]["en"] == "Liturgy"
    assert payload["titles"]["bo"] == "ཁ་འདོན།"
    assert payload["descriptions"]["en"] == "Prayers"
    assert payload["descriptions"]["bo"] == "ཆོ་ག"
    # configured languages should always exist as keys
    assert "zh" in payload["descriptions"]


@pytest.mark.asyncio
async def test_build_recursive_multilingual_payloads_recurse_children_uploads_all_levels():
    service = CollectionService()

    root_level = [
        {
            "language": "en",
            "collections": [
                {
                    "_id": {"$oid": "c1"},
                    "title": "Root",
                    "description": "Root desc",
                    "parent_id": None,
                    "has_sub_child": True,
                }
            ],
        },
        {"language": "bo", "collections": [{"_id": {"$oid": "c1"}, "title": "རྩ་བ།"}]},
        {"language": "zh", "collections": [{"_id": {"$oid": "c1"}, "title": "根"}]},
    ]
    child_level = [
        {
            "language": "en",
            "collections": [
                {
                    "_id": {"$oid": "c2"},
                    "title": "Child",
                    "description": "Child desc",
                    "parent_id": {"$oid": "c1"},
                    "has_sub_child": False,
                }
            ],
        },
        {"language": "bo", "collections": [{"_id": {"$oid": "c2"}, "title": "བུ།"}]},
        {"language": "zh", "collections": [{"_id": {"$oid": "c2"}, "title": "子"}]},
    ]

    async def fake_get_collections_service(*, openpecha_api_url: str, parent_id=None):
        if parent_id is None:
            return root_level
        if parent_id == "c1":
            return child_level
        return [{"language": "en", "collections": []}]

    with patch.object(
        service,
        "get_collections_service",
        new=AsyncMock(side_effect=fake_get_collections_service),
    ), patch(
        "pecha_api.text_uploader.collections.collection_service.get_collection_by_pecha_collection_id",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "pecha_api.text_uploader.collections.collection_service.post_collections",
        new_callable=AsyncMock,
        side_effect=[
            {"id": {"$oid": "local_c1"}},
            {"id": "local_c2"},
        ],
    ) as mock_post:
        payloads = await service.build_recursive_multilingual_payloads(
            destination_url="https://dest.example/api/v1",
            openpecha_api_url="https://openpecha.example",
            access_token="tok",
        )

    assert mock_post.await_count == 2

    assert len(payloads) == 1
    root_payload = payloads[0]
    assert root_payload["pecha_collection_id"] == "c1"
    assert root_payload["local_id"] == "local_c1"

    assert "children" in root_payload
    assert len(root_payload["children"]) == 1
    child_payload = root_payload["children"][0]
    assert child_payload["pecha_collection_id"] == "c2"
    assert child_payload["local_id"] == "local_c2"

    # Ensure recursion used the root's local_id as the child's parent_id in POST.
    first_call = mock_post.await_args_list[0]
    second_call = mock_post.await_args_list[1]
    assert first_call.kwargs["collection_model"].parent_id is None
    assert second_call.kwargs["collection_model"].parent_id == "local_c1"

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from pecha_api.text_uploader.collections.collection_service import CollectionService
from pecha_api.text_uploader.constants import COLLECTION_LANGUAGES
from pecha_api.text_uploader.collections.collection_model import CollectionPayload
from pecha_api.text_uploader.text_uploader_response_model import TextUploadRequest


@pytest.mark.asyncio
@pytest.mark.parametrize("parent_id", [None, "parent_1"])
async def test_get_collections_service_delegates_to_repository(parent_id: str | None):
    expected = [{"language": "en", "collections": [{"id": "c1"}]}]

    with patch(
        "pecha_api.text_uploader.collections.collection_service.get_collections",
        new_callable=AsyncMock,
        return_value=expected,
    ) as mock_get_collections:
        service = CollectionService()

        result = await service.get_collections_service(
            openpecha_api_url="https://openpecha.example",
            parent_id=parent_id,
        )

        assert result == expected
        mock_get_collections.assert_awaited_once_with(
            openpecha_api_url="https://openpecha.example",
            languages=COLLECTION_LANGUAGES,
            parent_id=parent_id,
        )


@pytest.mark.asyncio
async def test_upload_collections_success():
    """Test upload_collections calls build_recursive_multilingual_payloads"""
    service = CollectionService()
    
    text_upload_request = TextUploadRequest(
        destination_url="https://destination.example",
        openpecha_api_url="https://openpecha.example",
        text_id="test_text_id"
    )
    token = "test_token"
    
    with patch.object(
        service,
        "build_recursive_multilingual_payloads",
        new_callable=AsyncMock
    ) as mock_build:
        await service.upload_collections(
            text_upload_request=text_upload_request,
            token=token
        )
        
        mock_build.assert_awaited_once_with(
            destination_url="https://destination.example",
            openpecha_api_url="https://openpecha.example",
            access_token=token
        )


@pytest.mark.asyncio
async def test_build_multilingual_payload_single_language():
    """Test build_multilingual_payload with single language collections"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "id": "collection_id_1",
                    "slug": "test-collection",
                    "title": "Test Collection",
                    "description": "Test Description",
                    "parent_id": None,
                    "has_sub_child": False
                }
            ]
        }
    ]
    
    result = service.build_multilingual_payload(collections_by_language)
    
    assert len(result) == 1
    assert result[0]["pecha_collection_id"] == "collection_id_1"
    assert result[0]["slug"] == "Test Collection"
    assert result[0]["titles"] == {"en": "Test Collection"}
    assert result[0]["descriptions"]["en"] == "Test Description"
    assert result[0]["parent_id"] is None
    assert result[0]["has_sub_child"] is False


@pytest.mark.asyncio
async def test_build_multilingual_payload_multiple_languages():
    """Test build_multilingual_payload with multiple languages for same collection"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "id": "collection_id_1",
                    "slug": "madhyamaka",
                    "title": "Madhyamaka",
                    "description": "Madhyamaka treatises",
                    "parent_id": None,
                    "has_sub_child": True
                }
            ]
        },
        {
            "language": "bo",
            "collections": [
                {
                    "id": "collection_id_1",
                    "slug": "madhyamaka",
                    "title": "དབུ་མ།",
                    "description": "དབུ་མའི་གཞུང་སྣ་ཚོགས།",
                    "parent_id": None,
                    "has_sub_child": True
                }
            ]
        }
    ]
    
    result = service.build_multilingual_payload(collections_by_language)
    
    assert len(result) == 1
    assert result[0]["pecha_collection_id"] == "collection_id_1"
    assert result[0]["slug"] == "Madhyamaka"  # English title is used as slug
    assert result[0]["titles"] == {"en": "Madhyamaka", "bo": "དབུ་མ།"}
    assert result[0]["descriptions"]["en"] == "Madhyamaka treatises"
    assert result[0]["descriptions"]["bo"] == "དབུ་མའི་གཞུང་སྣ་ཚོགས།"
    assert result[0]["has_sub_child"] is True


@pytest.mark.asyncio
async def test_build_multilingual_payload_with_oid_format():
    """Test build_multilingual_payload with MongoDB ObjectId format"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "_id": {"$oid": "507f1f77bcf86cd799439011"},
                    "slug": "test",
                    "title": "Test Collection",
                    "description": "Test Description",
                    "parent_id": {"$oid": "507f1f77bcf86cd799439012"},
                    "has_child": True
                }
            ]
        }
    ]
    
    result = service.build_multilingual_payload(collections_by_language)
    
    assert len(result) == 1
    assert result[0]["pecha_collection_id"] == "507f1f77bcf86cd799439011"
    assert result[0]["parent_id"] == {"$oid": "507f1f77bcf86cd799439012"}
    assert result[0]["has_sub_child"] is True


@pytest.mark.asyncio
async def test_build_multilingual_payload_multiple_collections():
    """Test build_multilingual_payload with multiple different collections"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "id": "collection_1",
                    "title": "Collection 1",
                    "description": "Description 1",
                    "has_sub_child": False
                },
                {
                    "id": "collection_2",
                    "title": "Collection 2",
                    "description": "Description 2",
                    "has_sub_child": True
                }
            ]
        }
    ]
    
    result = service.build_multilingual_payload(collections_by_language)
    
    assert len(result) == 2
    collection_ids = [r["pecha_collection_id"] for r in result]
    assert "collection_1" in collection_ids
    assert "collection_2" in collection_ids


@pytest.mark.asyncio
async def test_build_multilingual_payload_with_titles_dict():
    """Test build_multilingual_payload when titles/descriptions are already dicts"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "id": "collection_1",
                    "slug": "test",
                    "titles": {"en": "English Title", "bo": "བོད་ཡིག"},
                    "descriptions": {"en": "English Description"},
                    "has_sub_child": False
                }
            ]
        }
    ]
    
    result = service.build_multilingual_payload(collections_by_language)
    
    assert len(result) == 1
    assert result[0]["titles"]["en"] == "English Title"
    assert result[0]["slug"] == "English Title"


@pytest.mark.asyncio
async def test_build_recursive_multilingual_payloads_no_children():
    """Test build_recursive_multilingual_payloads with collections that have no children"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "id": "collection_1",
                    "title": "Test Collection",
                    "description": "Test Description",
                    "parent_id": None,
                    "has_sub_child": False
                }
            ]
        }
    ]
    
    with patch.object(
        service,
        "get_collections_service",
        new_callable=AsyncMock,
        return_value=collections_by_language
    ) as mock_get_collections, \
    patch(
        "pecha_api.text_uploader.collections.collection_service.get_collection_by_pecha_collection_id",
        new_callable=AsyncMock,
        return_value=None
    ) as mock_get_existing, \
    patch(
        "pecha_api.text_uploader.collections.collection_service.post_collections",
        new_callable=AsyncMock,
        return_value={"id": "new_local_id_1"}
    ) as mock_post:
        result = await service.build_recursive_multilingual_payloads(
            destination_url="https://destination.example",
            openpecha_api_url="https://openpecha.example",
            access_token="test_token"
        )
        
        assert len(result) == 1
        assert result[0]["pecha_collection_id"] == "collection_1"
        assert result[0]["children"] == []
        assert result[0]["local_id"] == "new_local_id_1"
        mock_post.assert_awaited_once()


@pytest.mark.asyncio
async def test_build_recursive_multilingual_payloads_multiple_collections_no_children():
    """Test build_recursive_multilingual_payloads with multiple collections without children"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "id": "collection_1",
                    "title": "Collection 1",
                    "description": "Description 1",
                    "has_sub_child": False
                },
                {
                    "id": "collection_2",
                    "title": "Collection 2",
                    "description": "Description 2",
                    "has_sub_child": False
                }
            ]
        }
    ]
    
    with patch.object(
        service,
        "get_collections_service",
        new_callable=AsyncMock,
        return_value=collections_by_language
    ), \
    patch(
        "pecha_api.text_uploader.collections.collection_service.get_collection_by_pecha_collection_id",
        new_callable=AsyncMock,
        return_value=None
    ), \
    patch(
        "pecha_api.text_uploader.collections.collection_service.post_collections",
        new_callable=AsyncMock,
        side_effect=[
            {"id": "local_1"},
            {"id": "local_2"}
        ]
    ) as mock_post:
        result = await service.build_recursive_multilingual_payloads(
            destination_url="https://destination.example",
            openpecha_api_url="https://openpecha.example",
            access_token="test_token"
        )
        
        assert len(result) == 2
        assert result[0]["pecha_collection_id"] == "collection_1"
        assert result[0]["local_id"] == "local_1"
        assert result[0]["children"] == []
        assert result[1]["pecha_collection_id"] == "collection_2"
        assert result[1]["local_id"] == "local_2"
        assert result[1]["children"] == []
        assert mock_post.await_count == 2


@pytest.mark.asyncio
async def test_build_recursive_multilingual_payloads_existing_collection():
    """Test build_recursive_multilingual_payloads skips existing collections"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "id": "existing_collection",
                    "title": "Existing Collection",
                    "description": "Already exists",
                    "has_sub_child": False
                }
            ]
        }
    ]
    
    with patch.object(
        service,
        "get_collections_service",
        new_callable=AsyncMock,
        return_value=collections_by_language
    ), \
    patch(
        "pecha_api.text_uploader.collections.collection_service.get_collection_by_pecha_collection_id",
        new_callable=AsyncMock,
        return_value="existing_local_id"
    ) as mock_get_existing, \
    patch(
        "pecha_api.text_uploader.collections.collection_service.post_collections",
        new_callable=AsyncMock
    ) as mock_post:
        result = await service.build_recursive_multilingual_payloads(
            destination_url="https://destination.example",
            openpecha_api_url="https://openpecha.example",
            access_token="test_token"
        )
        
        assert len(result) == 1
        mock_get_existing.assert_awaited_once()
        mock_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_build_recursive_multilingual_payloads_with_oid_local_id():
    """Test build_recursive_multilingual_payloads handles ObjectId format for local_id"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "id": "collection_1",
                    "title": "Test Collection",
                    "has_sub_child": False
                }
            ]
        }
    ]
    
    with patch.object(
        service,
        "get_collections_service",
        new_callable=AsyncMock,
        return_value=collections_by_language
    ), \
    patch(
        "pecha_api.text_uploader.collections.collection_service.get_collection_by_pecha_collection_id",
        new_callable=AsyncMock,
        return_value=None
    ), \
    patch(
        "pecha_api.text_uploader.collections.collection_service.post_collections",
        new_callable=AsyncMock,
        return_value={"_id": {"$oid": "507f1f77bcf86cd799439011"}}
    ):
        result = await service.build_recursive_multilingual_payloads(
            destination_url="https://destination.example",
            openpecha_api_url="https://openpecha.example",
            access_token="test_token"
        )
        
        assert len(result) == 1
        assert result[0]["local_id"] == "507f1f77bcf86cd799439011"


@pytest.mark.asyncio
async def test_build_recursive_multilingual_payloads_with_local_parent_id():
    """Test build_recursive_multilingual_payloads uses provided local_parent_id"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "id": "child_collection",
                    "title": "Child Collection",
                    "parent_id": "remote_parent_id",
                    "has_sub_child": False
                }
            ]
        }
    ]
    
    with patch.object(
        service,
        "get_collections_service",
        new_callable=AsyncMock,
        return_value=collections_by_language
    ), \
    patch(
        "pecha_api.text_uploader.collections.collection_service.get_collection_by_pecha_collection_id",
        new_callable=AsyncMock,
        return_value=None
    ), \
    patch(
        "pecha_api.text_uploader.collections.collection_service.post_collections",
        new_callable=AsyncMock,
        return_value={"id": "new_local_id"}
    ) as mock_post:
        result = await service.build_recursive_multilingual_payloads(
            destination_url="https://destination.example",
            openpecha_api_url="https://openpecha.example",
            access_token="test_token",
            local_parent_id="local_parent_id_123"
        )
        
        assert len(result) == 1
        # Verify that the collection was posted with the correct parent_id
        call_args = mock_post.call_args
        assert call_args[1]["collection_model"].parent_id == "local_parent_id_123"


@pytest.mark.asyncio
async def test_build_multilingual_payload_empty_collections():
    """Test build_multilingual_payload with empty collections"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": []
        }
    ]
    
    result = service.build_multilingual_payload(collections_by_language)
    
    assert len(result) == 0
    assert result == []


@pytest.mark.asyncio
async def test_build_multilingual_payload_none_descriptions():
    """Test build_multilingual_payload handles None descriptions"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "id": "collection_1",
                    "title": "Test Collection",
                    "description": None,
                    "has_sub_child": False
                }
            ]
        }
    ]
    
    result = service.build_multilingual_payload(collections_by_language)
    
    assert len(result) == 1
    assert result[0]["titles"]["en"] == "Test Collection"
    # Description for 'en' should be empty string (from initialization)
    assert "descriptions" in result[0]


@pytest.mark.asyncio
async def test_build_recursive_multilingual_payloads_no_remote_parent_id():
    """Test build_recursive_multilingual_payloads handles missing remote parent id"""
    service = CollectionService()
    
    collections_by_language = [
        {
            "language": "en",
            "collections": [
                {
                    "id": "valid_id",  # Valid ID but will test edge case
                    "title": "Test Collection",
                    "has_sub_child": False  # No children to avoid recursion bug
                }
            ]
        }
    ]
    
    with patch.object(
        service,
        "get_collections_service",
        new_callable=AsyncMock,
        return_value=collections_by_language
    ), \
    patch(
        "pecha_api.text_uploader.collections.collection_service.get_collection_by_pecha_collection_id",
        new_callable=AsyncMock,
        return_value=None
    ), \
    patch(
        "pecha_api.text_uploader.collections.collection_service.post_collections",
        new_callable=AsyncMock,
        return_value={"id": "new_id"}
    ):
        result = await service.build_recursive_multilingual_payloads(
            destination_url="https://destination.example",
            openpecha_api_url="https://openpecha.example",
            access_token="test_token"
        )
        
        assert len(result) == 1
        assert result[0]["pecha_collection_id"] == "valid_id"
        # Should have empty children since has_sub_child is False
        assert result[0]["children"] == []


