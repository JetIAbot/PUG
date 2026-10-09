from services.extraction_service import ExtractionService
from services.extraction_worker import ExtractionTask, ExtractionWorker
from services.job_store import PersistentJobStore
from services.registration_service import RegistrationService


class FakeStudentManager:
    def __init__(self, existing=None):
        self.existing = existing
        self.lookups = []

    def obtener_estudiante(self, matricola):
        self.lookups.append(matricola)
        return self.existing


class FakeScheduler:
    def __init__(self):
        self.calls = []

    def extraer_y_guardar_datos(self, matricola, password):
        self.calls.append((matricola, password))
        return {"success": True, "message": "ok", "data": {"matricola": matricola}}


def test_registration_rejects_duplicate_without_persisting_password():
    manager = FakeStudentManager(existing={"matricola": "171532"})
    service = RegistrationService(manager)

    result = service.prepare_extraction(
        {"matricola": "171532", "password": "PortalPass123"}
    )

    assert not result["valid"]
    assert "password" not in result
    assert manager.lookups == ["171532"]


def test_registration_prepares_credentials_only_for_extraction():
    manager = FakeStudentManager()
    service = RegistrationService(manager)

    result = service.prepare_extraction(
        {"matricola": "171532", "password": "PortalPass123"}
    )

    assert result["valid"]
    assert result["extraction"] == {
        "matricola": "171532",
        "password": "PortalPass123",
    }


def test_extraction_delegates_to_scheduler():
    scheduler = FakeScheduler()
    service = ExtractionService(scheduler)

    result = service.execute(" 171532 ", "PortalPass123")

    assert result["success"]
    assert scheduler.calls == [("171532", "PortalPass123")]


def test_extraction_rejects_missing_credentials_without_scheduler_call():
    scheduler = FakeScheduler()
    service = ExtractionService(scheduler)

    result = service.execute("", "")

    assert not result["success"]
    assert scheduler.calls == []


def test_extraction_worker_completes_job_without_persisting_password():
    scheduler = FakeScheduler()
    store = FakeJobStore()
    worker = ExtractionWorker(store, ExtractionService(scheduler))
    worker.start()
    worker.submit(ExtractionTask("job-1", "171532", "PortalPass123"))
    worker._queue.join()
    worker.stop()

    assert store.statuses == [("job-1", "processing"), ("job-1", "completed")]
    assert scheduler.calls == [("171532", "PortalPass123")]


class FakeJobStore:
    def __init__(self):
        self.statuses = []

    def mark_processing(self, job_id):
        self.statuses.append((job_id, "processing"))

    def mark_completed(self, job_id, message):
        self.statuses.append((job_id, "completed"))

    def mark_failed(self, job_id, message):
        self.statuses.append((job_id, "failed"))


def test_persistent_job_store_recovers_interrupted_jobs(tmp_path):
    path = tmp_path / "jobs.json"
    store = PersistentJobStore(path)
    job = store.create("171532")
    store.mark_processing(job["job_id"])

    recovered = PersistentJobStore(path)

    result = recovered.get(job["job_id"])
    assert result["status"] == "failed"
    assert "reiniciar" in result["message"]
