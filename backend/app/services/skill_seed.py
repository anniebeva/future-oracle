from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.models.skill_alias import SkillAlias

INITIAL_DICTIONARY_VERSION = 1
INITIAL_SKILLS: tuple[dict[str, str | tuple[str, ...]], ...] = (
    {
        "code": "python",
        "display_name": "Python",
        "aliases": ("python", "python3", "python 3"),
    },
    {"code": "django", "display_name": "Django", "aliases": ("django",)},
    {
        "code": "fastapi",
        "display_name": "FastAPI",
        "aliases": ("fastapi", "fast api"),
    },
    {
        "code": "postgresql",
        "display_name": "PostgreSQL",
        "aliases": ("postgresql", "postgres"),
    },
    {
        "code": "docker",
        "display_name": "Docker",
        "aliases": ("docker", "containerization"),
    },
    {
        "code": "aws",
        "display_name": "AWS",
        "aliases": ("aws", "amazon web services"),
    },
)


def seed_initial_skills(session: Session) -> list[Skill]:
    """Create or update the explicit version-one skill dictionary"""
    skills: list[Skill] = []

    for definition in INITIAL_SKILLS:
        code = str(definition["code"])
        display_name = str(definition["display_name"])
        aliases = definition["aliases"]
        if not isinstance(aliases, tuple):
            raise ValueError(f"Invalid aliases for {code}")

        skill = session.scalar(select(Skill).where(Skill.code == code))
        if skill is None:
            skill = Skill(
                code=code,
                display_name=display_name,
                dictionary_version=INITIAL_DICTIONARY_VERSION,
                is_active=True,
            )
            session.add(skill)
            session.flush()
        else:
            skill.display_name = display_name
            skill.dictionary_version = INITIAL_DICTIONARY_VERSION
            skill.is_active = True

        _seed_aliases(session, skill, aliases)
        skills.append(skill)

    session.flush()
    return skills


def alias_order(skill_code: str) -> tuple[str, ...]:
    """Return the explicit alias order for an initial skill"""
    for definition in INITIAL_SKILLS:
        if definition["code"] == skill_code:
            aliases = definition["aliases"]
            if isinstance(aliases, tuple):
                return aliases
    return ()


def _seed_aliases(session: Session, skill: Skill, aliases: Sequence[str]) -> None:
    """Create or reactivate aliases for one skill"""
    for alias in aliases:
        skill_alias = session.scalar(
            select(SkillAlias).where(
                SkillAlias.skill_id == skill.id,
                SkillAlias.alias == alias,
            )
        )
        if skill_alias is None:
            session.add(
                SkillAlias(
                    skill_id=skill.id,
                    alias=alias,
                    match_type="token",
                    is_active=True,
                )
            )
        else:
            skill_alias.match_type = "token"
            skill_alias.is_active = True
