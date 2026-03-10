"""
PUG - Portal University Grouper
Sistema de carpooling universitario - Universidad Pontificia Gregoriana
Interfaz de linea de comandos (CLI)

Uso: python main.py
"""

import os
import sys
import logging
from datetime import datetime, date

# Forzar UTF-8 en Windows para caracteres especiales
if os.name == "nt":
    os.system("chcp 65001 > NUL 2>&1")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Silenciar logs de librerias durante la interaccion con el usuario
logging.disable(logging.CRITICAL)


# ─── Colores ANSI (Windows 10+ / terminales modernas) ────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"


def ok(msg):   print(f"  {C.GREEN}[OK]{C.RESET} {msg}")
def err(msg):  print(f"  {C.RED}[ERROR]{C.RESET} {msg}")
def warn(msg): print(f"  {C.YELLOW}[AVISO]{C.RESET} {msg}")
def info(msg): print(f"  {C.CYAN}[INFO]{C.RESET} {msg}")


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


def pausar():
    input(f"\n  {C.DIM}Presiona Enter para continuar...{C.RESET}")


def titulo(texto):
    linea = "=" * (len(texto) + 4)
    print(f"\n{C.BOLD}{C.BLUE}  +{linea}+")
    print(f"  |  {texto}  |")
    print(f"  +{linea}+{C.RESET}\n")


def subtitulo(texto):
    print(f"\n{C.CYAN}  {'─' * 52}")
    print(f"  {C.BOLD}{texto}{C.RESET}")
    print(f"{C.CYAN}  {'─' * 52}{C.RESET}\n")


def menu_opcion(numero, texto, extra=""):
    extra_str = f"  {C.DIM}({extra}){C.RESET}" if extra else ""
    print(f"  {C.CYAN}[{numero}]{C.RESET} {texto}{extra_str}")


def pedir(label, requerido=True, valor_defecto=None):
    """Pedir input al usuario con validacion basica."""
    defecto_str = f" [{valor_defecto}]" if valor_defecto is not None else ""
    prompt = f"  {C.YELLOW}>{C.RESET} {label}{defecto_str}: "
    while True:
        try:
            valor = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if not valor and valor_defecto is not None:
            return valor_defecto
        if not valor and requerido:
            err("Campo requerido.")
            continue
        return valor


def pedir_opcion(opciones: list, label="Opcion"):
    """Mostrar lista numerada y devolver el valor elegido."""
    for i, op in enumerate(opciones, 1):
        print(f"  {C.CYAN}[{i}]{C.RESET} {op}")
    while True:
        try:
            val = int(pedir(label))
            if 1 <= val <= len(opciones):
                return opciones[val - 1]
            err(f"Ingresa un numero entre 1 y {len(opciones)}.")
        except ValueError:
            err("Ingresa un numero valido.")


def pedir_confirmacion(pregunta):
    """Pedir confirmacion s/n. Devuelve bool."""
    resp = pedir(f"{pregunta} [s/n]", requerido=False, valor_defecto="n")
    return resp.lower() in ("s", "si", "y", "yes")


# ─── Inicializacion lazy de managers ─────────────────────────────────────────

_managers = {}


def get_car_manager():
    if "car" not in _managers:
        from core.car_manager import CarManager
        _managers["car"] = CarManager()
    return _managers["car"]


def get_student_manager():
    if "student" not in _managers:
        from core.student_manager import StudentManager
        _managers["student"] = StudentManager()
    return _managers["student"]


def get_viaje_manager():
    if "viaje" not in _managers:
        from core.viaje_manager import ViajeManager
        _managers["viaje"] = ViajeManager()
    return _managers["viaje"]


def verificar_conexion():
    """Verificar acceso al almacenamiento local. Devuelve bool."""
    print(f"  {C.DIM}Verificando almacenamiento local...{C.RESET}", end="", flush=True)
    try:
        from core.obsidian_manager import ObsidianManager
        storage = ObsidianManager()
        if storage.test_connection():
            print(f"\r  {C.GREEN}Almacenamiento local OK.{C.RESET}                          ")
            return True
        else:
            print(f"\r  {C.RED}No se pudo acceder al almacenamiento.{C.RESET}               ")
            return False
    except Exception as e:
        print(f"\r  {C.RED}Error de conexion: {e}{C.RESET}")
        return False


# =============================================================================
#  MODULO: CARROS
# =============================================================================

def menu_carros():
    while True:
        limpiar()
        titulo("GESTION DE CARROS")
        menu_opcion(1, "Listar carros")
        menu_opcion(2, "Agregar carro")
        menu_opcion(3, "Ver detalle")
        menu_opcion(4, "Editar carro")
        menu_opcion(5, "Cambiar estado")
        menu_opcion(6, "Eliminar carro")
        menu_opcion(0, "Volver")
        print()
        op = pedir("Opcion", requerido=False, valor_defecto="0")
        if   op == "0": break
        elif op == "1": listar_carros()
        elif op == "2": crear_carro()
        elif op == "3": ver_carro()
        elif op == "4": editar_carro()
        elif op == "5": cambiar_estado_carro()
        elif op == "6": eliminar_carro()
        else: err("Opcion invalida.")


def _tabla_carros(carros):
    if not carros:
        warn("No se encontraron carros.")
        return
    fmt = "  {:<22} {:<22} {:<12} {:<12} {:<5} {}"
    print(f"\n{C.BOLD}" + fmt.format("ID", "MARCA / MODELO", "PLACA", "TIPO", "CAP", "ESTADO") + C.RESET)
    print("  " + "─" * 85)
    for c in carros:
        d = c if isinstance(c, dict) else c.to_dict()
        estado = d.get("estado", "")
        color = (C.GREEN if estado == "disponible"
                 else C.YELLOW if estado == "en_uso"
                 else C.RED)
        nombre = f"{d.get('marca','')} {d.get('modelo','')}".strip()
        print(fmt.format(
            d.get("id_carro", "")[:21],
            nombre[:21],
            d.get("placa", "")[:11],
            d.get("tipo_carro", "")[:11],
            str(d.get("capacidad_pasajeros", "")),
            f"{color}{estado}{C.RESET}"
        ))


