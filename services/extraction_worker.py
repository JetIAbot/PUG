"""Cola local y pool limitado para ejecutar extracciones fuera de Flask."""

from __future__ import annotations

from dataclasses import dataclass, field
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread
from typing import Any

from services.extraction_service import ExtractionService


@dataclass
class ExtractionTask:
    job_id: str
    matricola: str
    password: str
    carpool: dict[str, Any] = field(default_factory=dict)


class ExtractionWorker:
    """Consume extracciones con un número limitado de sesiones Selenium."""

    def __init__(
        self,
        job_store: Any,
        extraction_service: ExtractionService,
        on_completed: Any | None = None,
        timeout_seconds: float = 300,
        worker_count: int = 2,
        max_pending_jobs: int = 20,
    ) -> None:
        if worker_count < 1:
            raise ValueError("worker_count debe ser mayor que cero.")
        if max_pending_jobs < 1:
            raise ValueError("max_pending_jobs debe ser mayor que cero.")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds debe ser mayor que cero.")
        self.job_store = job_store
        self.extraction_service = extraction_service
        self.timeout_seconds = timeout_seconds
        self.on_completed = on_completed
        self.worker_count = worker_count
        self.max_pending_jobs = max_pending_jobs
        self._queue: Queue[ExtractionTask | None] = Queue(maxsize=max_pending_jobs)
        self._stop_event = Event()
        self._completion_lock = Lock()
        self._threads: list[Thread] = []

    def start(self) -> None:
        if any(thread.is_alive() for thread in self._threads):
            return
        self._stop_event.clear()
        self._threads = [
            Thread(
                target=self._run,
                name=f"pug-extraction-worker-{index}",
                daemon=True,
            )
            for index in range(1, self.worker_count + 1)
        ]
        for thread in self._threads:
            thread.start()

    def submit(self, task: ExtractionTask) -> bool:
        """Encola una tarea sin bloquear la petición HTTP si la cola está llena."""
        try:
            self._queue.put_nowait(task)
        except Full:
            return False
        return True

    def stop(self, timeout: float = 2) -> None:
        self._stop_event.set()
        alive_threads = [thread for thread in self._threads if thread.is_alive()]
        if not alive_threads:
            while True:
                try:
                    task = self._queue.get_nowait()
                except Empty:
                    break
                if task is not None:
                    task.password = ""
                self._queue.task_done()
            self._threads = []
            return
        for _ in alive_threads:
            self._queue.put(None)
        for thread in alive_threads:
            thread.join(timeout=timeout)
        self._threads = []

    def _run(self) -> None:
        while True:
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
            try:
                if self.on_completed is not None:
                    with self._completion_lock:
                        self.on_completed(task.matricola, task.carpool)
            except Exception:
                self.job_store.mark_failed(
                    task.job_id,
                    "La extracción terminó, pero no se pudieron guardar los datos de conducción.",
                )
                return
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
