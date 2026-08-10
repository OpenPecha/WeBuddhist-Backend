from typing import List
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.traditions.tradition_constants import DEFAULT_CHAT_LANGUAGE, tradition_id_from_code
from pecha_api.traditions.tradition_onboarding import (
    get_tradition_onboarding_content,
    get_tradition_path_entry,
    list_tradition_path_codes,
)
from pecha_api.traditions.tradition_repository import (
    delete_user_tradition,
    get_user_traditions,
    save_user_tradition,
    update_user_tradition,
)
from pecha_api.traditions.tradition_response_models import (
    SaveUserTraditionRequest,
    TraditionListItemDTO,
    TraditionListResponse,
    TraditionOnboardingPathsDTO,
    TraditionOnboardingPathDTO,
    TraditionOnboardingResponse,
    UserTraditionDTO,
    UserTraditionsResponse,
)
from pecha_api.users.users_service import validate_and_extract_user_details


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


async def update_user_tradition_service(
    token: str,
    user_tradition_id: UUID,
    update_request: SaveUserTraditionRequest,
) -> UserTraditionDTO:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        try:
            user_tradition = update_user_tradition(
                db=db,
                user_id=current_user.id,
                user_tradition_id=user_tradition_id,
                tradition_code=update_request.tradition_code,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        return _build_user_tradition_dto(
            user_tradition=user_tradition,
            tradition_code=update_request.tradition_code,
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
    for code in sorted(list_tradition_path_codes()):
        path_entry = get_tradition_path_entry(code, language=language)
        if path_entry is None:
            continue
        traditions.append(
            TraditionListItemDTO(
                code=code,
                name=path_entry["title"],
                regions=[],
            )
        )
    return TraditionListResponse(traditions=traditions)


async def get_tradition_onboarding_service(
    language: str = DEFAULT_CHAT_LANGUAGE,
) -> TraditionOnboardingResponse:
    content = get_tradition_onboarding_content(language=language)
    paths = content["paths"]
    return TraditionOnboardingResponse(
        title=content["title"],
        subtitle=content["subtitle"],
        option_intro=content["option_intro"],
        paths=TraditionOnboardingPathsDTO(
            pali=TraditionOnboardingPathDTO(**paths["pali"]),
            chinese=TraditionOnboardingPathDTO(**paths["chinese"]),
            tibetan=TraditionOnboardingPathDTO(**paths["tibetan"]),
        ),
        footer=content["footer"],
    )


def _build_user_tradition_dto_from_record(user_tradition, language: str) -> UserTraditionDTO:
    tradition_code = _resolve_tradition_code(user_tradition)
    return _build_user_tradition_dto(
        user_tradition=user_tradition,
        tradition_code=tradition_code,
        language=language,
    )


def _resolve_tradition_code(user_tradition) -> str:
    tradition_id = user_tradition.tradition_id
    for code in list_tradition_path_codes():
        if tradition_id_from_code(code) == tradition_id:
            return code

    if user_tradition.tradition and user_tradition.tradition.metadata_entries:
        for metadata in user_tradition.tradition.metadata_entries:
            if metadata.language == LanguageCode.EN:
                return metadata.name
        return user_tradition.tradition.metadata_entries[0].name

    return str(tradition_id)


def _build_user_tradition_dto(user_tradition, tradition_code: str, language: str) -> UserTraditionDTO:
    path_entry = get_tradition_path_entry(tradition_code, language=language)
    tradition_name = path_entry["title"] if path_entry else tradition_code
    return UserTraditionDTO(
        id=user_tradition.id,
        tradition_code=tradition_code,
        tradition_name=tradition_name,
        created_at=user_tradition.created_at,
        updated_at=user_tradition.updated_at,
    )