def listar_carros():
    subtitulo("LISTA DE CARROS")
    try:
        cm = get_car_manager()
        estado = pedir(
            "Filtrar por estado [disponible/en_uso/mantenimiento/fuera_servicio] o Enter para todos",
            requerido=False, valor_defecto=""
        )
        filtros = {"estado": estado} if estado else {}
        carros = cm.obtener_todos_carros(filtros)
        _tabla_carros(carros)
        stats = cm.obtener_estadisticas()
        por_estado = stats.get('por_estado', {})
        print(f"\n  {C.DIM}Total: {stats.get('total_carros',0)} | "
              f"Disponibles: {por_estado.get('disponible',0)} | "
              f"En uso: {por_estado.get('en_uso',0)} | "
              f"Mantenimiento: {por_estado.get('mantenimiento',0)}{C.RESET}")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def crear_carro():
    subtitulo("AGREGAR CARRO")
    from core.models import TipoCarro, TipoCombustible
    try:
        marca     = pedir("Marca")
        modelo    = pedir("Modelo")
        anio      = pedir("Ano (ej: 2019)")
        placa     = pedir("Placa (ej: AB123CD)")

        print(f"\n  {C.CYAN}Tipo de carro:{C.RESET}")
        tipo = pedir_opcion([t.value for t in TipoCarro], "Tipo")

        print(f"\n  {C.CYAN}Combustible:{C.RESET}")
        combustible = pedir_opcion([t.value for t in TipoCombustible], "Combustible")

        capacidad = pedir("Capacidad de pasajeros")
        obs = pedir("Observaciones", requerido=False, valor_defecto="")

        datos = {
            "marca": marca, "modelo": modelo, "ano": anio, "placa": placa,
            "tipo_carro": tipo, "tipo_combustible": combustible,
            "capacidad_pasajeros": capacidad, "observaciones": obs,
        }
        res = get_car_manager().crear_carro(datos)
        if res["success"]:
            ok(res["message"])
        else:
            err(res["message"])
            for e_msg in res.get("errors", []):
                print(f"    - {e_msg}")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def ver_carro():
    subtitulo("DETALLE DE CARRO")
    id_carro = pedir("ID del carro")
    try:
        carro = get_car_manager().obtener_carro(id_carro)
        if not carro:
            err("Carro no encontrado.")
        else:
            d = carro if isinstance(carro, dict) else carro.to_dict()
            print()
            for k, v in d.items():
                print(f"  {C.CYAN}{k:<30}{C.RESET} {v}")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def editar_carro():
    subtitulo("EDITAR CARRO")
    id_carro = pedir("ID del carro")
    try:
        cm = get_car_manager()
        carro = cm.obtener_carro(id_carro)
        if not carro:
            err("Carro no encontrado.")
            pausar()
            return
        d = carro if isinstance(carro, dict) else carro.to_dict()
        info(f"Editando: {d.get('marca')} {d.get('modelo')} - {d.get('placa')}")
        info("Dejar en blanco mantiene el valor actual.")
        print()
        marca     = pedir("Marca",      requerido=False, valor_defecto=d.get("marca", ""))
        modelo    = pedir("Modelo",     requerido=False, valor_defecto=d.get("modelo", ""))
        anio      = pedir("Ano",        requerido=False, valor_defecto=str(d.get("ano", d.get("año", ""))))
        placa     = pedir("Placa",      requerido=False, valor_defecto=d.get("placa", ""))
        capacidad = pedir("Capacidad",  requerido=False, valor_defecto=str(d.get("capacidad_pasajeros", "")))
        obs       = pedir("Observaciones", requerido=False, valor_defecto=d.get("observaciones", ""))

        datos = {
            "marca": marca, "modelo": modelo, "ano": anio, "placa": placa,
            "tipo_carro": d.get("tipo_carro"), "tipo_combustible": d.get("tipo_combustible"),
            "capacidad_pasajeros": capacidad, "estado": d.get("estado"),
            "observaciones": obs,
        }
        res = cm.actualizar_carro(id_carro, datos)
        if res["success"]:
            ok(res["message"])
        else:
            err(res["message"])
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def cambiar_estado_carro():
    subtitulo("CAMBIAR ESTADO")
    from core.models import EstadoCarro
    id_carro = pedir("ID del carro")
    try:
        print(f"\n  {C.CYAN}Nuevo estado:{C.RESET}")
        estado_str = pedir_opcion([e.value for e in EstadoCarro], "Estado")
        res = get_car_manager().cambiar_estado_carro(id_carro, EstadoCarro(estado_str))
        if res["success"]:
            ok(res["message"])
        else:
            err(res["message"])
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def eliminar_carro():
    subtitulo("ELIMINAR CARRO")
    id_carro = pedir("ID del carro")
    try:
        cm = get_car_manager()
        carro = cm.obtener_carro(id_carro)
        if not carro:
            err("Carro no encontrado.")
            pausar()
            return
        d = carro if isinstance(carro, dict) else carro.to_dict()
        warn(f"Eliminar: {d.get('marca')} {d.get('modelo')} - {d.get('placa')}")
        if pedir_confirmacion("Confirmar eliminacion"):
            res = cm.eliminar_carro(id_carro)
            ok(res["message"]) if res["success"] else err(res["message"])
        else:
            info("Cancelado.")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


# =============================================================================
#  MODULO: ESTUDIANTES
# =============================================================================

def menu_estudiantes():
    while True:
        limpiar()
        titulo("GESTION DE ESTUDIANTES")
        menu_opcion(1, "Listar estudiantes")
        menu_opcion(2, "Agregar estudiante (manual)")
        menu_opcion(3, "Registrar via portal universitario", "requiere Chrome")
        menu_opcion(4, "Ver detalle")
        menu_opcion(5, "Editar estudiante")
        menu_opcion(6, "Marcar disponibilidad de hoy")
        menu_opcion(7, "Eliminar estudiante")
        menu_opcion(0, "Volver")
        print()
        op = pedir("Opcion", requerido=False, valor_defecto="0")
        if   op == "0": break
        elif op == "1": listar_estudiantes()
        elif op == "2": crear_estudiante()
        elif op == "3": registrar_via_portal()
        elif op == "4": ver_estudiante()
        elif op == "5": editar_estudiante()
        elif op == "6": marcar_disponibilidad()
        elif op == "7": eliminar_estudiante()
        else: err("Opcion invalida.")


