from __future__ import annotations

import json
from typing import Any

from src.config.settings import Settings
from src.domain.models import Case, ExportRecord, PromptRun, StageResult, utc_now_iso
from src.storage.db import get_connection


class CaseRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create(self, case: Case) -> None:
        with get_connection(self.settings) as conn:
            conn.execute(
                """
                INSERT INTO cases (
                  case_id, client_alias, source_text, current_stage,
                  tags_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case.case_id,
                    case.client_alias,
                    case.source_text,
                    case.current_stage,
                    json.dumps(case.tags, ensure_ascii=False),
                    case.created_at,
                    case.updated_at,
                ),
            )
            conn.commit()

    def list_cases(self) -> list[Case]:
        with get_connection(self.settings) as conn:
            rows = conn.execute(
                "SELECT * FROM cases ORDER BY updated_at DESC"
            ).fetchall()
        return [self._row_to_case(row) for row in rows]

    def get(self, case_id: str) -> Case | None:
        with get_connection(self.settings) as conn:
            row = conn.execute(
                "SELECT * FROM cases WHERE case_id = ?",
                (case_id,),
            ).fetchone()
        return self._row_to_case(row) if row else None

    def update_stage(self, case_id: str, stage_name: str) -> None:
        with get_connection(self.settings) as conn:
            conn.execute(
                "UPDATE cases SET current_stage = ?, updated_at = ? WHERE case_id = ?",
                (stage_name, utc_now_iso(), case_id),
            )
            conn.commit()

    def _row_to_case(self, row: Any) -> Case:
        return Case(
            case_id=row["case_id"],
            client_alias=row["client_alias"],
            source_text=row["source_text"],
            current_stage=row["current_stage"],
            tags=json.loads(row["tags_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class StageResultRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def save(self, result: StageResult) -> None:
        with get_connection(self.settings) as conn:
            conn.execute(
                """
                INSERT INTO case_versions (
                  case_id, stage_name, version_no, input_payload, output_payload, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result.case_id,
                    result.stage_name,
                    result.version_no,
                    json.dumps(result.input_payload, ensure_ascii=False),
                    json.dumps(result.output_payload, ensure_ascii=False),
                    result.created_at,
                ),
            )
            conn.commit()

    def next_version_no(self, case_id: str, stage_name: str) -> int:
        with get_connection(self.settings) as conn:
            row = conn.execute(
                """
                SELECT COALESCE(MAX(version_no), 0) AS max_version
                FROM case_versions
                WHERE case_id = ? AND stage_name = ?
                """,
                (case_id, stage_name),
            ).fetchone()
        return int(row["max_version"]) + 1

    def get_latest(self, case_id: str, stage_name: str) -> dict[str, Any] | None:
        with get_connection(self.settings) as conn:
            row = conn.execute(
                """
                SELECT * FROM case_versions
                WHERE case_id = ? AND stage_name = ?
                ORDER BY version_no DESC
                LIMIT 1
                """,
                (case_id, stage_name),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "case_id": row["case_id"],
            "stage_name": row["stage_name"],
            "version_no": row["version_no"],
            "input_payload": json.loads(row["input_payload"]),
            "output_payload": json.loads(row["output_payload"]),
            "created_at": row["created_at"],
        }

    def list_by_case(self, case_id: str) -> list[dict[str, Any]]:
        with get_connection(self.settings) as conn:
            rows = conn.execute(
                """
                SELECT * FROM case_versions
                WHERE case_id = ?
                ORDER BY created_at DESC
                """,
                (case_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "case_id": row["case_id"],
                "stage_name": row["stage_name"],
                "version_no": row["version_no"],
                "input_payload": json.loads(row["input_payload"]),
                "output_payload": json.loads(row["output_payload"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]


class PromptRunRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def save(self, prompt_run: PromptRun) -> None:
        with get_connection(self.settings) as conn:
            conn.execute(
                """
                INSERT INTO prompt_runs (
                  case_id, stage_name, prompt_name, model, temperature,
                  input_summary, raw_response, success, latency_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prompt_run.case_id,
                    prompt_run.stage_name,
                    prompt_run.prompt_name,
                    prompt_run.model,
                    prompt_run.temperature,
                    prompt_run.input_summary,
                    prompt_run.raw_response,
                    int(prompt_run.success),
                    prompt_run.latency_ms,
                    prompt_run.created_at,
                ),
            )
            conn.commit()


class ExportRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def save(self, export_record: ExportRecord) -> None:
        with get_connection(self.settings) as conn:
            conn.execute(
                """
                INSERT INTO exports (case_id, export_type, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    export_record.case_id,
                    export_record.export_type,
                    export_record.content,
                    export_record.created_at,
                ),
            )
            conn.commit()
