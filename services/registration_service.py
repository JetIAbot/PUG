"""Validación y preparación de solicitudes de registro de estudiantes."""

from __future__ import annotations

from typing import Any, Mapping

from utils.validators import DataValidator, FormValidator


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

    def prepare_refresh(self, form_data: Mapping[str, Any]) -> dict[str, Any]:
        """Preparar una actualización para una matrícula ya registrada."""
        data = dict(form_data)
        result = self.validator.validate_student_form(data)
        if not result["valid"]:
            return result
        matricola = result["cleaned_data"]["matricola"]
        if self.student_manager.obtener_estudiante(matricola) is None:
            result["valid"] = False
            result["errors"]["matricola"] = [
                "No existe un estudiante registrado con esa matrícula."
            ]
            return result
        try:
            result["extraction"] = self._extraction_data(data, matricola)
        except ValueError as exc:
            result["valid"] = False
            result["errors"]["license"] = [str(exc)]
        return result

    def prepare_extraction(self, form_data: Mapping[str, Any]) -> dict[str, Any]:
        data = dict(form_data)
        result = self.validate_submission(data)
        if not result["valid"]:
            return result
        try:
            result["extraction"] = self._extraction_data(
                data, result["cleaned_data"]["matricola"]
            )
        except ValueError as exc:
            result["valid"] = False
            result["errors"]["license"] = [str(exc)]
        return result

    def _extraction_data(self, data: dict[str, Any], matricola: str) -> dict[str, Any]:
        has_license = data.get("tiene_licencia") in (True, "true", "1", 1)
        license_types = data.get("tipos_licencia", [])
        if isinstance(license_types, str):
            license_types = [license_types]
        license_types = [str(value).upper() for value in license_types]
        expiry = data.get("fecha_vencimiento_licencia") or None
        errors: list[str] = []
        if has_license:
            valid_types = {"A1", "A2", "A", "B", "C1", "C", "D1", "D", "BE", "CE", "DE"}
            if not license_types or not set(license_types).issubset(valid_types):
                errors.append("Selecciona al menos un tipo de licencia válido.")
            if not expiry:
                errors.append("Indica la fecha de vencimiento de la licencia.")
            else:
                validation = DataValidator.validate_license_data(license_types[0], expiry)
                errors.extend(validation["errors"])
        if errors:
            raise ValueError("; ".join(errors))
        return {
            "matricola": matricola,
            "password": str(data["password"]),
            "carpool": {
                "tiene_licencia": has_license,
                "tipos_licencia": license_types if has_license else [],
                "fecha_vencimiento_licencia": expiry if has_license else None,
            },
        }

    def update_carpool_data(self, matricola: str, data: dict[str, Any]) -> None:
        """Guardar los datos de conducción tras una extracción exitosa."""
        result = self.student_manager.actualizar_estudiante(matricola, data)
        if not result.get("success"):
            raise RuntimeError(result.get("message", "No se pudieron guardar los datos de conducción."))
