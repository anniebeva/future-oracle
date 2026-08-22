from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories.weekly_indicator_repository import WeeklyIndicatorRepository
from app.schemas.weekly_indicator import (
    IndicatorSkillResponse,
    IndicatorSourceResponse,
    WeeklyIndicatorFilters,
    WeeklyIndicatorResponse,
)

router = APIRouter(prefix="/api/indicators", tags=["indicators"])


@router.get("/weekly", response_model=list[WeeklyIndicatorResponse])
def list_weekly_indicators(
    filters: Annotated[WeeklyIndicatorFilters, Query()],
    session: Annotated[Session, Depends(get_db_session)],
) -> list[WeeklyIndicatorResponse]:
    """Return persisted weekly indicators for active sources and skills"""
    rows = WeeklyIndicatorRepository().list_indicators(
        session,
        source=filters.source,
        skill=filters.skill,
        period_start=filters.period_start,
        period_end=filters.period_end,
    )
    return [
        WeeklyIndicatorResponse(
            source=IndicatorSourceResponse(code=source.code, name=source.name),
            skill=IndicatorSkillResponse(code=skill.code, display_name=skill.display_name),
            period_start=indicator.period_start,
            period_end=indicator.period_end,
            eligible_postings_count=indicator.eligible_postings_count,
            matching_postings_count=indicator.matching_postings_count,
            skill_share=indicator.skill_share,
            coverage_days=indicator.coverage_days,
            calculated_at=indicator.calculated_at,
        )
        for indicator, source, skill in rows
    ]