def _tabla_estudiantes(estudiantes):
    if not estudiantes:
        warn("No se encontraron estudiantes.")
        return
    fmt = "  {:<12} {:<26} {:<32} {} {}"
    print(f"\n{C.BOLD}" + fmt.format("MATRICOLA", "NOMBRE", "EMAIL", "LICENCIA", "HOY") + C.RESET)
    print("  " + "─" * 85)
    for e in estudiantes:
        d = e if isinstance(e, dict) else e.to_dict()
        lic_txt = "Si" if d.get("tiene_licencia") else "No"
        hoy_txt = "Si" if d.get("viaja_hoy")      else "No"
        lic_color = C.GREEN if d.get("tiene_licencia") else C.DIM
        hoy_color = C.GREEN if d.get("viaja_hoy")      else C.DIM
        nombre = f"{d.get('nombre', d.get('nome', ''))} {d.get('apellido', d.get('cognome', ''))}".strip()
        print(fmt.format(
            d.get("matricola", "")[:11],
            nombre[:25],
            d.get("email", "")[:31],
            f"{lic_color}{lic_txt:<10}{C.RESET}",
            f"{hoy_color}{hoy_txt}{C.RESET}"
        ))


def listar_estudiantes():
    subtitulo("LISTA DE ESTUDIANTES")
    try:
        sm = get_student_manager()
        filtro = pedir(
            "Filtrar [todos/conductores/viajan_hoy]",
            requerido=False, valor_defecto="todos"
        )
        filtros = {}
        if filtro == "conductores":
            filtros["tiene_licencia"] = True
        elif filtro == "viajan_hoy":
            filtros["viaja_hoy"] = True

        estudiantes = sm.listar_estudiantes(filtros if filtros else None)
        _tabla_estudiantes(estudiantes)
        stats = sm.obtener_estadisticas()
        resumen = stats.get('resumen', {})
        print(f"\n  {C.DIM}Total: {resumen.get('total_estudiantes',0)} | "
              f"Conductores: {resumen.get('con_licencia',0)} | "
              f"Viajan hoy: {resumen.get('viajan_hoy',0)}{C.RESET}")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


DIAS_SEMANA_IT = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
DIAS_CORTO = {"Lunedì": "LUN", "Martedì": "MAR", "Mercoledì": "MIE", "Giovedì": "JUE", "Venerdì": "VIE"}


def _calcular_viaja_hoy(horario):
    """Determina si el estudiante viaja hoy segun su horario."""
    from datetime import datetime as _dt
    idx = _dt.now().weekday()
    if idx > 4:
        return False, "Fin de semana", 0
    dia_hoy = DIAS_SEMANA_IT[idx]
    clases_hoy = [c for c in horario if c.get("dia") == dia_hoy]
    return len(clases_hoy) > 0, dia_hoy, len(clases_hoy)


def _calcular_disponibilidad_semanal(horario):
    """Devuelve dict {dia_italiano: n_clases} para LUN-VIE."""
    disp = {}
    for dia in DIAS_SEMANA_IT:
        n = len([c for c in horario if c.get("dia") == dia])
        disp[dia] = n
    return disp


def _pedir_licencias():
    """Helper para pedir tipos de licencia. Devuelve (lista_tipos, fecha_vencimiento)."""
    from core.models import TipoLicencia
    tipos_disponibles = [t.value for t in TipoLicencia]
    print(f"\n  {C.CYAN}Tipos de licencia disponibles:{C.RESET}")
    cols = 5
    for i, t in enumerate(tipos_disponibles, 1):
        print(f"  {C.DIM}[{i:>2}]{C.RESET} {t:<6}", end="  ")
        if i % cols == 0:
            print()
    print()
    sel = pedir("Numeros separados por coma (ej: 4 para Licencia B)")
    tipos_lic = []
    for s in sel.split(","):
        try:
            idx = int(s.strip()) - 1
            if 0 <= idx < len(tipos_disponibles):
                tipos_lic.append(tipos_disponibles[idx])
        except ValueError:
            pass
    fecha_venc = pedir("Fecha vencimiento licencia (YYYY-MM-DD)")
    return tipos_lic, fecha_venc


