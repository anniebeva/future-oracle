from typing import Literal

from pydantic import BaseModel


class ForecastSkillResponse(BaseModel):
    """Public skill information for forecast response"""

    code: str
    display_name: str


class ForecastResponse(BaseModel):
    """Forecast prediction for a skill's demand trend"""

    skill: ForecastSkillResponse
    score: float
    direction: Literal["growing", "stable", "declining"]
    confidence: int
    risk: Literal["low", "medium", "high"]
    explanation: str
    calculation_steps: dict


class InsufficientDataResponse(BaseModel):
    """Response when not enough data is available for forecasting"""

    reason: str
