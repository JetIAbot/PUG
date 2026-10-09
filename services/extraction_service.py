"""Servicio de aplicación para extraer y guardar horarios del portal."""

from __future__ import annotations

import logging
from typing import Any

from core.student_scheduler import StudentScheduler

logger = logging.getLogger(__name__)


class ExtractionService:
    """Aísla el scheduler del adaptador web o de la cola de trabajos."""

    def __init__(self, scheduler: Any | None = None):
        self.scheduler = scheduler or StudentScheduler()

    def execute(self, matricola: str, password: str) -> dict[str, Any]:
        """Ejecutar una extracción sin persistir ni registrar la contraseña."""
        matricola = matricola.strip()
        if not matricola:
            return {
                "success": False,
                "message": "La matrícula es obligatoria",
                "data": None,
            }
        if not password:
            return {
                "success": False,
                "message": "La contraseña es obligatoria",
                "data": None,
            }

        try:
            return self.scheduler.extraer_y_guardar_datos(matricola, password)
        except Exception:
            logger.exception(
                "Error no controlado durante la extracción para matrícula %s****",
                matricola[:2],
            )
            return {
                "success": False,
                "message": "No se pudo completar la extracción.",
                "data": None,
            }
