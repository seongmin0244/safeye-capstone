from typing import Literal

from pydantic import BaseModel


SeverityType = Literal[
    "CRITICAL",
    "WARNING",
    "INFO",
]


class AIAnalysisResponse(
    BaseModel
):
    is_danger: bool

    severity: SeverityType

    vlm_description: str

    violated_regulation: str

    action_guide: str