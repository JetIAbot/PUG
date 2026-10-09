from app import InMemoryJobStore, create_app
from services.extraction_service import ExtractionService
from services.registration_service import RegistrationService


class FakeStudentManager:
    def __init__(self, existing=None):
        self.existing = existing

    def obtener_estudiante(self, matricola):
        return self.existing


class FakeScheduler:
    def extraer_y_guardar_datos(self, matricola, password):
        return {"success": True, "message": "ok", "data": None}


def make_client():
    service = RegistrationService(FakeStudentManager())
    extraction = ExtractionService(FakeScheduler())
    return create_app(service, InMemoryJobStore(), extraction).test_client()


def test_health_endpoint():
    response = make_client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "service": "pug-web"}


def test_register_requires_consent():
    response = make_client().post(
        "/students/register",
        json={"matricola": "171532", "password": "PortalPass123"},
    )

    assert response.status_code == 400
    assert "consentimiento" in response.get_json()["errors"]


def test_register_creates_pending_job_without_returning_password():
    client = make_client()
    response = client.post(
        "/students/register",
        json={
            "matricola": "171532",
            "password": "PortalPass123",
            "consentimiento": True,
        },
    )

    body = response.get_json()
    assert response.status_code == 202
    assert body["status"] == "pending"
    assert "password" not in str(body).lower()

    job_response = client.get(f"/jobs/{body['job_id']}")
    job_body = job_response.get_json()
    assert job_response.status_code == 200
    assert job_body["job"]["matricola"] == "171532"
    assert "password" not in str(job_body).lower()


def test_register_rejects_duplicate_pending_job():
    client = make_client()
    payload = {
        "matricola": "171532",
        "password": "PortalPass123",
        "consentimiento": True,
    }

    assert client.post("/students/register", json=payload).status_code == 202
    assert client.post("/students/register", json=payload).status_code == 409


def test_refresh_accepts_existing_student_and_blocks_repeated_request(monkeypatch):
    service = RegistrationService(FakeStudentManager(existing={"matricola": "171532"}))
    extraction = ExtractionService(FakeScheduler())
    client = create_app(service, InMemoryJobStore(), extraction).test_client()
    monkeypatch.setenv("REFRESH_COOLDOWN_SECONDS", "900")
    payload = {
        "matricola": "171532",
        "password": "PortalPass123",
        "consentimiento": True,
    }

    first = client.post("/students/refresh", json=payload)
    second = client.post("/students/refresh", json=payload)

    assert first.status_code == 202
    assert second.status_code == 429
    assert "password" not in str(second.get_json()).lower()


def test_refresh_rejects_unknown_student():
    client = make_client()

    response = client.post("/students/refresh", json={
        "matricola": "171532",
        "password": "PortalPass123",
        "consentimiento": True,
    })

    assert response.status_code == 400
    assert "matricola" in response.get_json()["errors"]
