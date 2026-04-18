from pydantic import BaseModel
from typing_extensions import Literal


class QuerySpec(BaseModel):
    regions: list[str] | None
    sectors: list[str] | None
    crisis_types: list[str] | None
    min_scale_of_need: int | None
    max_coverage_ratio: float | None
    year_range: tuple[int, int] | None
    hrp_status: list[str] | None
    chronic_neglect_only: bool

    interpretation_confidence: Literal["high", "medium", "low"]
    interpretation_notes: str | None
