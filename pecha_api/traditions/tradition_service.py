from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.traditions.tradition_constants import (
    DEFAULT_CHAT_LANGUAGE,
    ONBOARDING_TRADITION_CODES,
)
from pecha_api.traditions.tradition_onboarding import get_tradition_onboarding_chrome
from pecha_api.traditions.tradition_repository import (
    create_tradition,
    delete_tradition,
    delete_user_tradition,
    get_tradition_by_code,
    get_tradition_by_id,
    get_user_traditions,
    list_traditions,
    list_traditions_cms,
    resolve_tradition_metadata,
    save_user_tradition,
    update_tradition,
    update_user_tradition,
)
from pecha_api.traditions.tradition_response_models import (
    CreateTraditionRequest,
    SaveUserTraditionRequest,
    TraditionCMSDTO,
    TraditionListItemDTO,
    TraditionListResponse,
    TraditionMetadataDTO,
    TraditionOnboardingPathsDTO,
    TraditionOnboardingPathDTO,
    TraditionOnboardingResponse,
    TraditionsCMSListResponse,
    UpdateTraditionRequest,
    UserTraditionDTO,
    UserTraditionsResponse,
)
from pecha_api.users.users_service import validate_and_extract_user_details


async def save_user_tradition_service(
    token: str,
    save_request: SaveUserTraditionRequest,
    language: str = DEFAULT_CHAT_LANGUAGE,
) -> UserTraditionDTO:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        user_tradition = save_user_tradition(
            db=db,
            user_id=current_user.id,
            tradition_code=save_request.tradition_code,
        )
        return _build_user_tradition_dto(user_tradition=user_tradition, language=language)


async def update_user_tradition_service(
    token: str,
    user_tradition_id: UUID,
    update_request: SaveUserTraditionRequest,
    language: str = DEFAULT_CHAT_LANGUAGE,
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

        return _build_user_tradition_dto(user_tradition=user_tradition, language=language)


async def delete_user_tradition_service(token: str, user_tradition_id: UUID) -> None:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        delete_user_tradition(
            db=db,
            user_id=current_user.id,
            user_tradition_id=user_tradition_id,
        )


async def get_user_traditions_service(
    token: str,
    language: str = DEFAULT_CHAT_LANGUAGE,
) -> UserTraditionsResponse:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        user_traditions = get_user_traditions(db=db, user_id=current_user.id)
        traditions = [
            _build_user_tradition_dto(user_tradition, language=language)
            for user_tradition in user_traditions
        ]
        return UserTraditionsResponse(traditions=traditions)


async def list_traditions_service(language: str = DEFAULT_CHAT_LANGUAGE) -> TraditionListResponse:
    with SessionLocal() as db:
        traditions = list_traditions(db=db)
        items: List[TraditionListItemDTO] = []
        for tradition in traditions:
            metadata = resolve_tradition_metadata(tradition, language=language)
            items.append(
                TraditionListItemDTO(
                    code=tradition.code,
                    name=metadata.name if metadata else tradition.code,
                    regions=list(tradition.regions or []),
                )
            )
        return TraditionListResponse(traditions=items)


async def get_tradition_onboarding_service(
    language: str = DEFAULT_CHAT_LANGUAGE,
) -> TraditionOnboardingResponse:
    chrome = get_tradition_onboarding_chrome(language=language)

    with SessionLocal() as db:
        paths: dict[str, TraditionOnboardingPathDTO] = {}
        for code in sorted(ONBOARDING_TRADITION_CODES):
            tradition = get_tradition_by_code(db=db, tradition_code=code)
            if tradition is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tradition catalog is incomplete; missing: {code}",
                )
            metadata = resolve_tradition_metadata(tradition, language=language)
            paths[code] = TraditionOnboardingPathDTO(
                title=metadata.name if metadata else code,
                description=(metadata.description if metadata and metadata.description else ""),
            )

        return TraditionOnboardingResponse(
            title=chrome["title"],
            subtitle=chrome["subtitle"],
            option_intro=chrome["option_intro"],
            paths=TraditionOnboardingPathsDTO(**paths),
            footer=chrome["footer"],
        )


def get_cms_traditions_list(
    token: str,
    *,
    search: Optional[str] = None,
    language: str = "EN",
    skip: int = 0,
    limit: int = 20,
) -> TraditionsCMSListResponse:
    validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        traditions, total = list_traditions_cms(
            db=db,
            search=search,
            skip=skip,
            limit=limit,
        )
        return TraditionsCMSListResponse(
            traditions=[
                _build_cms_tradition_dto(tradition, language=language)
                for tradition in traditions
            ],
            skip=skip,
            limit=limit,
            total=total,
        )


def get_cms_tradition_detail(
    token: str,
    tradition_id: UUID,
    language: str = "EN",
) -> TraditionCMSDTO:
    validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        tradition = get_tradition_by_id(db=db, tradition_id=tradition_id)
        if tradition is None or tradition.code.startswith("legacy_"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tradition with ID {tradition_id} not found",
            )
        return _build_cms_tradition_dto(tradition, language=language)


async def create_cms_tradition(
    token: str,
    create_request: CreateTraditionRequest,
    language: str = "EN",
) -> TraditionCMSDTO:
    validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        tradition = create_tradition(
            db=db,
            code=create_request.code,
            regions=create_request.regions,
            parent_id=create_request.parent_id,
            metadata_inputs=create_request.metadata,
        )
        return _build_cms_tradition_dto(tradition, language=language)


async def update_cms_tradition(
    token: str,
    tradition_id: UUID,
    update_request: UpdateTraditionRequest,
    language: str = "EN",
) -> TraditionCMSDTO:
    validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        tradition = update_tradition(
            db=db,
            tradition_id=tradition_id,
            code=update_request.code,
            regions=update_request.regions,
            parent_id=update_request.parent_id,
            metadata_inputs=update_request.metadata,
        )
        return _build_cms_tradition_dto(tradition, language=language)


def delete_cms_tradition(token: str, tradition_id: UUID) -> None:
    validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        delete_tradition(db=db, tradition_id=tradition_id)


def _build_cms_tradition_dto(tradition, language: str) -> TraditionCMSDTO:
    localized = resolve_tradition_metadata(tradition, language=language)
    metadata = [
        TraditionMetadataDTO(
            id=entry.id,
            language=(
                entry.language.value
                if hasattr(entry.language, "value")
                else str(entry.language)
            ),
            name=entry.name,
            description=entry.description,
            other_names=list(entry.other_names or []) if entry.other_names else None,
        )
        for entry in sorted(
            tradition.metadata_entries or [],
            key=lambda item: (
                item.language.value
                if hasattr(item.language, "value")
                else str(item.language)
            ),
        )
    ]
    return TraditionCMSDTO(
        id=tradition.id,
        code=tradition.code,
        regions=list(tradition.regions or []),
        parent_id=tradition.parent_id,
        name=localized.name if localized else tradition.code,
        description=localized.description if localized else None,
        metadata=metadata,
    )


def _build_user_tradition_dto(user_tradition, language: str) -> UserTraditionDTO:
    tradition = user_tradition.tradition
    if tradition is None:
        tradition_code = str(user_tradition.tradition_id)
        tradition_name = tradition_code
    else:
        tradition_code = tradition.code
        metadata = resolve_tradition_metadata(tradition, language=language)
        tradition_name = metadata.name if metadata else tradition_code

    return UserTraditionDTO(
        id=user_tradition.id,
        tradition_code=tradition_code,
        tradition_name=tradition_name,
        created_at=user_tradition.created_at,
        updated_at=user_tradition.updated_at,
    )
