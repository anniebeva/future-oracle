from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories.reference_repository import ReferenceRepository
from app.schemas.forecast import (ForecastResponse, ForecastSkillResponse,
                                  InsufficientDataResponse)
from app.services.forecast_service import (ForecastService,
                                           InsufficientDataResult)

router = APIRouter(prefix="/api/forecasts", tags=["forecasts"])


@router.get(
    "/skills/{skill_code}",
    response_model=ForecastResponse | InsufficientDataResponse,
)
def get_forecast(
    skill_code: str,
    session: Annotated[Session, Depends(get_db_session)],
    weeks_history: int = Query(4, ge=3),
) -> ForecastResponse | InsufficientDataResponse:
    """Get forecast for a specific skill"""
    reference_repository = ReferenceRepository()
    skills = reference_repository.list_skills(session)

    skill = next((item for item in skills if item.code == skill_code), None)

    if skill is None:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )

    result = ForecastService(session).forecast_skill_demand(
        skill_code=skill_code,
        weeks_history=weeks_history,
    )

    if isinstance(result, InsufficientDataResult):
        return InsufficientDataResponse(reason=result.reason)

    return ForecastResponse(
        skill=ForecastSkillResponse(
            code=skill.code,
            display_name=skill.display_name,
        ),
        score=result.score,
        direction=result.direction,
        confidence=result.confidence,
        risk=result.risk,
        explanation=result.explanation,
        calculation_steps=result.calculation_steps,
    )
