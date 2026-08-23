from typing import Literal, NamedTuple

from sqlalchemy.orm import Session

from app.repositories.weekly_indicator_repository import \
    WeeklyIndicatorRepository
from app.services.weekly_indicator_service import (MINIMUM_COVERAGE_DAYS,
                                                   MINIMUM_ELIGIBLE_POSTINGS)


class ForecastResult(NamedTuple):
    """Forecast prediction for a skill's demand trend"""

    score: float
    direction: Literal["growing", "stable", "declining"]
    confidence: int
    risk: Literal["low", "medium", "high"]
    explanation: str
    calculation_steps: dict


class InsufficientDataResult(NamedTuple):
    """Result when not enough data is available for forecasting"""

    reason: str


class ForecastService:
    """Calculate deterministic forecasts for skill demand trends"""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repository = WeeklyIndicatorRepository()

    def forecast_skill_demand(
        self,
        skill_code: str,
        weeks_history: int = 4,
    ) -> ForecastResult | InsufficientDataResult:
        """Calculate a deterministic forecast for skill demand"""

        weeks_history = max(weeks_history, 3)

        indicators_with_source_skill = self._repository.list_indicators(
            self._session,
            skill=skill_code,
            period_end=None,
        )

        valid_indicators = [
            indicator
            for indicator, _, _ in indicators_with_source_skill
            if (
                indicator.eligible_postings_count >= MINIMUM_ELIGIBLE_POSTINGS
                and indicator.coverage_days >= MINIMUM_COVERAGE_DAYS
            )
        ]

        if len(valid_indicators) < 3:
            return InsufficientDataResult(
                f"Need at least 3 complete weeks with sufficient data, "
                f"but found only {len(valid_indicators)} valid weeks"
            )

        valid_indicators.sort(
            key=lambda indicator: indicator.period_start,
            reverse=True,
        )

        recent_indicators = valid_indicators[:weeks_history]

        skill_shares = [float(ind.skill_share) * 100 for ind in recent_indicators]

        trend_pp = skill_shares[0] - skill_shares[1]
        trend_signal = max(-1.0, min(1.0, trend_pp / 5.0))

        previous_trend_pp = skill_shares[1] - skill_shares[2]
        momentum_pp = trend_pp - previous_trend_pp
        momentum_signal = max(-1.0, min(1.0, momentum_pp / 3.0))

        score = 0.7 * trend_signal + 0.3 * momentum_signal

        if score > 0.2:
            direction = "growing"
        elif score < -0.2:
            direction = "declining"
        else:
            direction = "stable"

        current_indicator = recent_indicators[0]

        coverage_factor = current_indicator.coverage_days / 7.0
        volume_factor = min(
            current_indicator.eligible_postings_count / 100.0,
            1.0,
        )

        confidence = int(100 * (0.6 * coverage_factor + 0.4 * volume_factor))
        confidence = max(0, min(100, confidence))

        if confidence >= 80 and len(recent_indicators) >= 4:
            risk = "low"
        elif confidence >= 50:
            risk = "medium"
        else:
            risk = "high"

        explanation = (
            f"Trend: {trend_pp:+.1f}pp "
            f"({trend_signal:+.2f} signal). "
            f"Momentum: {momentum_pp:+.1f}pp "
            f"({momentum_signal:+.2f} signal). "
            f"Score: {score:.2f} -> {direction}. "
            f"Confidence: {confidence}% from "
            f"{current_indicator.coverage_days}/7 days coverage "
            f"and {current_indicator.eligible_postings_count} "
            f"eligible postings."
        )

        calculation_steps = {
            "trend_pp": round(trend_pp, 2),
            "trend_signal": round(trend_signal, 2),
            "momentum_pp": round(momentum_pp, 2),
            "momentum_signal": round(momentum_signal, 2),
            "coverage_factor": round(coverage_factor, 2),
            "volume_factor": round(volume_factor, 2),
        }

        return ForecastResult(
            score=round(score, 2),
            direction=direction,
            confidence=confidence,
            risk=risk,
            explanation=explanation,
            calculation_steps=calculation_steps,
        )
