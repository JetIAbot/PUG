"""Persistencia de estados de trabajos sin almacenar credenciales."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4


class PersistentJobStore:
    """Almacena únicamente metadatos y estados de trabajos en JSON."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self._lock = Lock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._active_by_matricola: set[str] = set()
        self._load()
        self._recover_interrupted()

    def create(
        self, matricola: str, cooldown_seconds: int = 0
    ) -> dict[str, Any] | None:
        with self._lock:
            if matricola in self._active_by_matricola:
                return None
            if cooldown_seconds > 0:
                now = datetime.now(timezone.utc)
                for job in self._jobs.values():
                    if job.get("matricola") != matricola:
                        continue
                    created = datetime.fromisoformat(job["created_at"])
                    if (now - created).total_seconds() < cooldown_seconds:
                        return None
            job = {
                "job_id": str(uuid4()),
                "matricola": matricola,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._jobs[job["job_id"]] = job
            self._active_by_matricola.add(matricola)
            self._save()
            return job.copy()

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return job.copy() if job else None

    def mark_processing(self, job_id: str) -> None:
        self._update(job_id, status="processing")

    def mark_completed(self, job_id: str, message: str) -> None:
        self._finish(job_id, "completed", message)

    def mark_failed(self, job_id: str, message: str) -> None:
        self._finish(job_id, "failed", message)

    def _update(self, job_id: str, **values: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.update(values)
                self._save()

    def _finish(self, job_id: str, status: str, message: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job.update(
                status=status,
                message=message,
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
            self._active_by_matricola.discard(job["matricola"])
            self._save()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"No se pudo leer el almacén de trabajos: {self.path}") from exc
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise RuntimeError(f"Formato inválido del almacén de trabajos: {self.path}")
        for job in data["jobs"]:
            if isinstance(job, dict) and isinstance(job.get("job_id"), str):
                self._jobs[job["job_id"]] = job
                if job.get("status") in {"pending", "processing"}:
                    self._active_by_matricola.add(job["matricola"])

    def _recover_interrupted(self) -> None:
        interrupted = [
            job for job in self._jobs.values()
            if job.get("status") in {"pending", "processing"}
        ]
        if not interrupted:
            return
        for job in interrupted:
            job.update(
                status="failed",
                message="Trabajo interrumpido al reiniciar la aplicación.",
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
            self._active_by_matricola.discard(job["matricola"])
        self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        payload = {"jobs": list(self._jobs.values())}
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)
