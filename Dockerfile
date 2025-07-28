# filepath: d:\Documents\GitHub\PUG\Dockerfile
# Usamos una imagen oficial de Python como base.
FROM python:3.9-slim-bookworm

# Establecemos el directorio de trabajo
WORKDIR /workspaces/PUG

# --- INSTALACIÓN DE GOOGLE CHROME ---
# Añadimos los comandos para instalar Chrome y sus dependencias
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    --no-install-recommends \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y \
    google-chrome-stable \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && rm /etc/apt/sources.list.d/google-chrome.list

# Copiamos el archivo de dependencias primero para aprovechar el caché de Docker
COPY requirements.txt .

# Instalamos las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código de la aplicación
COPY . .

# Exponemos los puertos para Flask y Redis
EXPOSE 5000 6379

# El CMD se puede omitir si se inicia manualmente, o se puede configurar uno por defecto.
# CMD ["python", "src/app.py"]