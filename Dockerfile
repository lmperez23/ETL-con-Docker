# Dockerfile para ejecutar el script de collage

# Imagen base de Python
FROM python:3.9-slim

# Crear y definir el directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto al contenedor
COPY . /app

# Asegurarse de que la imagen del marco esté disponible en el contenedor
COPY Imagen_de_marco.png /app

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Definir el comando para ejecutar el script
CMD ["python", "collage_script.py"]
