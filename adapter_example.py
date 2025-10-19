"""Enhanced Adapter Example for Bridging Legacy and Modern Agent APIs

This module demonstrates a realistic adapter pattern with:
- Input parameter validation and type conversion
- Structured error handling and logging
- Fallback/safe operation path via `safe_act`
- Clear, actionable docstrings for maintainers

The adapter translates a modern API surface to a legacy implementation while
ensuring safer runtime behavior and predictable response shapes.

Author: Architecture Integration Team
Date: October 2025
"""
from __future__ import annotations

from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import logging

# Configure logging for library + demo usage
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegacyAgentAPI:
    """Simulates a legacy agent API with old-style methods and data structures.

    The legacy API exposes:
    - execute_task(task_id, params): returns a dict with primitive fields
    - get_status(task_id): returns a pipe-delimited status string
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://legacy-api.example.com"
        logger.info(f"Initialized LegacyAgentAPI with base URL: {self.base_url}")

    def execute_task(self, task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using legacy format.

        Args:
            task_id: Unique identifier for the task
            params: Dictionary with keys like 'action', 'priority', 'data'

        Returns:
            Dict with keys: 'status', 'result_code', 'output', 'timestamp'
        """
        logger.info(f"Executing legacy task: {task_id}")
        return {
            "status": "completed",
            "result_code": 200,
            "output": f"Task {task_id} executed with action {params.get('action')}",
            "timestamp": datetime.now().isoformat(),
        }

    def get_status(self, task_id: str) -> str:
        """Get task status in legacy format (simple string)."""
        # In a real system this might query a backing store; we return a synthetic mix
        return "RUNNING|COMPLETED|FAILED"


