from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StageDefinition:
    name: str
    prompt_name: str
    temperature: float
    max_tokens: int
    expects_json: bool = True


STRUCTURED_ANALYSIS = StageDefinition(
    name="structured_analysis",
    prompt_name="structured_analysis",
    temperature=0.2,
    max_tokens=1600,
    expects_json=True,
)

QUESTIONING = StageDefinition(
    name="questioning",
    prompt_name="question_generation",
    temperature=0.3,
    max_tokens=1100,
    expects_json=True,
)

ROUTE_PLANNING = StageDefinition(
    name="route_planning",
    prompt_name="route_planning",
    temperature=0.3,
    max_tokens=1600,
    expects_json=True,
)

FINAL_REPORT = StageDefinition(
    name="final_report",
    prompt_name="final_report",
    temperature=0.4,
    max_tokens=1500,
    expects_json=False,
)

STAGE_ORDER = [
    "intake",
    STRUCTURED_ANALYSIS.name,
    QUESTIONING.name,
    ROUTE_PLANNING.name,
    FINAL_REPORT.name,
]
