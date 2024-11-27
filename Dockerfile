# Usa una imagen ligera de Python como base
FROM python:3.10-slim

# Instala herramientas adicionales necesarias para Pillow (procesamiento de imágenes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Establece un directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos de la carpeta local al contenedor
COPY requirements.txt /app/
COPY etl_script.py /app/

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Define el comando por defecto para ejecutar el script
CMD ["python", "etl_script.py"]
