import logging
from typing import List
from uuid import UUID

import httpx
from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.traditions.llm_client import chat_with_worker
from pecha_api.traditions.tradition_constants import DEFAULT_CHAT_LANGUAGE
from pecha_api.traditions.tradition_llm_utils import parse_llm_json_response
from pecha_api.traditions.tradition_prompt import build_tradition_chat_system_prompt
from pecha_api.traditions.tradition_repository import (
    delete_user_tradition,
    get_user_traditions,
    save_user_tradition,
)
from pecha_api.traditions.tradition_response_models import (
    SaveUserTraditionRequest,
    SuggestedTradition,
    TraditionChatMessage,
    TraditionChatRequest,
    TraditionChatResponse,
    TraditionListItemDTO,
    TraditionListResponse,
    UserTraditionDTO,
    UserTraditionsResponse,
)
from pecha_api.traditions.tradition_taxonomy import (
    get_tradition_display_name,
    get_tradition_entry,
    list_tradition_codes,
    load_tradition_taxonomy,
    tradition_id_from_code,
)
from pecha_api.users.users_service import validate_and_extract_user_details


def _build_conversation_prompt(messages: List[TraditionChatMessage]) -> str:
    lines: list[str] = []
    for message in messages:
        speaker = "User" if message.role == "user" else "Assistant"
        lines.append(f"{speaker}: {message.content}")
    return "\n\n".join(lines)


def _normalize_suggested_traditions(
    suggested_traditions: list,
    language: str,
) -> List[SuggestedTradition]:
    allowed_codes = list_tradition_codes()
    normalized: list[SuggestedTradition] = []
    seen_codes: set[str] = set()

    for item in suggested_traditions:
        if not isinstance(item, dict):
            continue

        code = str(item.get("code", "")).strip()
        if not code or code not in allowed_codes or code in seen_codes:
            continue

        entry = get_tradition_entry(code)
        name = item.get("name") or (get_tradition_display_name(entry, language) if entry else code)
        normalized.append(SuggestedTradition(code=code, name=name))
        seen_codes.add(code)

    return normalized


def _normalize_follow_up_questions(follow_up_questions: list) -> List[str]:
    normalized: list[str] = []
    for question in follow_up_questions:
        if not isinstance(question, str):
            continue
        cleaned = question.strip()
        if cleaned:
            normalized.append(cleaned)
    return normalized


def _normalize_selected_tradition_code(selected_code: object) -> str | None:
    if selected_code in (None, "", "null"):
        return None

    normalized = str(selected_code).strip()
    if normalized not in list_tradition_codes():
        return None
    return normalized


async def tradition_chat_service(
    token: str,
    chat_request: TraditionChatRequest,
) -> TraditionChatResponse:
    validate_and_extract_user_details(token=token)

    language = chat_request.language.lower() if chat_request.language else DEFAULT_CHAT_LANGUAGE
    system_prompt = build_tradition_chat_system_prompt(language=language)
    prompt = _build_conversation_prompt(chat_request.messages)

    try:
        worker_response = await chat_with_worker(
            prompt=prompt,
            system_prompt=system_prompt,
        )
    except httpx.HTTPStatusError as exc:
        logging.exception("Tradition chat worker request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Tradition assistant is temporarily unavailable",
        ) from exc
    except httpx.RequestError as exc:
        logging.exception("Tradition chat worker request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach tradition assistant service",
        ) from exc

    raw_response = worker_response.get("response", "")
    try:
        parsed_response = parse_llm_json_response(raw_response)
    except (TypeError, ValueError) as exc:
        logging.exception("Failed to parse tradition chat LLM response: %s", raw_response)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Tradition assistant returned an invalid response",
        ) from exc

    selected_tradition_code = _normalize_selected_tradition_code(
        parsed_response.get("selected_tradition_code")
    )
    is_complete = bool(parsed_response.get("is_complete")) and selected_tradition_code is not None

    return TraditionChatResponse(
        message=str(parsed_response.get("message", "")).strip(),
        suggested_traditions=_normalize_suggested_traditions(
            parsed_response.get("suggested_traditions", []),
            language=language,
        ),
        follow_up_questions=_normalize_follow_up_questions(
            parsed_response.get("follow_up_questions", [])
        ),
        is_complete=is_complete,
        selected_tradition_code=selected_tradition_code if is_complete else None,
        model=worker_response.get("model", ""),
    )


async def save_user_tradition_service(
    token: str,
    save_request: SaveUserTraditionRequest,
) -> UserTraditionDTO:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        user_tradition = save_user_tradition(
            db=db,
            user_id=current_user.id,
            tradition_code=save_request.tradition_code,
        )

        return _build_user_tradition_dto(
            user_tradition=user_tradition,
            tradition_code=save_request.tradition_code,
            language=DEFAULT_CHAT_LANGUAGE,
        )


async def delete_user_tradition_service(token: str, user_tradition_id: UUID) -> None:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        delete_user_tradition(
            db=db,
            user_id=current_user.id,
            user_tradition_id=user_tradition_id,
        )


async def get_user_traditions_service(token: str) -> UserTraditionsResponse:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        user_traditions = get_user_traditions(db=db, user_id=current_user.id)
        traditions = [
            _build_user_tradition_dto_from_record(user_tradition, language=DEFAULT_CHAT_LANGUAGE)
            for user_tradition in user_traditions
        ]
        return UserTraditionsResponse(traditions=traditions)


async def list_traditions_service(language: str = DEFAULT_CHAT_LANGUAGE) -> TraditionListResponse:
    traditions: list[TraditionListItemDTO] = []
    for entry in load_tradition_taxonomy()["traditions"]:
        traditions.append(
            TraditionListItemDTO(
                code=entry["id"],
                name=get_tradition_display_name(entry, language),
                level=entry["level"],
                parent_code=entry.get("parent"),
                regions=entry.get("regions") or [],
            )
        )
    return TraditionListResponse(traditions=traditions)


def _build_user_tradition_dto_from_record(user_tradition, language: str) -> UserTraditionDTO:
    tradition_code = _resolve_tradition_code(user_tradition)
    return _build_user_tradition_dto(
        user_tradition=user_tradition,
        tradition_code=tradition_code,
        language=language,
    )


def _resolve_tradition_code(user_tradition) -> str:
    tradition_id = user_tradition.tradition_id
    for entry in load_tradition_taxonomy()["traditions"]:
        if tradition_id_from_code(entry["id"]) == tradition_id:
            return entry["id"]

    if user_tradition.tradition and user_tradition.tradition.metadata_entries:
        for metadata in user_tradition.tradition.metadata_entries:
            if metadata.language == LanguageCode.EN:
                return metadata.name
        return user_tradition.tradition.metadata_entries[0].name

    return str(tradition_id)


def _build_user_tradition_dto(user_tradition, tradition_code: str, language: str) -> UserTraditionDTO:
    entry = get_tradition_entry(tradition_code)
    return UserTraditionDTO(
        id=user_tradition.id,
        tradition_code=tradition_code,
        tradition_name=get_tradition_display_name(entry, language) if entry else tradition_code,
        level=entry["level"] if entry else 0,
        parent_code=entry.get("parent") if entry else None,
        created_at=user_tradition.created_at,
        updated_at=user_tradition.updated_at,
    )
