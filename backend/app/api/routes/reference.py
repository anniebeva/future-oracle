from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories.reference_repository import ReferenceRepository
from app.schemas.reference import DataSourceResponse, SkillResponse

router = APIRouter(prefix="/api", tags=["reference"])


@router.get("/sources", response_model=list[DataSourceResponse])
def list_sources(
    session: Annotated[Session, Depends(get_db_session)],
) -> list[DataSourceResponse]:
    """Return active sources for frontend filters"""
    return [
        DataSourceResponse(code=source.code, name=source.name, base_url=source.base_url)
        for source in ReferenceRepository().list_sources(session)
    ]


@router.get("/skills", response_model=list[SkillResponse])
def list_skills(
    session: Annotated[Session, Depends(get_db_session)],
) -> list[SkillResponse]:
    """Return active skills for frontend filters"""
    return [
        SkillResponse(
            code=skill.code,
            display_name=skill.display_name,
            dictionary_version=skill.dictionary_version,
        )
        for skill in ReferenceRepository().list_skills(session)
    ]
