# filepath: d:\Documents\GitHub\PUG\Dockerfile
# Usamos una imagen oficial de Python como base.
FROM python:3.9-slim-bookworm

# Establecemos variables de entorno para que los logs de Python aparezcan inmediatamente.
ENV PYTHONUNBUFFERED=1

# Instalamos las dependencias del sistema: Redis para Celery y Git.
RUN apt-get update && apt-get install -y redis-server git

# Establecemos el directorio de trabajo dentro del contenedor.
WORKDIR /app

# Copiamos el archivo de requerimientos primero para aprovechar el caché de Docker.
COPY requirements.txt .

# Instalamos las dependencias de Python.
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código de nuestro proyecto al contenedor.
COPY . .

# Exponemos el puerto 5000 (para Flask) y 6379 (para Redis).
EXPOSE 5000 6379