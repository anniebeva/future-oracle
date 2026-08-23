from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.job_posting import JobPosting
from app.repositories.job_posting_repository import JobPostingRepository
from app.schemas.job_posting import (JobPostingFilters, JobPostingResponse,
                                     JobSkillResponse, JobSourceResponse)

router = APIRouter(prefix="/api", tags=["jobs"])


@router.get("/jobs", response_model=list[JobPostingResponse])
def list_jobs(
    filters: Annotated[JobPostingFilters, Query()],
    session: Annotated[Session, Depends(get_db_session)],
) -> list[JobPostingResponse]:
    """Return persisted active job postings with current matched skills"""
    postings = JobPostingRepository().list_postings(
        session,
        source=filters.source,
        skill=filters.skill,
        location=filters.location,
        is_remote=filters.is_remote,
        published_from=filters.published_from,
        published_to=filters.published_to,
        search=filters.search,
    )
    return [_to_response(posting) for posting in postings]


def _to_response(posting: JobPosting) -> JobPostingResponse:
    """Map one loaded posting to its public response schema"""
    current_skills = sorted(
        {
            (match.skill.code, match.skill.display_name)
            for match in posting.skill_matches
            if match.skill.is_active
            and match.dictionary_version == match.skill.dictionary_version
        }
    )
    return JobPostingResponse(
        id=posting.id,
        source=JobSourceResponse(code=posting.source.code, name=posting.source.name),
        external_id=posting.external_id,
        title=posting.title,
        company_name=posting.company_name,
        source_url=posting.source_url,
        published_at=posting.published_at,
        location_raw=posting.location_raw,
        location_scope=posting.location_scope,
        is_remote=posting.is_remote,
        category=posting.category,
        employment_type=posting.employment_type,
        description_text=posting.description_text,
        skills=[
            JobSkillResponse(code=code, display_name=display_name)
            for code, display_name in current_skills
        ],
    )