def crear_estudiante():
    subtitulo("AGREGAR ESTUDIANTE MANUAL")
    try:
        matricola = pedir("Matricola (6-8 digitos)")
        nombre    = pedir("Nombre")
        apellido  = pedir("Apellido")
        email     = pedir("Email")
        telefono  = pedir("Telefono", requerido=False, valor_defecto="")

        tiene_lic = pedir_confirmacion("Tiene licencia de conducir?")
        tipos_lic, fecha_venc = ([], None)
        if tiene_lic:
            tipos_lic, fecha_venc = _pedir_licencias()
            # Verificar si la licencia esta vencida
            if fecha_venc:
                from datetime import date as _date
                try:
                    fecha_obj = _date.fromisoformat(fecha_venc)
                    if fecha_obj < _date.today():
                        warn("La licencia esta vencida. Se registrara como licencia vencida.")
                        tiene_lic = False
                        tipos_lic = []
                        fecha_venc = None
                except ValueError:
                    warn("Fecha invalida, se ignora.")
                    fecha_venc = None

        datos = {
            "matricola": matricola, "nombre": nombre, "apellido": apellido,
            "email": email, "telefono": telefono,
            "tiene_licencia": tiene_lic, "tipos_licencia": tipos_lic,
            "fecha_vencimiento_licencia": fecha_venc,
        }
        res = get_student_manager().crear_estudiante(datos)
        if res["success"]:
            ok(res["message"])
        else:
            err(res["message"])
            for e_msg in res.get("errors", []):
                print(f"    - {e_msg}")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def registrar_via_portal():
    subtitulo("REGISTRO VIA PORTAL UNIVERSITARIO")
    warn("Este proceso abre Chrome y accede al portal de la universidad.")
    warn("Requiere Chrome instalado y conexion a internet.")
    print()
    if not pedir_confirmacion("Continuar?"):
        return
    matricola = pedir("Matricola universitaria")
    password  = pedir("Contrasena del portal")
    info("Iniciando extraccion... (puede tardar 1-2 minutos)")
    try:
        from core.student_scheduler import StudentScheduler
        resultado = StudentScheduler().extraer_y_guardar_datos(matricola, password)
        if resultado["success"]:
            ok("Datos extraidos y guardados.")
            data = resultado.get("data", {})
            perfil = data.get("perfil", {})
            horario = data.get("horario", [])
            info(f"Estudiante: {perfil.get('nome','')} {perfil.get('cognome','')}")
            info(f"Clases encontradas: {len(horario)}")
            if horario:
                info(f"Semestre activo: {data.get('semestre_activo', '?')}")
                info(f"Materias: {len(data.get('materias', []))}")

            # Preguntas de carpooling
            print()
            subtitulo("DATOS DE CARPOOLING")
            tiene_lic = pedir_confirmacion("Tiene licencia de conducir?")
            tipos_lic, fecha_venc = [], None
            if tiene_lic:
                tipos_lic, fecha_venc = _pedir_licencias()

            # Determinar viaja_hoy automaticamente segun horario
            viaja_hoy, dia_hoy, n_clases = _calcular_viaja_hoy(horario)
            if viaja_hoy:
                info(f"Viaja hoy: Si ({n_clases} clases el {dia_hoy})")
            else:
                info(f"Viaja hoy: No (sin clases el {dia_hoy})")

            datos_extra = {
                "tiene_licencia": tiene_lic,
                "tipos_licencia": tipos_lic,
                "fecha_vencimiento_licencia": fecha_venc,
                "viaja_hoy": viaja_hoy,
            }
            res = get_student_manager().actualizar_estudiante(matricola, datos_extra)
            if res["success"]:
                ok("Datos de carpooling guardados.")
            else:
                err(f"No se pudieron guardar datos extra: {res.get('message','')}")
        else:
            err(f"No se pudo extraer: {resultado.get('message','Error desconocido')}")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def ver_estudiante():
    subtitulo("DETALLE DE ESTUDIANTE")
    matricola = pedir("Matricola")
    try:
        estudiante = get_student_manager().obtener_estudiante(matricola)
        if not estudiante:
            err("Estudiante no encontrado.")
        else:
            d = estudiante if isinstance(estudiante, dict) else estudiante.to_dict()
            nombre = f"{d.get('nombre', d.get('nome', ''))} {d.get('apellido', d.get('cognome', ''))}".strip()
            print()
            # --- Perfil ---
            print(f"  {C.BOLD}PERFIL{C.RESET}")
            print(f"  {'─' * 50}")
            print(f"  {C.CYAN}{'Nombre':<20}{C.RESET} {nombre}")
            print(f"  {C.CYAN}{'Matricola':<20}{C.RESET} {d.get('matricola','')}")
            print(f"  {C.CYAN}{'Email':<20}{C.RESET} {d.get('email','')}")
            print(f"  {C.CYAN}{'Telefono':<20}{C.RESET} {d.get('telefono','')}")
            sem = d.get('semestre_activo', '')
            if sem:
                print(f"  {C.CYAN}{'Semestre activo':<20}{C.RESET} {sem}")
            lic = d.get('tiene_licencia', False)
            print(f"  {C.CYAN}{'Licencia':<20}{C.RESET} {'Si' if lic else 'No'}")
            if lic:
                tipos = d.get('tipos_licencia', [])
                if tipos:
                    print(f"  {C.CYAN}{'  Tipos':<20}{C.RESET} {', '.join(tipos)}")
                fv = d.get('fecha_vencimiento_licencia', '')
                if fv:
                    print(f"  {C.CYAN}{'  Vencimiento':<20}{C.RESET} {fv}")
            viaja = d.get('viaja_hoy', False)
            print(f"  {C.CYAN}{'Viaja hoy':<20}{C.RESET} {'Si' if viaja else 'No'}")

            # --- Materias ---
            materias = d.get("materias", [])
            if materias:
                print(f"\n  {C.BOLD}MATERIAS ({len(materias)}){C.RESET}")
                print(f"  {'─' * 50}")
                for m in materias:
                    print(f"  {C.DIM}{m.get('codigo',''):<10}{C.RESET} {m.get('nombre','')}")
                    print(f"  {'':<10} {C.DIM}{m.get('profesor','')}{C.RESET}")

            # --- Horario tipo grilla ---
            horario = d.get("horario", d.get("clases", []))
            if horario:
                dias_orden = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
                dias_corto = {"Lunedì": "LUN", "Martedì": "MAR", "Mercoledì": "MIE", "Giovedì": "JUE", "Venerdì": "VIE"}
                # Agrupar por (bloque, dia)
                grid = {}
                bloques_set = set()
                for c in horario:
                    blq = c.get("bloque", "")
                    dia = c.get("dia", "")
                    bloques_set.add(blq)
                    grid[(blq, dia)] = c
                bloques_romanos = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
                bloques = [b for b in bloques_romanos if b in bloques_set]

                col_w = 18
                print(f"\n  {C.BOLD}HORARIO SEMANAL (Semestre {d.get('semestre_activo','?')}){C.RESET}")
                print(f"  {'─' * (8 + col_w * len(dias_orden))}")
                # Encabezado
                header = f"  {C.BOLD}{'BLQ':<8}"
                for dia in dias_orden:
                    header += f"{dias_corto.get(dia, dia):<{col_w}}"
                header += C.RESET
                print(header)
                print(f"  {'─' * (8 + col_w * len(dias_orden))}")
                # Filas por bloque
                for blq in bloques:
                    # Linea 1: codigo + materia abreviada
                    linea1 = f"  {C.CYAN}{blq:<8}{C.RESET}"
                    linea2 = f"  {'':<8}"
                    for dia in dias_orden:
                        clase = grid.get((blq, dia))
                        if clase:
                            cod = clase.get("codigo", "")
                            mat = clase.get("materia", "")
                            if len(mat) > col_w - 2:
                                mat = mat[:col_w - 4] + ".."
                            linea1 += f"{cod:<{col_w}}"
                            linea2 += f"{C.DIM}{mat:<{col_w}}{C.RESET}"
                        else:
                            linea1 += f"{C.DIM}{'---':<{col_w}}{C.RESET}"
                            linea2 += f"{'':<{col_w}}"
                    print(linea1)
                    print(linea2)
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def editar_estudiante():
    subtitulo("EDITAR ESTUDIANTE")
    matricola = pedir("Matricola")
    try:
        sm = get_student_manager()
        estudiante = sm.obtener_estudiante(matricola)
        if not estudiante:
            err("Estudiante no encontrado.")
            pausar()
            return
        d = estudiante if isinstance(estudiante, dict) else estudiante.to_dict()
        nom_actual = d.get('nombre', d.get('nome', ''))
        ape_actual = d.get('apellido', d.get('cognome', ''))
        info(f"Editando: {nom_actual} {ape_actual} ({matricola})")
        info("Enter mantiene el valor actual.")
        print()
        nombre   = pedir("Nombre",   requerido=False, valor_defecto=nom_actual)
        apellido = pedir("Apellido", requerido=False, valor_defecto=ape_actual)
        email    = pedir("Email",    requerido=False, valor_defecto=d.get("email", ""))
        telefono = pedir("Telefono", requerido=False, valor_defecto=d.get("telefono", ""))

        tiene_lic_actual = d.get("tiene_licencia", False)
        tiene_lic = pedir_confirmacion(
            f"Tiene licencia? (actual: {'Si' if tiene_lic_actual else 'No'})"
        )
        tipos_lic  = d.get("tipos_licencia", [])
        fecha_venc = d.get("fecha_vencimiento_licencia")

        if tiene_lic and pedir_confirmacion("Actualizar datos de licencia?"):
            tipos_lic, fecha_venc = _pedir_licencias()

        # viaja_hoy se calcula automaticamente del horario
        horario = d.get("horario", d.get("clases", []))
        viaja_hoy, dia_hoy, n_clases = _calcular_viaja_hoy(horario)
        if viaja_hoy:
            info(f"Viaja hoy: Si ({n_clases} clases el {dia_hoy})")
        else:
            info(f"Viaja hoy: No (sin clases el {dia_hoy})")

        datos = {
            "nombre": nombre, "apellido": apellido, "email": email, "telefono": telefono,
            "tiene_licencia": tiene_lic, "tipos_licencia": tipos_lic,
            "fecha_vencimiento_licencia": fecha_venc, "viaja_hoy": viaja_hoy,
        }
        res = sm.actualizar_estudiante(matricola, datos)
        if res["success"]:
            ok(res["message"])
        else:
            err(res["message"])
            for e_msg in res.get("errors", []):
                print(f"    - {e_msg}")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def marcar_disponibilidad():
    subtitulo("DISPONIBILIDAD SEMANAL")
    info("Calculando disponibilidad de TODOS los estudiantes para la semana...")
    print()
    try:
        sm = get_student_manager()
        estudiantes = sm.listar_estudiantes()
        if not estudiantes:
            warn("No hay estudiantes registrados.")
            pausar()
            return

        from datetime import datetime as _dt
        idx_hoy = _dt.now().weekday()
        dia_hoy_it = DIAS_SEMANA_IT[idx_hoy] if idx_hoy < 5 else None

        # Encabezado
        col_n = 22
        col_d = 8
        header = f"  {'ESTUDIANTE':<{col_n}}"
        for dia in DIAS_SEMANA_IT:
            marca = "*" if dia == dia_hoy_it else " "
            header += f"{DIAS_CORTO[dia]+marca:<{col_d}}"
        print(f"{C.BOLD}{header}{C.RESET}")
        print(f"  {'─' * (col_n + col_d * 5)}")

        actualizados = 0
        for e in estudiantes:
            d = e if isinstance(e, dict) else e.to_dict()
            mat = d.get("matricola", "")
            nombre = f"{d.get('nombre', d.get('nome', ''))} {d.get('apellido', d.get('cognome', ''))}".strip()
            horario = d.get("horario", d.get("clases", []))
            disp = _calcular_disponibilidad_semanal(horario)

            # Actualizar viaja_hoy basado en el dia actual
            viaja_hoy = disp.get(dia_hoy_it, 0) > 0 if dia_hoy_it else False
            sm.actualizar_estudiante(mat, {
                "viaja_hoy": viaja_hoy,
                "disponibilidad_semanal": {DIAS_CORTO[d_]: disp[d_] > 0 for d_ in DIAS_SEMANA_IT}
            })
            actualizados += 1

            # Fila
            linea = f"  {nombre[:col_n-1]:<{col_n}}"
            for dia in DIAS_SEMANA_IT:
                n = disp[dia]
                if n > 0:
                    linea += f"{C.GREEN}{'Si':^{col_d}}{C.RESET}"
                else:
                    linea += f"{C.DIM}{'--':^{col_d}}{C.RESET}"
            print(linea)

        print(f"  {'─' * (col_n + col_d * 5)}")
        if dia_hoy_it:
            info(f"* = hoy ({dia_hoy_it})")
        else:
            info("Hoy es fin de semana — no hay clases.")
        ok(f"{actualizados} estudiante(s) actualizados.")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def eliminar_estudiante():
    subtitulo("ELIMINAR ESTUDIANTE")
    matricola = pedir("Matricola")
    try:
        sm = get_student_manager()
        estudiante = sm.obtener_estudiante(matricola)
        if not estudiante:
            err("Estudiante no encontrado.")
            pausar()
            return
        d = estudiante if isinstance(estudiante, dict) else estudiante.to_dict()
        warn(f"Eliminar: {d.get('nombre', d.get('nome',''))} {d.get('apellido', d.get('cognome',''))} ({matricola})")
        if pedir_confirmacion("Confirmar eliminacion"):
            res = sm.eliminar_estudiante(matricola)
            ok(res["message"]) if res["success"] else err(res["message"])
        else:
            info("Cancelado.")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


