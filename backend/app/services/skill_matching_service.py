import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_posting import JobPosting
from app.models.job_skill_match import JobSkillMatch
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.services.skill_seed import INITIAL_DICTIONARY_VERSION, alias_order


@dataclass(frozen=True)
class _SkillEvidence:
    """Deterministic match evidence for one skill"""

    matched_alias: str
    matched_in_title: bool
    matched_in_description: bool
    match_count: int


class SkillMatchingService:
    """Synchronize deterministic skill matches for job postings"""

    def match_job_posting(
        self,
        session: Session,
        job_posting_id: int,
        dictionary_version: int = INITIAL_DICTIONARY_VERSION,
    ) -> list[JobSkillMatch]:
        """Synchronize matches for one posting and dictionary version"""
        posting = session.get(JobPosting, job_posting_id)
        if posting is None:
            raise ValueError(f"Job posting {job_posting_id} was not found")

        title = self._normalize_text(posting.title)
        description = self._normalize_text(posting.description_text)
        evidence_by_skill = self._collect_evidence(session, title, description)
        existing_matches = {
            match.skill_id: match
            for match in session.scalars(
                select(JobSkillMatch).where(
                    JobSkillMatch.job_posting_id == posting.id,
                    JobSkillMatch.dictionary_version == dictionary_version,
                )
            )
        }

        synchronized_matches: list[JobSkillMatch] = []
        for skill_id, evidence in evidence_by_skill.items():
            match = existing_matches.pop(skill_id, None)
            if match is None:
                match = JobSkillMatch(
                    job_posting_id=posting.id,
                    skill_id=skill_id,
                    dictionary_version=dictionary_version,
                    matched_alias=evidence.matched_alias,
                    matched_in_title=evidence.matched_in_title,
                    matched_in_description=evidence.matched_in_description,
                    match_count=evidence.match_count,
                )
                session.add(match)
            else:
                match.matched_alias = evidence.matched_alias
                match.matched_in_title = evidence.matched_in_title
                match.matched_in_description = evidence.matched_in_description
                match.match_count = evidence.match_count
            synchronized_matches.append(match)

        for stale_match in existing_matches.values():
            session.delete(stale_match)

        session.flush()
        return synchronized_matches

    def match_job_postings(
        self,
        session: Session,
        job_posting_ids: list[int],
        dictionary_version: int = INITIAL_DICTIONARY_VERSION,
    ) -> list[JobSkillMatch]:
        """Synchronize matches for multiple postings"""
        matches: list[JobSkillMatch] = []
        for job_posting_id in job_posting_ids:
            matches.extend(self.match_job_posting(session, job_posting_id, dictionary_version))
        return matches

    def _collect_evidence(
        self,
        session: Session,
        title: str,
        description: str,
    ) -> dict[int, _SkillEvidence]:
        """Collect evidence for all active configured skills"""
        skills = session.scalars(
            select(Skill).where(Skill.is_active.is_(True)).order_by(Skill.code)
        ).all()
        aliases = session.scalars(
            select(SkillAlias)
            .join(Skill)
            .where(Skill.is_active.is_(True), SkillAlias.is_active.is_(True))
        ).all()
        aliases_by_skill: dict[int, list[SkillAlias]] = {}
        for alias in aliases:
            aliases_by_skill.setdefault(alias.skill_id, []).append(alias)

        evidence: dict[int, _SkillEvidence] = {}
        for skill in skills:
            skill_aliases = aliases_by_skill.get(skill.id, [])
            if not skill_aliases:
                continue
            ordered_aliases = self._ordered_aliases(skill.code, skill_aliases)
            title_matches = self._matches_for_text(title, ordered_aliases)
            description_matches = self._matches_for_text(description, ordered_aliases)
            all_matches = title_matches + description_matches
            if not all_matches:
                continue
            evidence[skill.id] = _SkillEvidence(
                matched_alias=self._representative_alias(ordered_aliases, title, description),
                matched_in_title=bool(title_matches),
                matched_in_description=bool(description_matches),
                match_count=len(all_matches),
            )
        return evidence

    def _ordered_aliases(self, skill_code: str, aliases: list[SkillAlias]) -> list[SkillAlias]:
        """Order aliases by configured priority then alphabetically"""
        configured_order = {
            self._normalize_text(alias): position
            for position, alias in enumerate(alias_order(skill_code))
        }
        return sorted(
            aliases,
            key=lambda alias: (
                configured_order.get(self._normalize_text(alias.alias), len(configured_order)),
                self._normalize_text(alias.alias),
            ),
        )

    def _matches_for_text(self, text: str, aliases: list[SkillAlias]) -> list[str]:
        """Count non-overlapping aliases, preferring longest overlaps"""
        candidates: list[tuple[int, int, int, str]] = []
        for priority, alias in enumerate(aliases):
            normalized_alias = self._normalize_text(alias.alias)
            pattern = re.compile(rf"(?<!\w){re.escape(normalized_alias)}(?!\w)")
            for occurrence in pattern.finditer(text):
                candidates.append((occurrence.start(), occurrence.end(), priority, alias.alias))

        candidates.sort(
            key=lambda candidate: (
                candidate[0],
                -(candidate[1] - candidate[0]),
                candidate[2],
            )
        )
        matches: list[str] = []
        next_available_position = 0
        for start, end, _, alias in candidates:
            if start < next_available_position:
                continue
            matches.append(alias)
            next_available_position = end
        return matches

    def _representative_alias(
        self,
        aliases: list[SkillAlias],
        title: str,
        description: str,
    ) -> str:
        """Choose the first configured alias present in either text"""
        for alias in aliases:
            normalized_alias = self._normalize_text(alias.alias)
            pattern = re.compile(rf"(?<!\w){re.escape(normalized_alias)}(?!\w)")
            if pattern.search(title) or pattern.search(description):
                return alias.alias
        raise ValueError("Match evidence must include an alias")

    @staticmethod
    def _normalize_text(text: str | None) -> str:
        return " ".join(text.casefold().split()) if text else ""