class ModernAgentAPI:
    """Simulates a modern agent API with updated methods and data structures.

    This is included to document the intended modern surface. The adapter below
    exposes a similar interface while delegating to the legacy API internally.
    """

    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials

    def run(self, job: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def query_status(self, job_id: str) -> Dict[str, Any]:
        raise NotImplementedError


class ValidationError(ValueError):
    """Raised when incoming parameters fail validation."""


class AgentAPIAdapter:
    """Adapter translating modern API calls to the legacy implementation.

    Responsibilities:
    - Validate and coerce incoming modern inputs into legacy-compatible formats
    - Add defensive error handling and structured logging
    - Provide a safe fallback path via `safe_act` when strict execution fails

    Modern interface provided:
    - run(job: Dict[str, Any]) -> Dict[str, Any]
    - query_status(job_id: str) -> Dict[str, Any]
    - safe_act(job: Dict[str, Any]) -> Dict[str, Any]

    Response invariants (modern shape):
    - Always returns a dictionary with keys: success(bool), code(int), data(dict),
      created_at(str, ISO 8601), completed_at(str, ISO 8601)
    """

    def __init__(self, legacy_api: LegacyAgentAPI):
        self.legacy_api = legacy_api

    # --------------- Validation & Conversion helpers ---------------
    @staticmethod
    def _require_keys(mapping: Dict[str, Any], keys: List[str], ctx: str) -> None:
        missing = [k for k in keys if k not in mapping]
        if missing:
            raise ValidationError(f"Missing required keys in {ctx}: {missing}")

    @staticmethod
    def _coerce_priority(value: Any) -> int:
        """Coerce priority to int within 1..5.

        Accepts int-like strings; clamps to the inclusive range [1, 5].
        """
        if isinstance(value, bool):  # avoid True/False being treated as 1/0
            raise ValidationError("Priority must be an integer 1..5, not boolean")
        try:
            iv = int(value)
        except (TypeError, ValueError):
            raise ValidationError("Priority must be an integer 1..5")
        return max(1, min(5, iv))

    @staticmethod
    def _coerce_action(job_type: Any) -> str:
        """Map modern job 'type' to a legacy 'action'."""
        if not isinstance(job_type, str) or not job_type.strip():
            raise ValidationError("job.type must be a non-empty string")
        mapping = {
            "data_processing": "process_data",
            "classification": "classify",
            "summarization": "summarize",
            "ingestion": "ingest",
        }
        return mapping.get(job_type, job_type)  # default: pass-through

    @staticmethod
    def _normalize_payload(payload: Any) -> Dict[str, Any]:
        """Ensure payload is a dictionary; parse JSON strings when provided."""
        if payload is None:
            return {}
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, str):
            payload = payload.strip()
            if not payload:
                return {}
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                raise ValidationError("payload string must be valid JSON object")
            if not isinstance(parsed, dict):
                raise ValidationError("payload JSON must decode to an object")
            return parsed
        raise ValidationError("payload must be a dict or JSON string")

    # --------------- Public modern methods ---------------
    def run(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a modern job via the legacy API.

        Expected job shape (modern):
        - id: str
        - type: str (mapped to legacy 'action')
        - priority: int|str (1..5)
        - payload: dict|json-string (free-form)
        - metadata: optional dict

        Returns modern-shaped response; on validation or runtime errors falls back to
        `safe_act` when possible to provide a graceful response.
        """
        created_at = datetime.now().isoformat()
        try:
            if not isinstance(job, dict):
                raise ValidationError("job must be a dictionary")
            self._require_keys(job, ["id", "type", "priority"], ctx="job")

            job_id = str(job["id"]).strip()
            if not job_id:
                raise ValidationError("job.id must be a non-empty string")

            action = self._coerce_action(job.get("type"))
            priority = self._coerce_priority(job.get("priority"))
            payload = self._normalize_payload(job.get("payload"))

            # Compose legacy params
            legacy_params = {
                "action": action,
                "priority": priority,
                "data": payload,
            }

            legacy_resp = self.legacy_api.execute_task(task_id=job_id, params=legacy_params)

            # Convert legacy to modern response shape
            modern = {
                "success": legacy_resp.get("result_code", 500) == 200,
                "code": int(legacy_resp.get("result_code", 500)),
                "data": {
                    "job_id": job_id,
                    "result": legacy_resp.get("output"),
                    "metrics": {
                        # In a real system, transform or compute metrics
                        "duration_ms": 0,
                        "cpu_usage": 0.0,
                    },
                },
                "created_at": created_at,
                "completed_at": legacy_resp.get("timestamp", datetime.now().isoformat()),
            }
            return modern
        except ValidationError as ve:
            logger.warning(f"Validation failed for job: {ve}")
            return self.safe_act(job, error_msg=str(ve), created_at=created_at)
        except Exception as e:
            logger.exception("Unexpected error while running job")
            return self.safe_act(job, error_msg=str(e), created_at=created_at)

    def query_status(self, job_id: str) -> Dict[str, Any]:
        """Query status for a job ID and convert to modern structure.

        Modern shape:
        - success: bool (True if status includes COMPLETED)
        - code: int (200 when known, 206 for partial/unknown, 500 on error)
        - data: { job_id, status: one-of [RUNNING, COMPLETED, FAILED, UNKNOWN] }
        - created_at/completed_at: ISO 8601 timestamps for traceability
        """
        created_at = datetime.now().isoformat()
        try:
            if not isinstance(job_id, str) or not job_id.strip():
                raise ValidationError("job_id must be a non-empty string")
            legacy_status_pipe = self.legacy_api.get_status(job_id.strip())
            options = [s.strip() for s in str(legacy_status_pipe).split("|") if s.strip()]

            # Pick the most favorable status deterministically for demo; real code would map actual state
            status = "UNKNOWN"
            for candidate in ("COMPLETED", "RUNNING", "FAILED"):
                if candidate in options:
                    status = candidate
                    break

            success = status == "COMPLETED"
            code = 200 if success else (206 if status in {"RUNNING", "UNKNOWN"} else 500)
            return {
                "success": success,
                "code": code,
                "data": {
                    "job_id": job_id,
                    "status": status,
                },
                "created_at": created_at,
                "completed_at": datetime.now().isoformat(),
            }
        except ValidationError as ve:
            logger.warning(f"Validation failed for status query: {ve}")
            return {
                "success": False,
                "code": 400,
                "data": {"job_id": job_id, "status": "UNKNOWN", "error": str(ve)},
                "created_at": created_at,
                "completed_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.exception("Unexpected error while querying status")
            return {
                "success": False,
                "code": 500,
                "data": {"job_id": job_id, "status": "UNKNOWN", "error": str(e)},
                "created_at": created_at,
                "completed_at": datetime.now().isoformat(),
            }

    # --------------- Fallback path ---------------
    def safe_act(self, job: Dict[str, Any], *, error_msg: str, created_at: Optional[str] = None) -> Dict[str, Any]:
        """Return a conservative, consistent response when strict execution fails.

        Behavior:
        - Best-effort extraction of job_id
        - Returns a standardized error payload with safe defaults
        - Never raises; always returns a modern-shaped response

        Args:
            job: The original job dictionary (possibly malformed)
            error_msg: Human-readable error message used for diagnostics
            created_at: Optional created time to preserve trace continuity
        """
        job_id = "unknown"
        try:
            if isinstance(job, dict) and job.get("id"):
                job_id = str(job.get("id")).strip() or "unknown"
        except Exception:
            # Ignore extraction issues
            pass

        return {
            "success": False,
            "code": 500,
            "data": {
                "job_id": job_id,
                "result": f"Error: {error_msg}",
                "metrics": {"duration_ms": 0, "cpu_usage": 0.0},
            },
            "created_at": created_at or datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
        }


# ------------------------- Example usage -------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("Agent API Adapter Example")
    print("=" * 70)

    # Initialize legacy API
    legacy_api = LegacyAgentAPI(api_key="legacy_key_12345")

    # Create adapter
    adapter = AgentAPIAdapter(legacy_api)

    # Create a modern-style job
    modern_job = {
        "id": "job_2025_001",
        "type": "data_processing",
        "priority": 3,  # try also "4" to test coercion
        "payload": {
            "input_file": "data.csv",
            "operations": ["filter", "transform", "aggregate"],
        },
        "metadata": {"user": "admin", "department": "analytics"},
    }

    # Execute job through adapter (which uses legacy API internally)
    print("\nExecuting modern job through adapter...")
    result = adapter.run(modern_job)

    print("\nModern API Response:")
    print(json.dumps(result, indent=2))

    # Query job status
    print("\nQuerying job status...")
    status = adapter.query_status("job_2025_001")

    print("\nStatus Response:")
    print(json.dumps(status, indent=2))

    print("\n" + "=" * 70)
    print("Adapter successfully bridged legacy API to modern interface!")
    print("=" * 70)
