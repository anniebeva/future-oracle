import re

RELIABLE_TECHNICAL_CATEGORIES_BY_SOURCE: dict[str, frozenset[str]] = {
    "muse": frozenset({"software engineering", "software development"}),
    "remotive": frozenset({"software-dev", "software development"}),
}
TECHNICAL_TITLE_KEYWORDS: tuple[str, ...] = (
    "python developer",
    "backend engineer",
    "backend developer",
    "software engineer",
    "software developer",
    "full stack",
    "fullstack",
    "data engineer",
    "machine learning engineer",
    "ml engineer",
    "devops engineer",
    "site reliability engineer",
    "platform engineer",
)
NON_TECHNICAL_TITLE_KEYWORDS: tuple[str, ...] = (
    "recruiter",
    "sales manager",
    "product marketing manager",
    "accountant",
    "customer support",
)


def is_technical_posting(source_code: str, category: str | None, title: str | None) -> bool:
    """Determine technical eligibility from source category and title"""
    normalized_title = _normalize(title)
    if _contains_keyword(normalized_title, NON_TECHNICAL_TITLE_KEYWORDS):
        return False

    normalized_category = _normalize(category)
    reliable_categories = RELIABLE_TECHNICAL_CATEGORIES_BY_SOURCE.get(
        source_code.casefold(), frozenset()
    )
    return normalized_category in reliable_categories or _contains_keyword(
        normalized_title, TECHNICAL_TITLE_KEYWORDS
    )


def _contains_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    """Match a configured keyword as a standalone phrase"""
    return any(re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text) for keyword in keywords)


def _normalize(value: str | None) -> str:
    """Normalize text for deterministic comparisons"""
    return " ".join(value.casefold().split()) if value else ""
