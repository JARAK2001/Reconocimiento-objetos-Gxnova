# Usar una imagen base de Python oficial y ligera
FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y permitir que los logs se vean en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias para OpenCV y YOLO
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libx11-6 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el archivo de requerimientos e instalar dependencias de Python
COPY requirements.txt .
# Actualizar pip
RUN pip install --no-cache-dir --upgrade pip
# 1. Instalar numpy PRIMERO y de forma aislada para evitar que sea sobreescrito
RUN pip install --no-cache-dir "numpy==1.26.4"
# 2. Instalar PyTorch CPU-only (evita descargar versión CUDA ~2-3 GB)
RUN pip install --no-cache-dir \
    torch==2.2.2+cpu \
    torchvision==0.17.2+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu
# 3. Instalar el resto de dependencias (numpy ya está fijado, no se sobreescribirá)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto que usará Railway (vía variable de entorno $PORT)
EXPOSE 8080

# Comando para iniciar la aplicación usando uvicorn
# Railway inyectará automáticamente la variable $PORT
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
