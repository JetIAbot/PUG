"""
ObsidianManager - Base de datos local con archivos Markdown estilo Obsidian
Reemplaza FirebaseManager — cada documento es un archivo .md con frontmatter YAML

Estructura en disco:
    datos/
        estudiantes/
            172934.md
        carros/
            ABC123.md
        viajes/
            viaje_001.md
        listas_diarias/
            2026-03-10.md
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import yaml

logger = logging.getLogger(__name__)

# Sentinel que se resuelve a datetime.now() al escribir
SERVER_TIMESTAMP = "__SERVER_TIMESTAMP__"


# ──────────────────────────────────────────────
#  Utilidades de lectura / escritura Markdown
# ──────────────────────────────────────────────

def _resolve_timestamps(data: dict) -> dict:
    """Reemplazar SERVER_TIMESTAMP con la fecha/hora actual."""
    now = datetime.now().isoformat()
    resolved = {}
    for k, v in data.items():
        if v is SERVER_TIMESTAMP or v == SERVER_TIMESTAMP:
            resolved[k] = now
        elif isinstance(v, dict):
            resolved[k] = _resolve_timestamps(v)
        elif isinstance(v, list):
            resolved[k] = [
                _resolve_timestamps(item) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            resolved[k] = v
    return resolved


def _read_frontmatter(path: Path) -> Optional[dict]:
    """Leer frontmatter YAML de un archivo .md. Retorna None si no existe."""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    yaml_text = text[3:end].strip()
    if not yaml_text:
        return {}
    return yaml.safe_load(yaml_text) or {}


def _write_md(path: Path, data: dict, body: str = ""):
    """Escribir archivo .md con frontmatter YAML y cuerpo opcional."""
    path.parent.mkdir(parents=True, exist_ok=True)
    resolved = _resolve_timestamps(data)
    frontmatter = yaml.dump(
        resolved,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    content = f"---\n{frontmatter}---\n"
    if body:
        content += f"\n{body}\n"
    path.write_text(content, encoding="utf-8")


# ──────────────────────────────────────────────
#  API compatible con Firestore (collection/document)
# ──────────────────────────────────────────────

class MarkdownSnapshot:
    """Equivalente a firestore.DocumentSnapshot"""

    def __init__(self, doc_id: str, reference: "MarkdownDocument", data: Optional[dict]):
        self.id = doc_id
        self.reference = reference
        self._data = data
        self.exists = data is not None

    def to_dict(self) -> dict:
        return dict(self._data) if self._data else {}


class MarkdownDocument:
    """Equivalente a firestore.DocumentReference"""

    def __init__(self, path: Path, doc_id: str):
        self.path = path
        self.id = doc_id
        self.reference = self

    def get(self) -> MarkdownSnapshot:
        data = _read_frontmatter(self.path)
        return MarkdownSnapshot(self.id, self, data)

    def set(self, data: dict, merge: bool = False):
        if merge and self.path.exists():
            existing = _read_frontmatter(self.path) or {}
            existing.update(_resolve_timestamps(data))
            data = existing
        _write_md(self.path, data)

    def update(self, data: dict):
        existing = _read_frontmatter(self.path) or {}
        existing.update(_resolve_timestamps(data))
        _write_md(self.path, existing)

    def delete(self):
        if self.path.exists():
            self.path.unlink()
        # Limpiar carpeta de subcolecciones si existe
        sub_dir = self.path.parent / f"_{self.id}"
        if sub_dir.exists():
            shutil.rmtree(sub_dir)

    def collection(self, name: str) -> "MarkdownCollection":
        """Subcolección almacenada en _<doc_id>/<name>/"""
        sub_path = self.path.parent / f"_{self.id}" / name
        return MarkdownCollection(sub_path)


class MarkdownCollection:
    """Equivalente a firestore.CollectionReference"""

    def __init__(self, path: Path):
        self.path = path
        self._order_field: Optional[str] = None
        self._filters: List[tuple] = []

    def document(self, doc_id: str) -> MarkdownDocument:
        return MarkdownDocument(self.path / f"{doc_id}.md", doc_id)

    def where(self, field: str, op: str, value) -> "MarkdownCollection":
        """Filtrar documentos por campo. Soporta operador '=='."""
        clone = MarkdownCollection(self.path)
        clone._order_field = self._order_field
        clone._filters = self._filters + [(field, op, value)]
        return clone

    def order_by(self, field: str) -> "MarkdownCollection":
        clone = MarkdownCollection(self.path)
        clone._order_field = field
        clone._filters = list(self._filters)
        return clone

    def stream(self) -> Iterator[MarkdownSnapshot]:
        """Iterar todos los documentos .md de la colección."""
        if not self.path.exists():
            return
        docs = []
        for f in sorted(self.path.glob("*.md")):
            doc_id = f.stem
            data = _read_frontmatter(f)
            if data is not None:
                # Aplicar filtros
                if self._filters:
                    skip = False
                    for field, op, value in self._filters:
                        doc_val = data.get(field)
                        if op == "==" and doc_val != value:
                            skip = True
                            break
                    if skip:
                        continue
                ref = MarkdownDocument(f, doc_id)
                docs.append(MarkdownSnapshot(doc_id, ref, data))
        if self._order_field and docs:
            docs.sort(key=lambda s: s.to_dict().get(self._order_field, 0))
        yield from docs


class MarkdownDB:
    """Equivalente a firestore.Client — raíz de acceso a colecciones."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def collection(self, name: str) -> MarkdownCollection:
        return MarkdownCollection(self.base_path / name)

    def collections(self) -> List[MarkdownCollection]:
        if not self.base_path.exists():
            return []
        return [
            MarkdownCollection(p)
            for p in sorted(self.base_path.iterdir())
            if p.is_dir() and not p.name.startswith("_")
        ]


