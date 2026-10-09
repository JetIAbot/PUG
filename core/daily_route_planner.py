"""
Planificador diario de rutas y generador PDF.

Agrupa estudiantes por hora de primera clase, calcula el regreso a partir
de la ultima clase, respeta reservas de carros particulares y prioriza
carros institucionales segun antiguedad y capacidad.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from utils.constants import BLOQUES_A_HORAS, ORDEN_BLOQUES


WEEKDAY_TO_IT = {
    0: "Lunedì",
    1: "Martedì",
    2: "Mercoledì",
    3: "Giovedì",
    4: "Venerdì",
}

BLOQUE_INDEX = {bloque: idx for idx, bloque in enumerate(ORDEN_BLOQUES)}


@dataclass
class StudentSchedule:
    matricola: str
    nombre: str
    apellido: str
    viaja_hoy: bool
    horario_dia: List[Dict[str, Any]]
    first_block: str
    last_block: str
    first_start: time
    first_departure: datetime
    last_end: time
    last_return_departure: datetime
    tipos_licencia: List[str]


class DailyRoutePlanner:
    """Planificador de rutas para un dia especifico."""

    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    def __init__(self, student_manager=None, car_manager=None):
        if student_manager is None:
            from core.student_manager import StudentManager
            student_manager = StudentManager()
        if car_manager is None:
            from core.car_manager import CarManager
            car_manager = CarManager()

        self.student_manager = student_manager
        self.car_manager = car_manager

    def generar_pdf_diario(self, fecha_str: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generar el plan y exportarlo a PDF."""
        plan = self.generar_plan_diario(fecha_str)
        if not plan.get("success"):
            return plan

        fecha_obj = date.fromisoformat(fecha_str)
        ruta_salida = Path(output_path) if output_path else self._ruta_pdf_por_defecto(fecha_obj)
        if not ruta_salida.is_absolute():
            ruta_salida = self.PROJECT_ROOT / ruta_salida
        ruta_salida.parent.mkdir(parents=True, exist_ok=True)
        self._exportar_pdf(plan["data"], ruta_salida)

        return {
            "success": True,
            "message": "PDF diario generado exitosamente",
            "path": str(ruta_salida),
            "data": plan["data"],
        }

    def generar_plan_diario(self, fecha_str: str) -> Dict[str, Any]:
        """Construir el plan diario sin exportar el PDF."""
        try:
            fecha_obj = date.fromisoformat(fecha_str)
        except ValueError:
            return {
                "success": False,
                "message": "Formato de fecha invalido",
                "errors": ["Usa YYYY-MM-DD"],
            }

        dia_it = WEEKDAY_TO_IT.get(fecha_obj.weekday())
        if not dia_it:
            return {
                "success": False,
                "message": "La fecha elegida cae en fin de semana",
                "errors": ["No se generan rutas sabado/domingo"],
            }

        estudiantes_raw = self.student_manager.listar_estudiantes()
        carros_raw = self.car_manager.obtener_todos_carros()

        estudiantes = self._construir_estudiantes_del_dia(estudiantes_raw, fecha_obj, dia_it)
        if not estudiantes:
            return {
                "success": False,
                "message": f"No hay estudiantes con clases el {dia_it}",
                "errors": ["Sin estudiantes para planificar"],
            }

        carros = [self._normalizar_carro(c) for c in carros_raw]
        if not carros:
            return {
                "success": False,
                "message": "No hay carros registrados",
                "errors": ["Sin carros"],
            }

        particulares = [c for c in carros if c.get("pertenencia") == "particular"]
        institucionales = [c for c in carros if c.get("pertenencia") != "particular"]

        asignaciones: List[Dict[str, Any]] = []
        estudiantes_reservados = set()

        # 1) Reservas de carros particulares.
        for carro in particulares:
            reservas = self._reservas_para_dia(carro, dia_it)
            if not reservas:
                continue
            for reserva in reservas:
                matriculas = [m for m in reserva.get("estudiantes", []) if m in estudiantes]
                if not matriculas:
                    continue
                for m in matriculas:
                    estudiantes_reservados.add(m)

                grupo = [estudiantes[m] for m in matriculas]
                asignacion = self._crear_asignacion_grupo(
                    fecha_obj=fecha_obj,
                    dia_it=dia_it,
                    estudiantes_grupo=grupo,
                    carro=carro,
                    conductor_matricola=reserva.get("conductor_matricola") or None,
                    tipo="particular",
                    criterio="reserva_particular",
                )
                if asignacion:
                    asignaciones.append(asignacion)

        # 2) Agrupacion de estudiantes restantes por hora de primera clase.
        estudiantes_restantes = [e for m, e in estudiantes.items() if m not in estudiantes_reservados]
        clusters = self._agrupar_por_hora(estudiantes_restantes, clave="first_departure", tolerancia_minutos=30)
        carros_libres = sorted(
            institucionales,
            key=lambda c: (c.get("año", 9999), -int(c.get("capacidad_pasajeros", 0)), c.get("placa", "")),
        )

        for cluster in clusters:
            pendientes = cluster[:]
            while pendientes and carros_libres:
                carro = carros_libres.pop(0)
                capacidad = max(1, int(carro.get("capacidad_pasajeros", 1)))
                grupo = pendientes[:capacidad]

                conductor = self._seleccionar_conductor(grupo, carro)
                if not conductor:
                    conductor = self._seleccionar_conductor(pendientes, carro)
                    if not conductor:
                        break
                    if conductor in grupo:
                        pass
                    else:
                        grupo = [conductor] + grupo[: max(0, capacidad - 1)]

                asignacion = self._crear_asignacion_grupo(
                    fecha_obj=fecha_obj,
                    dia_it=dia_it,
                    estudiantes_grupo=grupo,
                    carro=carro,
                    conductor_matricola=conductor["matricola"],
                    tipo="institucional",
                    criterio="primera_clase",
                )
                if asignacion:
                    asignaciones.append(asignacion)

                usados = {e["matricola"] for e in grupo}
                pendientes = [e for e in pendientes if e["matricola"] not in usados]

        asignados = {e["matricola"] for a in asignaciones for e in a.get("estudiantes", [])}
        sin_asignar = [
            {
                "matricola": e["matricola"],
                "nombre": e["nombre"],
                "apellido": e["apellido"],
                "first_departure": e["first_departure"].strftime("%H:%M"),
                "last_departure": e["last_return_departure"].strftime("%H:%M"),
            }
            for e in estudiantes.values()
            if e["matricola"] not in asignados
        ]

        plan = {
            "fecha": fecha_obj.isoformat(),
            "dia_it": dia_it,
            "asignaciones": asignaciones,
            "estudiantes": estudiantes,
            "sin_asignar": sin_asignar,
            "resumen": {
                "total_estudiantes": len(estudiantes),
                "total_asignados": len(asignados),
                "total_sin_asignar": len(sin_asignar),
                "total_carros_usados": len({a["carro"]["placa"] for a in asignaciones}),
                "total_institucionales": len([a for a in asignaciones if a["tipo"] == "institucional"]),
                "total_particulares": len([a for a in asignaciones if a["tipo"] == "particular"]),
            },
        }

        return {
            "success": True,
            "message": "Plan diario generado",
            "data": plan,
        }

    def _construir_estudiantes_del_dia(self, estudiantes_raw: List[Dict[str, Any]], fecha_obj: date, dia_it: str) -> Dict[str, Dict[str, Any]]:
        estudiantes: Dict[str, Dict[str, Any]] = {}
        for estudiante in estudiantes_raw:
            d = estudiante if isinstance(estudiante, dict) else estudiante.to_dict()
            horario = d.get("horario", d.get("clases", [])) or []
            clases_dia = [c for c in horario if c.get("dia") == dia_it and c.get("bloque") in BLOQUE_INDEX]
            if not clases_dia:
                continue

            clases_dia = sorted(clases_dia, key=lambda c: BLOQUE_INDEX.get(c.get("bloque", ""), 999))
            first_block = clases_dia[0]["bloque"]
            last_block = clases_dia[-1]["bloque"]
            first_start, first_end = self._parse_bloque(first_block)
            last_start, last_end = self._parse_bloque(last_block)
            if first_start is None or last_end is None:
                continue

            first_departure = datetime.combine(fecha_obj, first_start) - timedelta(minutes=90)
            last_return_departure = datetime.combine(fecha_obj, last_end) + timedelta(minutes=15)

            matricola = d.get("matricola")
            if not matricola:
                continue

            estudiantes[matricola] = {
                "matricola": matricola,
                "nombre": d.get("nombre", d.get("nome", "")),
                "apellido": d.get("apellido", d.get("cognome", "")),
                "viaja_hoy": d.get("viaja_hoy", False),
                "horario_dia": clases_dia,
                "first_block": first_block,
                "last_block": last_block,
                "first_start": first_start,
                "first_end": first_end,
                "first_departure": first_departure,
                "last_start": last_start,
                "last_end": last_end,
                "last_return_departure": last_return_departure,
                "tipos_licencia": [str(t).upper() for t in d.get("tipos_licencia", [])],
            }
        return estudiantes

    def _reservas_para_dia(self, carro: Dict[str, Any], dia_it: str) -> List[Dict[str, Any]]:
        reservas = []
        for reserva in carro.get("viajes_particulares", []) or []:
            if str(reserva.get("dia", "")).strip() == dia_it:
                reservas.append(reserva)
        return reservas

    def _agrupar_por_hora(self, estudiantes: List[Dict[str, Any]], clave: str, tolerancia_minutos: int) -> List[List[Dict[str, Any]]]:
        ordenados = sorted(estudiantes, key=lambda e: e[clave])
        clusters: List[List[Dict[str, Any]]] = []
        cluster_actual: List[Dict[str, Any]] = []
        base: Optional[datetime] = None

        for estudiante in ordenados:
            hora = estudiante[clave]
            if base is None:
                cluster_actual = [estudiante]
                base = hora
                continue

            if abs((hora - base).total_seconds()) <= tolerancia_minutos * 60:
                cluster_actual.append(estudiante)
            else:
                clusters.append(cluster_actual)
                cluster_actual = [estudiante]
                base = hora

        if cluster_actual:
            clusters.append(cluster_actual)

        return clusters

    def _crear_asignacion_grupo(
        self,
        fecha_obj: date,
        dia_it: str,
        estudiantes_grupo: List[Dict[str, Any]],
        carro: Dict[str, Any],
        conductor_matricola: Optional[str],
        tipo: str,
        criterio: str,
    ) -> Optional[Dict[str, Any]]:
        if not estudiantes_grupo:
            return None

        estudiantes_grupo = sorted(estudiantes_grupo, key=lambda e: e["first_departure"])

        conductor = None
        if conductor_matricola:
            conductor = next((e for e in estudiantes_grupo if e["matricola"] == conductor_matricola), None)
            if conductor is not None and not self._puede_conducir_carro(conductor, carro):
                conductor = None

        if conductor is None:
            conductor = self._seleccionar_conductor(estudiantes_grupo, carro)

        if conductor is None:
            return None

        pasajeros = [e for e in estudiantes_grupo if e["matricola"] != conductor["matricola"]]
        capacidad_maxima = max(1, int(carro.get("capacidad_pasajeros", 1)))
        pasajeros = pasajeros[: max(0, capacidad_maxima - 1)]

        ida_hora = estudiantes_grupo[0]["first_departure"].strftime("%H:%M")
        vuelta_hora = max(e["last_return_departure"] for e in estudiantes_grupo).strftime("%H:%M")

        return {
            "fecha": fecha_obj.isoformat(),
            "dia_it": dia_it,
            "tipo": tipo,
            "criterio": criterio,
            "carro": carro,
            "conductor": conductor,
            "estudiantes": [conductor] + pasajeros,
            "pasajeros": pasajeros,
            "ida": {
                "hora_salida": ida_hora,
                "origen": "Punto de partida",
                "destino": "Universidad Gregoriana",
                "hora_referencia": estudiantes_grupo[0]["first_start"].strftime("%H:%M"),
            },
            "vuelta": {
                "hora_salida": vuelta_hora,
                "origen": "Universidad Gregoriana",
                "destino": "Punto de partida",
                "hora_referencia": max(e["last_end"] for e in estudiantes_grupo).strftime("%H:%M"),
            },
        }

    def _seleccionar_conductor(self, estudiantes: List[Dict[str, Any]], carro: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        candidatos = [e for e in estudiantes if self._puede_conducir_carro(e, carro)]
        if not candidatos:
            return None
        candidatos.sort(key=lambda e: (-len(e.get("tipos_licencia", [])), e["matricola"]))
        return candidatos[0]

    def _puede_conducir_carro(self, conductor_data: Dict[str, Any], carro_data: Dict[str, Any]) -> bool:
        tipos_licencia = [str(t).upper() for t in conductor_data.get("tipos_licencia", [])]
        if not tipos_licencia:
            return False

        requeridas = carro_data.get("licencias_requeridas") or []
        if requeridas:
            return any(lic in requeridas for lic in tipos_licencia)

        tipo_carro = carro_data.get("tipo_carro")
        compatibilidad = {
            "mini": ["B", "C1", "C", "D1", "D"],
            "compacto": ["B", "C1", "C", "D1", "D"],
            "familiar": ["B", "C1", "C", "D1", "D"],
            "furgoneta": ["C1", "C", "D1", "D"],
            "microbus": ["D1", "D"],
        }
        licencias_requeridas = compatibilidad.get(tipo_carro, ["B"])
        return any(lic in tipos_licencia for lic in licencias_requeridas)

    def _normalizar_carro(self, carro: Any) -> Dict[str, Any]:
        d = carro if isinstance(carro, dict) else carro.to_dict()
        d = dict(d)
        d["placa"] = str(d.get("placa", "")).upper()
        d["pertenencia"] = str(d.get("pertenencia", "institucional")).lower()
        d["licencias_requeridas"] = [str(x).upper() for x in d.get("licencias_requeridas", [])]
        d["viajes_particulares"] = d.get("viajes_particulares", []) or []
        return d

    def _parse_bloque(self, bloque: str) -> Tuple[Optional[time], Optional[time]]:
        rango = BLOQUES_A_HORAS.get(bloque)
        if not rango:
            return None, None
        inicio, fin = [p.strip() for p in rango.split("-")]
        return (
            datetime.strptime(inicio, "%H:%M").time(),
            datetime.strptime(fin, "%H:%M").time(),
        )

    def _ruta_pdf_por_defecto(self, fecha_obj: date) -> Path:
        return self.PROJECT_ROOT / "reportes" / "rutas_diarias" / f"rutas_{fecha_obj.strftime('%Y%m%d')}.pdf"

    def _exportar_pdf(self, plan: Dict[str, Any], output_path: Path):
        estilos = getSampleStyleSheet()
        estilos.add(ParagraphStyle(name="Small", parent=estilos["BodyText"], fontSize=8, leading=10))
        estilos.add(ParagraphStyle(name="Tiny", parent=estilos["BodyText"], fontSize=7, leading=8))
        estilos.add(ParagraphStyle(
            name="TableText",
            parent=estilos["BodyText"],
            fontSize=7,
            leading=8,
            alignment=1,
        ))
        estilos.add(ParagraphStyle(
            name="TableTextLeft",
            parent=estilos["BodyText"],
            fontSize=7,
            leading=8,
        ))

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )

        story = []
        story.append(Paragraph("Lista de vehículos para el viaje", estilos["Title"]))
        story.append(Paragraph(
            f"{escape(plan['dia_it'])} · {escape(plan['fecha'])}",
            estilos["Heading3"],
        ))
        story.append(Spacer(1, 8))

        resumen = plan["resumen"]
        assignments = plan["asignaciones"]
        return_times = [
            a.get("vuelta", {}).get("hora_salida", "")
            for a in assignments
            if a.get("vuelta", {}).get("hora_salida")
        ]
        return_time = max(return_times) if return_times else "—"

        metadata = [
            [
                Paragraph("<b>Fecha del viaje</b>", estilos["TableTextLeft"]),
                Paragraph(escape(plan["fecha"]), estilos["TableTextLeft"]),
                Paragraph("<b>Destino</b>", estilos["TableTextLeft"]),
                Paragraph("Universidad Gregoriana", estilos["TableTextLeft"]),
            ],
            [
                Paragraph("<b>Hora de regreso</b>", estilos["TableTextLeft"]),
                Paragraph(escape(return_time), estilos["TableTextLeft"]),
                Paragraph("<b>Estudiantes</b>", estilos["TableTextLeft"]),
                Paragraph(
                    f"{resumen['total_asignados']} asignados / "
                    f"{resumen['total_sin_asignar']} sin asignar",
                    estilos["TableTextLeft"],
                ),
            ],
        ]
        tabla_metadata = Table(metadata, colWidths=[95, 120, 75, 245])
        tabla_metadata.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#D9EAF7")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#D9EAF7")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#8EA9C1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tabla_metadata)
        story.append(Spacer(1, 12))

        headers = [
            "Auto",
            "Placa",
            "Conductor",
            "Componentes",
            "Salida ida",
            "Clase ida",
            "Salida vuelta",
            "Clase termina",
        ]
        rows = [[Paragraph(f"<b>{escape(header)}</b>", estilos["TableText"]) for header in headers]]
        for idx, asignacion in enumerate(plan["asignaciones"], 1):
            estudiantes = asignacion.get("estudiantes", [])
            componentes_txt = "<br/>".join(
                f"{escape(str(e.get('matricola', '')))} - "
                f"{escape(str(e.get('nombre', '')))} {escape(str(e.get('apellido', '')))}"
                for e in estudiantes
            )
            carro = asignacion.get("carro", {})
            conductor = asignacion.get("conductor", {})
            ida = asignacion.get("ida", {})
            vuelta = asignacion.get("vuelta", {})
            auto = f"G{idx:02d} · {carro.get('marca', '')} {carro.get('modelo', '')}"
            conductor_txt = (
                f"{conductor.get('nombre', '')} {conductor.get('apellido', '')}<br/>"
                f"{conductor.get('matricola', '')}"
            )
            rows.append([
                Paragraph(escape(auto), estilos["TableTextLeft"]),
                Paragraph(escape(str(carro.get("placa", ""))), estilos["TableText"]),
                Paragraph(conductor_txt, estilos["TableTextLeft"]),
                Paragraph(componentes_txt, estilos["TableTextLeft"]),
                Paragraph(escape(str(ida.get("hora_salida", ""))), estilos["TableText"]),
                Paragraph(escape(str(ida.get("hora_referencia", ""))), estilos["TableText"]),
                Paragraph(escape(str(vuelta.get("hora_salida", ""))), estilos["TableText"]),
                Paragraph(escape(str(vuelta.get("hora_referencia", ""))), estilos["TableText"]),
            ])

        tabla = Table(
            rows,
            colWidths=[78, 48, 85, 145, 48, 48, 55, 56],
            repeatRows=1,
        )
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B0B0B0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (4, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#F8FBFF")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(Paragraph("<b>Vehículos y componentes</b>", estilos["Heading2"]))
        story.append(tabla)
        story.append(Spacer(1, 10))

        if plan["sin_asignar"]:
            story.append(Paragraph("<b>Componentes sin asignar</b>", estilos["Heading2"]))
            sin_asignar_rows = [[
                Paragraph("<b>Matrícula</b>", estilos["TableText"]),
                Paragraph("<b>Nombre</b>", estilos["TableText"]),
                Paragraph("<b>Salida prevista</b>", estilos["TableText"]),
                Paragraph("<b>Regreso previsto</b>", estilos["TableText"]),
            ]]
            for e in plan["sin_asignar"]:
                sin_asignar_rows.append([
                    Paragraph(escape(str(e["matricola"])), estilos["TableText"]),
                    Paragraph(escape(f"{e['nombre']} {e['apellido']}"), estilos["TableTextLeft"]),
                    Paragraph(escape(str(e["first_departure"])), estilos["TableText"]),
                    Paragraph(escape(str(e["last_departure"])), estilos["TableText"]),
                ])
            tabla_sin = Table(sin_asignar_rows, colWidths=[70, 220, 90, 90], repeatRows=1)
            tabla_sin.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7A1F1F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B0B0B0")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFF5F5"), colors.white]),
            ]))
            story.append(tabla_sin)

        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "Salida ida = 90 minutos antes de la primera clase del grupo. "
            "Salida vuelta = 15 minutos después de la última clase. "
            "Clase ida y Clase termina son las horas académicas de referencia.",
            estilos["Small"],
        ))

        doc.build(story)
