"""Cola local y worker único para ejecutar extracciones fuera de Flask."""

from __future__ import annotations

from dataclasses import dataclass
from queue import Queue
from threading import Event, Thread
from typing import Any

from services.extraction_service import ExtractionService


@dataclass
class ExtractionTask:
    job_id: str
    matricola: str
    password: str


class ExtractionWorker:
    """Consume extracciones en orden, manteniendo una sola sesión Selenium."""

    def __init__(
        self,
        job_store: Any,
        extraction_service: ExtractionService,
        timeout_seconds: float = 300,
    ) -> None:
        self.job_store = job_store
        self.extraction_service = extraction_service
        self.timeout_seconds = timeout_seconds
        self._queue: Queue[ExtractionTask | None] = Queue()
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(
            target=self._run,
            name="pug-extraction-worker",
            daemon=True,
        )
        self._thread.start()

    def submit(self, task: ExtractionTask) -> None:
        self._queue.put(task)

    def stop(self, timeout: float = 2) -> None:
        self._stop_event.set()
        self._queue.put(None)
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            task = self._queue.get()
            try:
                if task is None:
                    return
                self._process(task)
            finally:
                if task is not None:
                    task.password = ""
                self._queue.task_done()

    def _process(self, task: ExtractionTask) -> None:
        self.job_store.mark_processing(task.job_id)
        result: dict[str, Any] | None = None
        error: dict[str, Any] = {}
        operation = Thread(
            target=self._execute,
            args=(task, error),
            name=f"pug-extraction-{task.job_id}",
            daemon=True,
        )
        operation.start()
        operation.join(timeout=self.timeout_seconds)

        if operation.is_alive():
            self.job_store.mark_failed(
                task.job_id,
                "La extracción superó el tiempo máximo permitido.",
            )
            # No se inicia otra extracción mientras la anterior siga usando Selenium.
            operation.join()
            return

        result = error.pop("result", None)
        if result is not None and result.get("success"):
            self.job_store.mark_completed(task.job_id, "Extracción completada.")
        else:
            self.job_store.mark_failed(
                task.job_id,
                (result or {}).get("message", "No se pudo completar la extracción."),
            )

    def _execute(self, task: ExtractionTask, error: dict[str, Any]) -> None:
        error["result"] = self.extraction_service.execute(
            task.matricola,
            task.password,
        )
