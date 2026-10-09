"""Validación y preparación de solicitudes de registro de estudiantes."""

from __future__ import annotations

from typing import Any, Mapping

from utils.validators import FormValidator


class RegistrationService:
    """Orquesta la validación previa al registro sin guardar credenciales."""

    def __init__(self, student_manager: Any, validator: Any = FormValidator):
        self.student_manager = student_manager
        self.validator = validator

    def validate_submission(self, form_data: Mapping[str, Any]) -> dict[str, Any]:
        """Validar datos recibidos por la web o por otro adaptador."""
        data = dict(form_data)
        result = self.validator.validate_student_form(data)
        if not result["valid"]:
            return result

        matricola = result["cleaned_data"]["matricola"]
        if self.student_manager.obtener_estudiante(matricola) is not None:
            result["valid"] = False
            result["errors"]["matricola"] = [
                "Ya existe un estudiante con esa matrícula"
            ]

        return result

    def prepare_extraction(self, form_data: Mapping[str, Any]) -> dict[str, Any]:
        """Validar y devolver solo los datos necesarios para iniciar extracción.

        La contraseña se devuelve únicamente para que el coordinador de la
        solicitud la pase al worker; este servicio no la almacena ni la registra.
        """
        data = dict(form_data)
        result = self.validate_submission(data)
        if not result["valid"]:
            return result

        result["extraction"] = {
            "matricola": result["cleaned_data"]["matricola"],
            "password": str(data["password"]),
        }
        return result