# =============================================================================
#  MODULO: VIAJES
# =============================================================================

def menu_viajes():
    while True:
        limpiar()
        titulo("GESTION DE VIAJES")
        menu_opcion(1, "Listar viajes")
        menu_opcion(2, "Crear viaje manual")
        menu_opcion(3, "Ver detalle de viaje")
        menu_opcion(4, "Agregar pasajero a viaje")
        menu_opcion(5, "Asignacion automatica", "genera viajes del dia segun disponibilidad")
        menu_opcion(0, "Volver")
        print()
        op = pedir("Opcion", requerido=False, valor_defecto="0")
        if   op == "0": break
        elif op == "1": listar_viajes()
        elif op == "2": crear_viaje()
        elif op == "3": ver_viaje()
        elif op == "4": agregar_pasajero()
        elif op == "5": asignacion_automatica()
        else: err("Opcion invalida.")


def _tabla_viajes(viajes):
    if not viajes:
        warn("No se encontraron viajes.")
        return
    fmt = "  {:<22} {:<12} {:<8} {:<22} {:<16} {}"
    print(f"\n{C.BOLD}" + fmt.format("ID", "FECHA", "HORA", "CONDUCTOR", "ESTADO", "PAX") + C.RESET)
    print("  " + "─" * 90)
    for v in viajes:
        d = v if isinstance(v, dict) else v
        conductor = d.get("matricola_conductor", "")
        if not conductor:
            c_obj = d.get("conductor", {})
            conductor = c_obj.get("matricola", "") if isinstance(c_obj, dict) else ""
        pasajeros = d.get("pasajeros", [])
        n_pax = len(pasajeros) if isinstance(pasajeros, list) else 0
        estado = d.get("estado", "")
        color = C.GREEN if estado == "planificado" else C.YELLOW if estado == "en_curso" else C.DIM
        print(fmt.format(
            str(d.get("id_viaje", ""))[:21],
            str(d.get("fecha", ""))[:11],
            str(d.get("hora_salida", ""))[:7],
            str(conductor)[:21],
            f"{color}{estado}{C.RESET}",
            str(n_pax)
        ))


