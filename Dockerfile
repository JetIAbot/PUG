# Dockerfile para PUG - Sistema de Matchmaking Universitario
FROM python:3.11-slim

# Metadatos del contenedor
LABEL maintainer="PUG Team"
LABEL description="PUG Carpooling - Sistema de matchmaking para estudiantes universitarios"
LABEL version="1.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=src/app.py
ENV FLASK_ENV=production

# Crear usuario no-root para seguridad
RUN groupadd -r puguser && useradd -r -g puguser puguser

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chrome para Selenium
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p logs static/uploads \
    && chown -R puguser:puguser /app \
    && chmod +x scripts/*.py

# Cambiar a usuario no-root
USER puguser

# Exponer puertos
EXPOSE 5000

# Configurar health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Comando por defecto
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "src.app:app"]
