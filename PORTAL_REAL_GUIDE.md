# 🌐 Guía de Uso con Portal Real de la Universidad

## 📋 **Configuración Completada**

### ✅ **Sistemas Integrados:**

1. **Portal Real**: `https://segreteria.unigre.it/asp/authenticate.asp`
2. **Selenium WebDriver**: Configurado de forma segura
3. **Enmascaramiento de Datos**: Activo para protección
4. **Limpieza Automática**: Configurada para datos sensibles

### 🔒 **Medidas de Seguridad Activas:**

- ✅ **Navegador en modo incógnito**
- ✅ **Datos enmascarados en logs**
- ✅ **Sesiones limpias automáticamente**
- ✅ **Timeouts configurados (30s conexión, 60s respuesta)**
- ✅ **Reintentos automáticos (máximo 3)**
- ✅ **Limpieza al cerrar aplicación**

## 🚀 **Cómo Usar con Datos Reales:**

### **1. Verificar Configuración:**
```bash
python scripts\security_check.py
```
*Debe mostrar 10/10 verificaciones pasadas*

### **2. Probar Conexión al Portal:**
```bash
python scripts\test_portal.py
```
*Permite probar la conexión antes de usar la aplicación completa*

### **3. Usar la Aplicación Web:**

1. **Abrir**: http://127.0.0.1:5000
2. **Ingresar**: Tu matrícula y contraseña reales
3. **Enviar**: El sistema se conectará automáticamente al portal real
4. **Esperar**: El proceso puede tomar 30-60 segundos

### **4. Flujo Completo:**

```
Usuario → Formulario Web → Portal Universitario Real → Extracción Datos → Firebase → Matchmaking → Resultados
```

## ⚙️ **Configuración Técnica:**

### **Variables de Entorno Activas:**
```properties
USE_REAL_PORTAL=True
PORTAL_URL=https://segreteria.unigre.it/asp/authenticate.asp
HEADLESS_MODE=True
CONNECTION_TIMEOUT=30
REQUEST_TIMEOUT=60
MAX_RETRIES=3
MASK_CREDENTIALS=True
```

### **Características del Navegador:**
- **Modo**: Incógnito + Sin caché
- **JavaScript**: Habilitado solo si es necesario
- **Imágenes**: Deshabilitadas para velocidad
- **User Agent**: Genérico para evitar detección
- **Plugins**: Todos deshabilitados

### **Selectores Web Configurados:**
- **Campo Usuario**: `name="txtName"`
- **Campo Contraseña**: `name="txtPassword"`
- **Botón Login**: `input[type='submit'][value='Accedi']`
- **Error de Login**: `"ERRORE DI AUTENTICAZIONE"`
- **Login Exitoso**: `"Benvenuto nella Segreteria Online"`

## 🔐 **Protocolo de Seguridad:**

### **Antes de Cada Uso:**
1. Ejecutar verificación de seguridad
2. Confirmar que .env está protegido
3. Verificar que logs están siendo enmascarados

### **Durante el Uso:**
1. Solo usar credenciales autorizadas
2. No compartir sesiones del navegador
3. Monitorear logs para verificar enmascaramiento

### **Después de Cada Uso:**
1. Cerrar completamente la aplicación (Ctrl+C)
2. Verificar limpieza automática ejecutada
3. Confirmar que no hay datos expuestos

### **Datos que se Extraen:**
- ✅ **Información Personal**: Nombre, apellido, matrícula
- ✅ **Horario de Clases**: Materias, horarios, aulas, profesores
- ✅ **Materias**: Lista completa de cursos
- ✅ **Calificaciones**: Notas y evaluaciones (si disponibles)

### **Datos que NO se Almacenan:**
- ❌ **Contraseñas**: Nunca se guardan
- ❌ **Información Financiera**: No se accede
- ❌ **Datos Sensibles**: Solo lo mínimo necesario

## 🚨 **Protocolo de Emergencia:**

Si ocurre algún problema:

1. **Detener Aplicación**:
   ```bash
   Ctrl+C  # En terminal donde corre Flask
   ```

2. **Limpieza Inmediata**:
   ```bash
   python src\log_cleaner.py
   ```

3. **Verificar Estado**:
   ```bash
   python scripts\security_check.py
   ```

## 📞 **Soporte y Contacto:**

- **Responsable**: Desarrollador autorizado
- **Alcance**: Solo desarrollo y pruebas
- **Limitaciones**: Datos no pueden salir del entorno local
- **Auditoría**: Todos los accesos se registran

## ✅ **Confirmación de Funcionamiento:**

- ✅ **Portal Real**: Conectado y funcional
- ✅ **Datos Seguros**: Enmascarados en logs
- ✅ **Autorización**: Confirmada y documentada
- ✅ **Responsabilidad**: Asumida por desarrollador único
- ✅ **Limpieza**: Automática al cerrar aplicación

---

**🎉 El sistema está completamente configurado para uso seguro con datos reales del portal universitario.**
