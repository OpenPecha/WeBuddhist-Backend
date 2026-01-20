from typing import Any
from pecha_api.text_uploader.collections.collections_repository import get_collections, post_collections
from pecha_api.text_uploader.constants import COLLECTION_LANGUAGES
from pecha_api.text_uploader.collections.collection_model import CollectionPayload
from pecha_api.text_uploader.text_uploader_response_model import TextUploadRequest

from pecha_api.text_uploader.collections.collections_repository import get_collection_by_pecha_collection_id

import logging

class CollectionService:

    async def upload_collections(self, text_upload_request: TextUploadRequest, token: str):

        await self.build_recursive_multilingual_payloads(
            destination_url=text_upload_request.destination_url, 
            openpecha_api_url=text_upload_request.openpecha_api_url,
            access_token=token
        )


    async def get_collections_service(self, openpecha_api_url: str, parent_id: str | None = None):
        return await get_collections(
            openpecha_api_url=openpecha_api_url,
            languages=COLLECTION_LANGUAGES,
            parent_id=parent_id
        )

    async def build_recursive_multilingual_payloads(
        self,
        destination_url: str,
        openpecha_api_url: str,
        access_token: str,
        remote_parent_id: str | None = None,
        local_parent_id: str | None = None
    ) -> list[dict[str, Any]]:

        # Fetch collections for this level from the remote (OpenPecha) API.
        # This `remote_parent_id` is **only** for traversing the source tree.
        collections_by_language = await self.get_collections_service(
            openpecha_api_url=openpecha_api_url,
            parent_id=remote_parent_id
        )

        # Build the multilingual payload for the current level. This returns one
        # combined payload per `pecha_collection_id`, where `titles` and
        # `descriptions` contain entries for all languages.
        multilingual_payloads = self.build_multilingual_payload(
            collections_by_language
        )

        # First, upload collections at this level to the destination (webuddhist)
        # backend, capturing the *destination* IDs so they can be used as
        # `parent_id` for the next level.
        for payload in multilingual_payloads:
            # Determine parent_id: if local_parent_id is provided, use it.
            # Otherwise, look up the parent in the CSV using the parent's pecha_collection_id
            parent_id_to_use = local_parent_id
            
            # If we don't have a local_parent_id but this collection has a parent,
            # try to find the parent's destination ID from the CSV log
            if parent_id_to_use is None:
                parent_pecha_id = payload.get("parent_id")
                if parent_pecha_id:
                    # Normalize parent pecha_collection_id if it's in dict format
                    if isinstance(parent_pecha_id, dict) and "$oid" in parent_pecha_id:
                        parent_pecha_id = str(parent_pecha_id["$oid"])
                    elif parent_pecha_id is not None:
                        parent_pecha_id = str(parent_pecha_id)
                    
                    # Look up parent's destination ID from CSV
                    # if parent_pecha_id:
                    #     parent_id_to_use = get_parent_id_by_pecha_collection_id(parent_pecha_id)
            # if payload.get("slug") is None:
                # continue
            collection_model = CollectionPayload(
                pecha_collection_id=payload.get("pecha_collection_id"),
                slug=payload.get("slug"),
                titles=payload.get("titles"),
                descriptions=payload.get("descriptions"),
                # Use the resolved parent_id (from parameter or CSV lookup)
                parent_id=parent_id_to_use,
            )

            
            existing_collection_id = await get_collection_by_pecha_collection_id(pecha_collection_id=payload.get("pecha_collection_id"), destination_url=destination_url)
            # Upload to webuddhist backend. We send the full multilingual
            # payload body, and use "en" as the request language context.
            response_data = {}
            if not existing_collection_id:
                response_data = await post_collections(destination_url=destination_url, language="en", collection_model=collection_model, access_token=access_token)
                logging.info(f" '{payload.get('slug')!r}' uploaded successfully")
            else:
                logging.warning(f" '{payload.get('slug')!r}' ALREADY EXIST, skipping")

            # Extract the newly created destination collection ID so it can be
            # used as the parent for this node's children.

            raw_local_id = (
                response_data.get("id")
                or response_data.get("_id")
                or response_data.get("collection_id")
            )
            if isinstance(raw_local_id, dict) and "$oid" in raw_local_id:
                payload["local_id"] = str(raw_local_id["$oid"])
            elif raw_local_id is not None:
                payload["local_id"] = str(raw_local_id)
            else:
                payload["local_id"] = None


        # For each payload that has children, fetch and attach them recursively.
        for payload in multilingual_payloads:
            has_sub_child = payload.get("has_sub_child") or payload.get("has_child")

            if not has_sub_child:
                payload["children"] = []
                continue

            # Normalise the **remote/source** ID that should be used as
            # `remote_parent_id` for the next level when talking to OpenPecha.
            raw_remote_id = payload.get("pecha_collection_id")
            next_remote_parent_id: str | None
            if isinstance(raw_remote_id, dict) and "$oid" in raw_remote_id:
                next_remote_parent_id = str(raw_remote_id["$oid"])
            elif raw_remote_id is not None:
                next_remote_parent_id = str(raw_remote_id)
            else:
                next_remote_parent_id = None

            # If we don't have a usable remote parent id, we can't descend
            # further in the source API.
            if next_remote_parent_id is None:
                payload["children"] = []
                continue

            # The *local* parent_id for children is the ID we just created in
            # the destination backend for this node.
            next_local_parent_id: str | None = payload.get("local_id")

            # Recurse asynchronously for the next level.
            payload["children"] = await self.build_recursive_multilingual_payloads(
                destination_url=destination_url,
                openpecha_api_url=openpecha_api_url,
                access_token=access_token,
                remote_parent_id=next_remote_parent_id,
                local_parent_id=next_local_parent_id,
            )

        return multilingual_payloads

    def build_multilingual_payload(
        self, collections_by_language: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Create a payload that combines collections with the same ID across
        multiple languages into a **single multilingual document per ID**.

        Input (from `get_collections`):

        [
            {
                "language": "en",
                "collections": [
                    {
                        "_id": {"$oid": "..."},
                        "slug": "Liturgy",
                        "title": "Liturgy",
                        "description": "Prayers and rituals",
                        "parent_id": null,
                        "has_sub_child": true
                    },
                    ...
                ],
            },
            {
                "language": "bo",
                "collections": [
                    {
                        "_id": {"$oid": "..."},
                        "slug": "Liturgy",
                        "title": "ཁ་འདོན།",
                        "description": "ཆོ་ག་དང་འདོན་ཆ།",
                        "parent_id": null,
                        "has_sub_child": true
                    },
                    ...
                ],
            },
        ]

        Output (one combined payload per `pecha_collection_id`):

            {
                "pecha_collection_id": "sfsfsf-sfsdf",
                "slug": "Madhyamaka",
                "titles": {
                    "en": "Madhyamaka",
                    "bo": "དབུ་མ།"
                },
                "descriptions": {
                    "en": "Madhyamaka treatises",
                    "bo": "དབུ་མའི་གཞུང་སྣ་ཚོགས།"
                },
                "parent_id": null,
                "has_sub_child": true | false
            }
        """

        combined: dict[str, dict[str, Any]] = {}

        for entry in collections_by_language:
            language = entry["language"]
            for collection in entry["collections"]:
                # --- ID handling -------------------------------------------------
                # Prefer `id`, fall back to `_id` if necessary.
                raw_id = collection.get("id", collection.get("_id"))

                # Normalise ID to a string key, and also store this as
                # `pecha_collection_id` so that the final payload field is a
                # simple string (as in the desired output example).
                if isinstance(raw_id, dict) and "$oid" in raw_id:
                    id_key = str(raw_id["$oid"])
                else:
                    id_key = str(raw_id)

                # --- Parent / child flags ---------------------------------------
                parent_value = collection.get("parent_id", collection.get("parent"))
                has_sub_child_value = collection.get(
                    "has_sub_child", collection.get("has_child")
                )

                if id_key not in combined:
                    combined[id_key] = {
                        "pecha_collection_id": id_key,
                        "slug": collection.get("slug"),
                        "titles": {},
                        # Always initialise description keys for all configured languages.
                        "descriptions": {lang: "" for lang in COLLECTION_LANGUAGES},
                        "parent_id": parent_value,
                        "has_sub_child": has_sub_child_value,
                    }

                # --- Titles / descriptions --------------------------------------
                title_value = collection.get("title")
                if title_value is None:
                    title_value = collection.get("titles", {}).get(language)

                description_value = collection.get("description")
                if description_value is None:
                    description_value = collection.get("descriptions", {}).get(
                        language
                    )

                if title_value is not None:
                    combined[id_key]["titles"][language] = title_value

                    # Always use the English title as the slug so that all
                    # per-language payloads sharing this collection ID have a
                    # consistent, human-readable slug.
                    if language == "en":
                        combined[id_key]["slug"] = title_value

                if description_value is not None:
                    # Ensure the descriptions dictionary exists (it should from
                    # initialisation, but we guard just in case).
                    if "descriptions" not in combined[id_key]:
                        combined[id_key]["descriptions"] = {}
                    combined[id_key]["descriptions"][language] = description_value

        # Return the combined multilingual nodes directly – one payload per
        # `pecha_collection_id`, with `titles` and `descriptions` merged across
        # languages that share the same ID.
        return list(combined.values())
        

