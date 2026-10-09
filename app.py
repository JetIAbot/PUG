"""Aplicación HTTP y cola local de extracciones de PUG."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from threading import Lock
from typing import Any, Protocol
from uuid import uuid4

from flask import Flask, jsonify, render_template, request

from services.extraction_service import ExtractionService
from services.extraction_worker import ExtractionTask, ExtractionWorker
from services.job_store import PersistentJobStore
from services.registration_service import RegistrationService


class JobStore(Protocol):
    def create(self, matricola: str, cooldown_seconds: int = 0) -> dict[str, Any] | None: ...
    def get(self, job_id: str) -> dict[str, Any] | None: ...
    def mark_processing(self, job_id: str) -> None: ...
    def mark_completed(self, job_id: str, message: str) -> None: ...
    def mark_failed(self, job_id: str, message: str) -> None: ...


class InMemoryJobStore:
    """Registro temporal de trabajos; no almacena credenciales del portal."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._active_by_matricola: set[str] = set()
        self._lock = Lock()

    def create(self, matricola: str, cooldown_seconds: int = 0) -> dict[str, Any] | None:
        with self._lock:
            if matricola in self._active_by_matricola or self._recent(matricola, cooldown_seconds):
                return None
            job = {
                "job_id": str(uuid4()),
                "matricola": matricola,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._jobs[job["job_id"]] = job
            self._active_by_matricola.add(matricola)
            return job.copy()

    def _recent(self, matricola: str, cooldown_seconds: int) -> bool:
        if cooldown_seconds <= 0:
            return False
        now = datetime.now(timezone.utc)
        return any(
            job["matricola"] == matricola
            and (now - datetime.fromisoformat(job["created_at"])).total_seconds()
            < cooldown_seconds
            for job in self._jobs.values()
        )

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
            if (job := self._jobs.get(job_id)) is not None:
                job.update(values)

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


def create_app(
    registration_service: RegistrationService | None = None,
    job_store: JobStore | None = None,
    extraction_service: ExtractionService | None = None,
    extraction_worker: ExtractionWorker | None = None,
) -> Flask:
    app = Flask(__name__)
    registration_service = registration_service or _default_registration_service()
    store: JobStore = job_store or _default_job_store()
    extraction_service = extraction_service or ExtractionService()
    worker = extraction_worker or ExtractionWorker(
        store,
        extraction_service,
        on_completed=registration_service.update_carpool_data,
        timeout_seconds=_extraction_timeout_seconds(),
        worker_count=_extraction_worker_count(),
        max_pending_jobs=_max_pending_jobs(),
    )
    worker.start()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api")
    def api_info():
        return jsonify({"name": "PUG", "message": "API web activa",
                        "extraction_worker": "running"})

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "pug-web"})

    @app.post("/students/register")
    def register_student():
        return _submit_extraction(request, registration_service, store, worker, False)

    @app.post("/students/refresh")
    def refresh_student():
        return _submit_extraction(request, registration_service, store, worker, True)

    @app.get("/jobs/<job_id>")
    def get_job(job_id: str):
        job = store.get(job_id)
        if job is None:
            return jsonify({"success": False, "message": "Trabajo no encontrado."}), 404
        return jsonify({"success": True, "job": job})

    return app


def _submit_extraction(
    http_request: Any,
    registration_service: RegistrationService,
    store: JobStore,
    worker: ExtractionWorker,
    allow_existing: bool,
):
    payload = http_request.get_json(silent=True) or http_request.form.to_dict()
    if not _consent_given(payload.get("consentimiento")):
        return jsonify({"success": False, "errors": {"consentimiento": [
            "Debes aceptar el consentimiento para continuar."
        ]}}), 400

    prepare = (registration_service.prepare_refresh if allow_existing
               else registration_service.prepare_extraction)
    result = prepare(payload)
    if not result["valid"]:
        return jsonify({"success": False, "errors": result["errors"]}), 400

    extraction = result["extraction"]
    try:
        job = store.create(
            extraction["matricola"],
            _refresh_cooldown_seconds() if allow_existing else 0,
        )
        if job is None:
            return jsonify({
                "success": False,
                "message": (
                    "La matrícula está temporalmente bloqueada o ya tiene "
                    "una extracción en curso."
                ),
            }), 429 if allow_existing else 409
        accepted = worker.submit(ExtractionTask(
            job_id=job["job_id"],
            matricola=extraction["matricola"],
            password=extraction["password"],
            carpool=extraction["carpool"],
        ))
        if not accepted:
            store.mark_failed(
                job["job_id"],
                "La cola de extracciones está temporalmente llena.",
            )
            return jsonify({
                "success": False,
                "message": "La cola de extracciones está temporalmente llena.",
            }), 429
        return jsonify({
            "success": True, "job_id": job["job_id"], "status": job["status"],
            "message": "Solicitud recibida; la extracción se procesará en segundo plano.",
        }), 202
    finally:
        extraction.clear()


def _default_registration_service() -> RegistrationService:
    from core.student_manager import StudentManager
    return RegistrationService(StudentManager())


def _default_job_store() -> PersistentJobStore:
    from config import Config
    return PersistentJobStore(os.getenv(
        "JOB_STORE_PATH", os.path.join(Config.DATOS_PATH, ".pug_jobs.json")
    ))


def _refresh_cooldown_seconds() -> int:
    try:
        return max(0, int(os.getenv("REFRESH_COOLDOWN_SECONDS", "900")))
    except ValueError:
        return 900


def _positive_int_env(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def _extraction_timeout_seconds() -> float:
    try:
        return max(1.0, float(os.getenv("EXTRACTION_TIMEOUT_SECONDS", "300")))
    except ValueError:
        return 300.0


def _extraction_worker_count() -> int:
    return _positive_int_env("EXTRACTION_WORKERS", 2)


def _max_pending_jobs() -> int:
    return _positive_int_env("MAX_PENDING_JOBS", 20)


def _consent_given(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "si", "sí", "yes"}


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
