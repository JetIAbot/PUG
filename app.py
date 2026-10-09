"""Aplicación HTTP y cola local de extracciones de PUG."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from threading import Lock
from typing import Any, Protocol
from uuid import uuid4

from flask import Flask, jsonify, request

from services.registration_service import RegistrationService
from services.extraction_service import ExtractionService
from services.extraction_worker import ExtractionTask, ExtractionWorker
from services.job_store import PersistentJobStore


class JobStore(Protocol):
    def create(self, matricola: str) -> dict[str, Any] | None: ...
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

    def create(self, matricola: str) -> dict[str, Any] | None:
        with self._lock:
            if matricola in self._active_by_matricola:
                return None
            job_id = str(uuid4())
            job = {
                "job_id": job_id,
                "matricola": matricola,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._jobs[job_id] = job
            self._active_by_matricola.add(matricola)
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
    """Crear la aplicación Flask con dependencias sustituibles para pruebas."""
    app = Flask(__name__)
    registration_service = registration_service or _default_registration_service()
    store: JobStore = job_store or _default_job_store()
    job_store = store
    extraction_service = extraction_service or ExtractionService()
    extraction_worker = extraction_worker or ExtractionWorker(
        job_store,
        extraction_service,
    )
    extraction_worker.start()

    @app.get("/")
    def index():
        return jsonify(
            {
                "name": "PUG",
                "message": "API web activa",
                "extraction_worker": "running",
            }
        )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "pug-web"})

    @app.post("/students/register")
    def register_student():
        payload = request.get_json(silent=True)
        if payload is None:
            payload = request.form.to_dict()

        if not _consent_given(payload.get("consentimiento")):
            return jsonify(
                {
                    "success": False,
                    "errors": {
                        "consentimiento": [
                            "Debes aceptar el consentimiento para continuar."
                        ]
                    },
                }
            ), 400

        result = registration_service.prepare_extraction(payload)
        if not result["valid"]:
            return jsonify(
                {"success": False, "errors": result["errors"]}
            ), 400

        extraction = result["extraction"]
        try:
            job = job_store.create(extraction["matricola"])
            if job is None:
                return jsonify(
                    {
                        "success": False,
                        "errors": {
                            "matricola": [
                                "Ya existe una extracción pendiente para esta matrícula."
                            ]
                        },
                    }
                ), 409
            extraction_worker.submit(
                ExtractionTask(
                    job_id=job["job_id"],
                    matricola=extraction["matricola"],
                    password=extraction["password"],
                )
            )
            return jsonify(
                {
                    "success": True,
                    "job_id": job["job_id"],
                    "status": job["status"],
                    "message": "Solicitud recibida; la extracción se procesará en segundo plano.",
                }
            ), 202
        finally:
            # La contraseña ya fue transferida a la cola en memoria.
            extraction.clear()

    @app.get("/jobs/<job_id>")
    def get_job(job_id: str):
        job = job_store.get(job_id)
        if job is None:
            return jsonify({"success": False, "message": "Trabajo no encontrado."}), 404
        return jsonify({"success": True, "job": job})

    return app


def _default_registration_service() -> RegistrationService:
    from core.student_manager import StudentManager

    return RegistrationService(StudentManager())


def _default_job_store() -> PersistentJobStore:
    from config import Config

    path = os.getenv(
        "JOB_STORE_PATH",
        os.path.join(Config.DATOS_PATH, ".pug_jobs.json"),
    )
    return PersistentJobStore(path)


def _consent_given(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "si", "sí", "yes"}


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