def listar_viajes():
    subtitulo("LISTA DE VIAJES")
    try:
        fecha  = pedir("Fecha (YYYY-MM-DD) o Enter para todos", requerido=False, valor_defecto="")
        estado = pedir(
            "Estado [planificado/en_curso/completado/cancelado] o Enter para todos",
            requerido=False, valor_defecto=""
        )
        viajes = get_viaje_manager().listar_viajes(
            fecha=fecha or None,
            estado=estado or None
        )
        _tabla_viajes(viajes)
        info(f"Total: {len(viajes)} viaje(s)")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def crear_viaje():
    subtitulo("CREAR VIAJE MANUAL")
    try:
        fecha   = pedir("Fecha del viaje (YYYY-MM-DD)", valor_defecto=date.today().isoformat())
        hora    = pedir("Hora de salida (HH:MM)", valor_defecto="08:00")
        origen  = pedir("Origen", valor_defecto="Residencia")
        destino = pedir("Destino", valor_defecto="Universidad Gregoriana")

        # Conductores disponibles
        sm = get_student_manager()
        conductores = sm.buscar_conductores_disponibles()
        if not conductores:
            warn("No hay conductores disponibles (estudiantes con licencia vigente).")
            pausar()
            return
        print(f"\n  {C.CYAN}Conductores disponibles:{C.RESET}")
        for c in conductores:
            d = c if isinstance(c, dict) else c.to_dict()
            lics = ", ".join(d.get("tipos_licencia", []))
            print(f"  {C.DIM}  {d.get('matricola',''):<12} "
                  f"{d.get('nombre','')} {d.get('apellido','')}  [{lics}]{C.RESET}")
        matricola_conductor = pedir("Matricola del conductor")

        # Carros disponibles
        cm = get_car_manager()
        carros_disp = cm.obtener_todos_carros({"estado": "disponible"})
        if not carros_disp:
            warn("No hay carros disponibles.")
            pausar()
            return
        print(f"\n  {C.CYAN}Carros disponibles:{C.RESET}")
        for c in carros_disp:
            d = c if isinstance(c, dict) else c.to_dict()
            print(f"  {C.DIM}  {d.get('id_carro',''):<24} "
                  f"{d.get('marca','')} {d.get('modelo','')} - {d.get('placa','')} "
                  f"(cap: {d.get('capacidad_pasajeros','')}){C.RESET}")
        id_carro = pedir("ID del carro")
        obs      = pedir("Observaciones", requerido=False, valor_defecto="")

        datos = {
            "fecha": fecha, "hora_salida": hora, "origen": origen, "destino": destino,
            "matricola_conductor": matricola_conductor, "id_carro": id_carro,
            "pasajeros": [], "observaciones": obs,
        }
        res = get_viaje_manager().crear_viaje(datos)
        if res["success"]:
            ok(f"Viaje creado: {res.get('id_viaje', '')}")
        else:
            err(res["message"])
            for e_msg in res.get("errors", []):
                print(f"    - {e_msg}")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def ver_viaje():
    subtitulo("DETALLE DE VIAJE")
    id_viaje = pedir("ID del viaje")
    try:
        viaje = get_viaje_manager().obtener_viaje(id_viaje)
        if not viaje:
            err("Viaje no encontrado.")
        else:
            d = viaje if isinstance(viaje, dict) else viaje
            print()
            for k in ("id_viaje", "fecha", "hora_salida", "origen", "destino", "estado", "observaciones"):
                if k in d:
                    print(f"  {C.CYAN}{k:<25}{C.RESET} {d[k]}")

            conductor = d.get("conductor", {})
            if isinstance(conductor, dict) and conductor:
                print(f"\n  {C.BOLD}Conductor:{C.RESET}")
                print(f"  {C.DIM}  {conductor.get('matricola','')}  "
                      f"{conductor.get('nombre','')} {conductor.get('apellido','')}{C.RESET}")

            carro = d.get("carro", {})
            if isinstance(carro, dict) and carro:
                print(f"\n  {C.BOLD}Carro:{C.RESET}")
                print(f"  {C.DIM}  {carro.get('marca','')} {carro.get('modelo','')} "
                      f"- {carro.get('placa','')}  (cap: {carro.get('capacidad_pasajeros','')}){C.RESET}")

            pasajeros = d.get("pasajeros", [])
            print(f"\n  {C.BOLD}Pasajeros ({len(pasajeros)}):{C.RESET}")
            if pasajeros:
                for p in pasajeros:
                    if isinstance(p, dict):
                        print(f"  {C.DIM}  - {p.get('matricola',''):<12} "
                              f"{p.get('nombre','')} {p.get('apellido','')}{C.RESET}")
            else:
                print(f"  {C.DIM}  (ninguno asignado){C.RESET}")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def agregar_pasajero():
    subtitulo("AGREGAR PASAJERO A VIAJE")
    id_viaje  = pedir("ID del viaje")
    matricola = pedir("Matricola del pasajero")
    try:
        res = get_viaje_manager().agregar_pasajero(id_viaje, matricola)
        if res["success"]:
            ok(res["message"])
        else:
            err(res["message"])
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def asignacion_automatica():
    subtitulo("ASIGNACION AUTOMATICA")
    info("Asigna conductores, carros y pasajeros segun disponibilidad del dia.")
    fecha = pedir("Fecha (YYYY-MM-DD)", valor_defecto=date.today().isoformat())
    if not pedir_confirmacion(f"Generar asignacion para {fecha}?"):
        return
    try:
        info("Calculando... (puede tardar unos segundos)")
        res = get_viaje_manager().generar_asignacion_automatica(fecha)
        if res["success"]:
            ok(res.get("message", "Asignacion completada"))
            viajes_c = res.get("viajes_creados", [])
            info(f"Viajes creados: {len(viajes_c)}")
            sin_asignar = res.get("estudiantes_sin_asignar", [])
            if sin_asignar:
                warn(f"Estudiantes sin asignar ({len(sin_asignar)}):")
                for m in sin_asignar:
                    print(f"  {C.DIM}    - {m}{C.RESET}")
        else:
            err(res.get("message", "Error en asignacion"))
            for e_msg in res.get("errors", []):
                print(f"    - {e_msg}")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


