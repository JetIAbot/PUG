from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import subprocess
import sys
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializamos la aplicación Flask
app = Flask(__name__)
app.secret_key = 'una-clave-secreta-muy-segura' # Necesario para los mensajes flash

# Inicializamos Firebase en la app web, ya que es la que guardará los datos
cred = credentials.Certificate("credenciales.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


# --- Interfaz para el Estudiante ---
@app.route('/')
def index():
    """Página principal para el usuario/estudiante."""
    # Simplemente muestra la página de bienvenida.
    return render_template('index.html')

@app.route('/extraer-datos', methods=['POST'])
def extraer_datos():
    usuario = request.form.get('usuario')
    contrasena = request.form.get('contrasena')

    if not usuario or not contrasena:
        flash("El usuario y la contraseña son obligatorios.", "error")
        return redirect(url_for('index'))

    try:
        # Ejecutamos el script de scraping, añadiendo un manejador de errores de codificación
        resultado_proceso = subprocess.run(
            [sys.executable, 'main.py', '--usuario', usuario, '--contrasena', contrasena],
            capture_output=True, text=True, check=True, encoding='utf-8', errors='replace'
        )
        # Parseamos la salida JSON del script
        datos_extraidos = json.loads(resultado_proceso.stdout)

        if datos_extraidos.get("error"):
            flash(f"Error durante la extracción: {datos_extraidos['error']}", "error")
            return redirect(url_for('index'))

        if not datos_extraidos.get("datos_personales"):
             flash("No se pudieron extraer los datos personales. Verifique las credenciales o inténtelo más tarde.", "error")
             return redirect(url_for('index'))

        if not datos_extraidos.get("horario"):
            flash("Datos personales extraídos, pero el horario está vacío (posiblemente por vacaciones).", "info")
        
        return render_template('revisar.html', datos=datos_extraidos)

    except subprocess.CalledProcessError as e:
        # Si el script devuelve un código de error, mostramos su salida de error si existe
        error_output = e.stderr or e.stdout
        flash(f"Error crítico al ejecutar el script de scraping. Detalles: {error_output}", "error")
        return redirect(url_for('index'))
    except json.JSONDecodeError:
        # Este error es útil si el script falla y no imprime un JSON válido
        flash("Error de comunicación con el script de scraping (respuesta no válida).", "error")
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Ha ocurrido un error inesperado en la aplicación: {e}", "error")
        return redirect(url_for('index'))

@app.route('/guardar-horario', methods=['POST'])
def guardar_horario():
    """
    Recibe los datos del formulario de revisión y los guarda en Firestore.
    Esta función es la que finalmente escribe en la base de datos.
    """
    try:
        # 1. Recuperamos los datos personales del formulario
        matricola = request.form.get('matricola')
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')

        if not matricola:
            flash("Error: No se encontró la matrícula. No se puede guardar.", "error")
            return redirect(url_for('index'))

        # 2. Preparamos los datos del perfil del estudiante
        estudiante_ref = db.collection('estudiantes').document(matricola)
        datos_perfil = {'nome': nome, 'cognome': cognome}
        
        # Usamos .set con merge=True para crear o actualizar el perfil sin borrar otras subcolecciones
        estudiante_ref.set(datos_perfil, merge=True)

        # 3. Borramos el horario antiguo para asegurar consistencia
        horario_antiguo_ref = estudiante_ref.collection('horario')
        for doc in horario_antiguo_ref.stream():
            doc.reference.delete()
            
        # 4. (Opcional) Si hubiera un nuevo horario para guardar, aquí iría el código.
        #    Como en este caso de prueba el horario está vacío, no hacemos nada más.
        #    La lógica para guardar un horario con datos se añadiría aquí en el futuro.

        flash(f"¡Datos de {nome} {cognome} guardados correctamente en Firestore!", "success")

    except Exception as e:
        flash(f"Ocurrió un error al guardar en la base de datos: {e}", "error")
    
    return redirect(url_for('index'))


# --- Interfaz para el Administrador ---
@app.route('/admin')
def admin():
    """Página principal para el administrador."""
    return render_template('admin.html')

@app.route('/ejecutar-matchmaking', methods=['POST'])
def ejecutar_matchmaking():
    """
    Endpoint que se llama desde el botón en la interfaz del admin.
    Ejecuta el script matchmaking.py.
    """
    try:
        resultado = subprocess.run(
            [sys.executable, 'matchmaking.py'],
            capture_output=True, text=True, check=True, encoding='utf-8'
        )
        # Devolvemos el resultado como JSON para poder mostrarlo con más flexibilidad si se desea
        return jsonify(titulo="Resultado del Matchmaking", salida=resultado.stdout)
    except subprocess.CalledProcessError as e:
        error_msg = f"El script de matchmaking falló:\n{e.stderr or e.stdout}"
        return jsonify(titulo="Error en el Matchmaking", salida=error_msg), 500
    except Exception as e:
        return jsonify(titulo="Error inesperado", salida=str(e)), 500

# --- Plantilla genérica para mostrar resultados ---
@app.route('/resultado')
def resultado():
    # Esta ruta es solo para la plantilla, no se accede directamente.
    return render_template('resultado.html')


if __name__ == '__main__':
    # Se recomienda no usar el modo debug en producción
    app.run(host='0.0.0.0', port=5000)