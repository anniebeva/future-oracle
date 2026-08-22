from pydantic import BaseModel


class DataSourceResponse(BaseModel):
    """Public data source reference entry"""

    code: str
    name: str
    base_url: str


class SkillResponse(BaseModel):
    """Public skill reference entry"""

    code: str
    display_name: str
    dictionary_version: int