# =============================================================================
#  MODULO: LISTAS DIARIAS
# =============================================================================

def menu_listas():
    while True:
        limpiar()
        titulo("LISTAS DIARIAS")
        menu_opcion(1, "Lista de hoy")
        menu_opcion(2, "Lista de otra fecha")
        menu_opcion(3, "Generar lista (asignacion + crear)")
        menu_opcion(0, "Volver")
        print()
        op = pedir("Opcion", requerido=False, valor_defecto="0")
        if   op == "0": break
        elif op == "1": ver_lista_diaria(date.today().isoformat())
        elif op == "2": ver_lista_diaria(pedir("Fecha (YYYY-MM-DD)"))
        elif op == "3": generar_lista_diaria()
        else: err("Opcion invalida.")


def _imprimir_bloque_viajes(viajes, etiqueta):
    print(f"\n  {C.BOLD}{etiqueta} ({len(viajes)}):{C.RESET}")
    if not viajes:
        print(f"  {C.DIM}  (ninguno){C.RESET}")
        return
    for v in viajes:
        d = v if isinstance(v, dict) else v
        conductor = d.get("conductor", {})
        carro     = d.get("carro", {})
        pasajeros = d.get("pasajeros", [])
        print(f"\n  {C.CYAN}  [{d.get('hora_salida','')}]  "
              f"{d.get('origen','')} => {d.get('destino','')}{C.RESET}"
              f"  {C.DIM}({d.get('id_viaje','')}){C.RESET}")
        if isinstance(conductor, dict) and conductor:
            print(f"  {C.DIM}  Conductor : {conductor.get('nombre','')} {conductor.get('apellido','')} "
                  f"({conductor.get('matricola','')}){C.RESET}")
        if isinstance(carro, dict) and carro:
            print(f"  {C.DIM}  Carro     : {carro.get('marca','')} {carro.get('modelo','')} "
                  f"{carro.get('placa','')}  cap:{carro.get('capacidad_pasajeros','')}{C.RESET}")
        if pasajeros:
            nombres = [
                f"{p.get('nombre','')} {p.get('apellido','')}"
                for p in pasajeros if isinstance(p, dict)
            ]
            print(f"  {C.DIM}  Pasajeros : {', '.join(nombres)}{C.RESET}")


def ver_lista_diaria(fecha):
    subtitulo(f"LISTA DIARIA: {fecha}")
    try:
        lista = get_viaje_manager().obtener_lista_diaria(fecha)
        if not lista:
            warn(f"No hay lista generada para {fecha}.")
            info("Usa la opcion [3] Generar lista para crearla.")
        else:
            d = lista if isinstance(lista, dict) else lista
            print(f"  Estado    : {d.get('estado','')}")
            print(f"  Creado por: {d.get('creado_por','')}")
            _imprimir_bloque_viajes(d.get("viajes_ida",    []), "VIAJES DE IDA")
            _imprimir_bloque_viajes(d.get("viajes_vuelta", []), "VIAJES DE VUELTA")
            stats = d.get("estadisticas", {})
            if stats:
                print(f"\n  {C.DIM}Estudiantes ida: {stats.get('total_estudiantes_ida',0)} | "
                      f"vuelta: {stats.get('total_estudiantes_vuelta',0)} | "
                      f"carros: {stats.get('total_carros_usados',0)}{C.RESET}")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def generar_lista_diaria():
    subtitulo("GENERAR LISTA DIARIA")
    fecha = pedir("Fecha (YYYY-MM-DD)", valor_defecto=date.today().isoformat())
    if not pedir_confirmacion(f"Generar lista completa para {fecha}?"):
        return
    try:
        vm = get_viaje_manager()
        info("Paso 1/2: Ejecutando asignacion automatica...")
        res_asig = vm.generar_asignacion_automatica(fecha)
        if not res_asig["success"]:
            err(f"Error en asignacion: {res_asig.get('message','')}")
            pausar()
            return
        ids_viajes = res_asig.get("viajes_creados_ids", [])
        info(f"Viajes generados: {len(ids_viajes)}")

        info("Paso 2/2: Creando lista diaria...")
        res_lista = vm.crear_lista_diaria(fecha, viajes_ida=ids_viajes)
        if res_lista["success"]:
            ok(f"Lista diaria creada para {fecha}")
        else:
            err(res_lista.get("message", "Error creando lista"))
    except Exception as e:
        err(f"Error: {e}")
    pausar()


# =============================================================================
#  MODULO: SISTEMA
# =============================================================================

