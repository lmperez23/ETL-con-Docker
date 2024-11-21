# Usa una imagen oficial de Python como base
FROM python:3.10-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de dependencias a la imagen
COPY requirements.txt /app/

# Instala las dependencias desde requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código a la imagen
COPY . /app

# Define el comando que se ejecutará al iniciar el contenedor
CMD ["python", "etl_script.py"]