# ──────────────────────────────────────────────
#  ObsidianManager — reemplazo directo de FirebaseManager
# ──────────────────────────────────────────────

class ObsidianManager:
    """
    Gestor de datos usando archivos Markdown estilo Obsidian.
    Reemplazo de FirebaseManager con la misma API pública.
    """

    def __init__(self, datos_path: Optional[str] = None):
        self.datos_path = Path(datos_path or os.getenv("DATOS_PATH", "datos"))
        self.db = MarkdownDB(self.datos_path)
        self.logger = logging.getLogger("obsidian_manager")
        self.logger.info(f"ObsidianManager inicializado: {self.datos_path}")

    def get_client(self) -> MarkdownDB:
        """Retorna el cliente MarkdownDB (equivalente a Firestore client)."""
        return self.db

    def test_connection(self) -> bool:
        """Verificar que la carpeta de datos es accesible."""
        try:
            self.datos_path.mkdir(parents=True, exist_ok=True)
            test_file = self.datos_path / ".test_write"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink()
            self.logger.info("Almacenamiento local verificado")
            return True
        except Exception as e:
            self.logger.error(f"Error verificando almacenamiento: {e}")
            return False

    # ── CRUD de estudiantes ─────────────────────

    def guardar_estudiante(self, matricola: str, datos_estudiante: dict) -> dict:
        """Guardar datos completos de un estudiante en un archivo .md"""
        try:
            self.logger.info(f"Guardando datos para matrícula: {matricola[:2]}****")

            perfil = datos_estudiante.get("perfil", {})
            horario = datos_estudiante.get("horario", [])
            materias = datos_estudiante.get("materias", [])
            calificaciones = datos_estudiante.get("calificaciones", [])

            doc_data = {
                "matricola": matricola,
                "nome": perfil.get("nome", ""),
                "cognome": perfil.get("cognome", ""),
                "email": perfil.get("email", f"{matricola}@unigre.it"),
                "telefono": perfil.get("telefono", ""),
                "ultima_actualizacion": datetime.now().isoformat(),
                "estado_horarios": datos_estudiante.get("estado_horarios", "no_disponible"),
                "semestre_activo": datos_estudiante.get("semestre_activo"),
                "fecha_extraccion": datetime.now().isoformat(),
                "version": "2.0",
                "horario": horario,
                "materias": materias,
                "calificaciones": calificaciones,
            }

            body = self._generar_cuerpo_estudiante(doc_data)
            path = self.datos_path / "estudiantes" / f"{matricola}.md"
            _write_md(path, doc_data, body)

            self.logger.info(f"Estudiante {matricola} guardado exitosamente")
            return {
                "success": True,
                "message": f"Datos guardados exitosamente para {matricola}",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error guardando estudiante {matricola}: {e}")
            return {
                "success": False,
                "message": f"Error guardando datos: {str(e)}",
                "error": str(e),
            }

    def obtener_estudiante(self, matricola: str) -> Optional[dict]:
        """Leer datos de un estudiante desde su archivo .md"""
        try:
            path = self.datos_path / "estudiantes" / f"{matricola}.md"
            return _read_frontmatter(path)
        except Exception as e:
            self.logger.error(f"Error obteniendo estudiante {matricola}: {e}")
            return None

    def obtener_todos_estudiantes(self) -> dict:
        """Leer todos los estudiantes desde la carpeta datos/estudiantes/"""
        try:
            self.logger.info("Obteniendo datos de todos los estudiantes")
            estudiantes: Dict[str, dict] = {}
            est_dir = self.datos_path / "estudiantes"
            if not est_dir.exists():
                return {}

            for f in sorted(est_dir.glob("*.md")):
                matricola = f.stem
                data = _read_frontmatter(f)
                if not data or "nome" not in data:
                    self.logger.warning(f"Estudiante {matricola} sin datos básicos — omitido")
                    continue

                estudiantes[matricola] = {
                    "nome": data.get("nome", ""),
                    "cognome": data.get("cognome", ""),
                    "email": data.get("email", ""),
                    "ultima_actualizacion": data.get("ultima_actualizacion"),
                    "estado_horarios": data.get("estado_horarios", "no_disponible"),
                    "horario": data.get("horario", []),
                }

            self.logger.info(f"Obtenidos datos de {len(estudiantes)} estudiantes")
            return estudiantes
        except Exception as e:
            self.logger.error(f"Error obteniendo todos los estudiantes: {e}")
            return {}

    def eliminar_estudiante(self, matricola: str) -> bool:
        """Eliminar el archivo .md de un estudiante."""
        try:
            path = self.datos_path / "estudiantes" / f"{matricola}.md"
            if path.exists():
                path.unlink()
                self.logger.info(f"Estudiante {matricola} eliminado")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error eliminando {matricola}: {e}")
            return False

    def get_statistics(self) -> dict:
        """Obtener estadísticas del sistema de almacenamiento."""
        try:
            total_docs = 0
            colecciones = 0
            for d in self.datos_path.iterdir():
                if d.is_dir() and not d.name.startswith('.'):
                    colecciones += 1
                    total_docs += sum(1 for _ in d.glob("*.md"))

            est_dir = self.datos_path / "estudiantes"
            total_est = 0
            con_horarios = 0
            if est_dir.exists():
                for f in est_dir.glob("*.md"):
                    total_est += 1
                    data = _read_frontmatter(f)
                    if data and data.get("horario"):
                        con_horarios += 1

            return {
                "total_colecciones": colecciones,
                "total_documentos": total_docs,
                "total_estudiantes": total_est,
                "estudiantes_con_horarios": con_horarios,
                "ultima_consulta": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}

    # ── Generador de Markdown legible ───────────

    @staticmethod
    def _generar_cuerpo_estudiante(data: dict) -> str:
        """Generar cuerpo Markdown legible para Obsidian."""
        lines: List[str] = []
        nombre = f"{data.get('cognome', '')} {data.get('nome', '')}".strip()
        lines.append(f"# {data['matricola']} — {nombre}")
        lines.append("")
        lines.append(f"> Última actualización: {data.get('ultima_actualizacion', 'N/A')}")

        sem = data.get("semestre_activo")
        if sem:
            lines.append(f"> Semestre activo: {sem}")

        # Tabla de horario
        horario = data.get("horario", [])
        if horario:
            lines.append("")
            lines.append("## Horario")
            lines.append("")
            lines.append("| Bloque | Día | Código | Materia | Profesor | Aula |")
            lines.append("|--------|-----|--------|---------|----------|------|")
            for c in horario:
                lines.append(
                    f"| {c.get('bloque','')} | {c.get('dia','')} "
                    f"| {c.get('codigo','')} | {c.get('materia','')} "
                    f"| {c.get('profesor','')} | {c.get('aula','')} |"
                )

        # Lista de materias
        materias = data.get("materias", [])
        if materias:
            lines.append("")
            lines.append("## Materias")
            lines.append("")
            for m in materias:
                cod = m.get("codigo", "")
                nom = m.get("nombre", m.get("materia", ""))
                lines.append(f"- **{cod}** — {nom}")

        return "\n".join(lines)


# ── Funciones de compatibilidad ─────────────

def inicializar_datos():
    """Inicializar el almacenamiento local. Retorna MarkdownDB."""
    return ObsidianManager().get_client()