def menu_sistema():
    while True:
        limpiar()
        titulo("SISTEMA / CONFIGURACION")
        menu_opcion(1, "Estadisticas generales")
        menu_opcion(2, "Verificar almacenamiento local")
        menu_opcion(3, "Verificar Chrome / Selenium")
        menu_opcion(4, "Gestionar contrasena de administrador")
        menu_opcion(0, "Volver")
        print()
        op = pedir("Opcion", requerido=False, valor_defecto="0")
        if   op == "0": break
        elif op == "1": estadisticas_generales()
        elif op == "2": probar_almacenamiento()
        elif op == "3": probar_chrome()
        elif op == "4": gestionar_admin()
        else: err("Opcion invalida.")


def estadisticas_generales():
    subtitulo("ESTADISTICAS GENERALES")
    try:
        stats_c = get_car_manager().obtener_estadisticas()
        stats_e = get_student_manager().obtener_estadisticas()
        viajes_hoy = get_viaje_manager().listar_viajes(fecha=date.today().isoformat())

        print(f"\n  {C.BOLD}CARROS{C.RESET}")
        por_estado = stats_c.get('por_estado', {})
        print(f"  Total             {stats_c.get('total_carros',0)}")
        print(f"  Disponibles       {por_estado.get('disponible',0)}")
        print(f"  En uso            {por_estado.get('en_uso',0)}")
        print(f"  Mantenimiento     {por_estado.get('mantenimiento',0)}")
        print(f"  Fuera de servicio {por_estado.get('fuera_de_servicio',0)}")

        resumen_e = stats_e.get('resumen', {})
        print(f"\n  {C.BOLD}ESTUDIANTES{C.RESET}")
        print(f"  Total             {resumen_e.get('total_estudiantes',0)}")
        print(f"  Conductores       {resumen_e.get('con_licencia',0)}")
        print(f"  Viajan hoy        {resumen_e.get('viajan_hoy',0)}")

        print(f"\n  {C.BOLD}VIAJES HOY  ({date.today().isoformat()}){C.RESET}")
        print(f"  Total             {len(viajes_hoy)}")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def probar_almacenamiento():
    subtitulo("VERIFICAR ALMACENAMIENTO LOCAL")
    try:
        from core.obsidian_manager import ObsidianManager
        storage = ObsidianManager()
        if storage.test_connection():
            ok("Almacenamiento local accesible.")
            stats = storage.get_statistics()
            info(f"Directorio: {storage.datos_path}")
            info(f"Colecciones: {stats.get('total_colecciones', 0)}")
            info(f"Documentos: {stats.get('total_documentos', 0)}")
        else:
            err("No se pudo acceder al almacenamiento.")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


def probar_chrome():
    subtitulo("VERIFICAR CHROME / SELENIUM")
    info("Intentando iniciar Chrome en modo headless...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=opts)
        driver.get("about:blank")
        version = driver.capabilities.get("browserVersion", "desconocida")
        driver.quit()
        ok(f"Chrome funcionando. Version: {version}")
    except Exception as e:
        err(f"Chrome no disponible: {e}")
        info("Instala Google Chrome y luego: pip install webdriver-manager")
    pausar()


def gestionar_admin():
    subtitulo("GESTIONAR CONTRASENA ADMIN")
    try:
        from utils.admin_tools import AdminPasswordManager
        apm = AdminPasswordManager()
        print()
        menu_opcion(1, "Generar hash de nueva contrasena")
        menu_opcion(2, "Verificar una contrasena contra su hash")
        print()
        op = pedir("Opcion", requerido=False, valor_defecto="0")
        if op == "1":
            username = pedir("Nombre de usuario admin")
            password = pedir("Nueva contrasena")
            resultado = apm.generate_admin_hash(username, password)
            ok("Hash generado.")
            print(f"\n  {C.YELLOW}{resultado}{C.RESET}\n")
            info("Guarda este hash en tu .env.")
        elif op == "2":
            password     = pedir("Contrasena a verificar")
            hash_guardado = pedir("Hash guardado")
            if apm.verify_password(password, hash_guardado):
                ok("Contrasena valida.")
            else:
                err("Contrasena incorrecta.")
    except Exception as e:
        err(f"Error: {e}")
    pausar()


# =============================================================================
#  MENU PRINCIPAL
# =============================================================================

BANNER = f"""{C.BOLD}{C.BLUE}
  ██████╗ ██╗   ██╗ ██████╗
  ██╔══██╗██║   ██║██╔════╝
  ██████╔╝██║   ██║██║  ███╗
  ██╔═══╝ ██║   ██║██║   ██║
  ██║     ╚██████╔╝╚██████╔╝
  ╚═╝      ╚═════╝  ╚═════╝{C.RESET}
{C.CYAN}  Portal University Grouper
  Universidad Pontificia Gregoriana - Roma{C.RESET}
"""


def menu_principal():
    while True:
        limpiar()
        print(BANNER)
        print(f"  {C.DIM}Fecha activa : {date.today().isoformat()}   Modo : Terminal{C.RESET}\n")
        menu_opcion(1, "Gestionar Carros")
        menu_opcion(2, "Gestionar Estudiantes")
        menu_opcion(3, "Gestionar Viajes")
        menu_opcion(4, "Listas Diarias")
        menu_opcion(5, "Sistema / Configuracion")
        print()
        menu_opcion(0, f"{C.DIM}Salir{C.RESET}")
        print()
        op = pedir("Opcion", requerido=False, valor_defecto="0")
        if   op == "0":
            limpiar()
            print(f"\n  {C.CYAN}Hasta luego.{C.RESET}\n")
            sys.exit(0)
        elif op == "1": menu_carros()
        elif op == "2": menu_estudiantes()
        elif op == "3": menu_viajes()
        elif op == "4": menu_listas()
        elif op == "5": menu_sistema()
        else:
            err("Opcion invalida.")


# =============================================================================
#  PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    # Habilitar colores ANSI en la terminal de Windows
    if os.name == "nt":
        os.system("color")

    limpiar()
    print(BANNER)
    print(f"  {C.DIM}Iniciando sistema...{C.RESET}\n")

    if not verificar_conexion():
        print()
        warn("No se pudo acceder al almacenamiento local.")
        warn("Verifica que la carpeta datos/ existe y es accesible.")
        if not pedir_confirmacion("Continuar de todas formas?"):
            sys.exit(1)

    menu_principal()
