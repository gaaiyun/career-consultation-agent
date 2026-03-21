from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_case_id() -> str:
    return f"case_{uuid.uuid4().hex[:12]}"


@dataclass
class Case:
    case_id: str
    client_alias: str
    source_text: str
    current_stage: str = "intake"
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StageResult:
    case_id: str
    stage_name: str
    version_no: int
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PromptRun:
    case_id: str
    stage_name: str
    prompt_name: str
    model: str
    temperature: float
    input_summary: str
    raw_response: str
    success: bool
    latency_ms: int
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExportRecord:
    case_id: str
    export_type: str
    content: str
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
