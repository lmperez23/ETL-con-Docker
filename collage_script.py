import requests
import os
from urllib.parse import urlparse
from PIL import Image, ImageOps, ImageDraw
import matplotlib.pyplot as plt
import math
from io import BytesIO

# Solicitar al usuario la palabra clave de búsqueda y la ubicación geográfica
consulta = input("Introduce la palabra clave y/o la ubicación geográfica para la búsqueda: ")

# URL del endpoint de búsqueda
url = "https://collectionapi.metmuseum.org/public/collection/v1/search"

# Parámetros de la solicitud
parametros = {
    "q": consulta,    # La consulta de búsqueda ingresada por el usuario
    "geoLocation": consulta,  # Utilizar la misma entrada para la geolocalización
    "hasImages": True       # Filtrar solo objetos con imágenes disponibles
}

# Realizar la solicitud GET
respuesta = requests.get(url, params=parametros)

# Verificar si la solicitud fue exitosa
if respuesta.status_code == 200:
    # Convertir la respuesta JSON a un diccionario de Python
    datos = respuesta.json()
    
    # Obtener la lista de IDs de objetos
    ids_objetos = datos.get("objectIDs", [])
    
    if ids_objetos:
        print(f"Se encontraron {len(ids_objetos)} objetos relacionados con '{consulta}'.")

        # Crear la carpeta de salida si no existe
        carpeta_salida = "output"
        if not os.path.exists(carpeta_salida):
            os.makedirs(carpeta_salida)

        # Lista para almacenar las imágenes descargadas
        imagenes = []

        # Iterar sobre la lista de IDs de objetos para obtener la imagen principal de cada uno
        for id_objeto in ids_objetos:  # Sin límite, itera sobre todos los objetos
            url_objeto = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{id_objeto}"
            respuesta_objeto = requests.get(url_objeto)
            
            if respuesta_objeto.status_code == 200:
                datos_objeto = respuesta_objeto.json()
                # Descargar y usar la imagen si está disponible
                if 'primaryImage' in datos_objeto and datos_objeto['primaryImage']:
                    url_imagen = datos_objeto['primaryImage']
                    print(f"Descargando imagen del Object ID: {id_objeto}")
                    
                    # Descargar la imagen
                    respuesta_imagen = requests.get(url_imagen)
                    if respuesta_imagen.status_code == 200:
                        # Cargar la imagen directamente en la memoria
                        try:
                            img = Image.open(BytesIO(respuesta_imagen.content))
                            # Añadir bordes a la imagen para separarla visualmente
                            img.thumbnail((1000, 1000), Image.LANCZOS)  # Redimensionar la imagen para reducir el uso de memoria
                            img_con_borde = ImageOps.expand(img, border=5, fill='white')
                            imagenes.append(img_con_borde)
                        except Exception as e:
                            print(f"Error al abrir la imagen desde la URL {url_imagen}: {e}")
                    else:
                        print(f"Error al descargar la imagen con URL {url_imagen}: {respuesta_imagen.status_code}")
            else:
                print(f"Error al obtener el objeto con ID {id_objeto}: {respuesta_objeto.status_code}")

        # Crear un collage a partir de las imágenes descargadas
        if imagenes:
            # Determinar el tamaño del collage para que tenga una forma rectangular
            num_imagenes = len(imagenes)
            ruta_marco = os.path.join(os.getcwd(), 'Imagen_de_marco.png')
            img_marco = Image.open(ruta_marco) if os.path.exists(ruta_marco) else None
            if img_marco:
                relacion_aspecto_marco = img_marco.width / img_marco.height
                columnas_collage = round(math.sqrt(num_imagenes * relacion_aspecto_marco))
                filas_collage = math.ceil(num_imagenes / columnas_collage)
            else:
                columnas_collage = math.ceil(math.sqrt(num_imagenes * 1.5))
                filas_collage = math.ceil(num_imagenes / columnas_collage)

            print(f"El collage tendrá {filas_collage} filas y {columnas_collage} columnas (basado en la relación de aspecto del marco)")

            # Crear una figura para el collage con un fondo de color suave
            fig, axes = plt.subplots(filas_collage, columnas_collage, figsize=(columnas_collage * 3, filas_collage * 3), facecolor='lightgray')
            axes = axes.flatten() if num_imagenes > 1 else [axes]
            
            for ax, img in zip(axes, imagenes):
                # Mostrar la imagen en el eje correspondiente
                ax.imshow(img)
                # Desactivar los ejes para que no se muestren las marcas o bordes alrededor de la imagen
                ax.axis('off')
            
            # Eliminar ejes vacíos
            for ax in axes[len(imagenes):]:
                ax.axis('off')
            
            # Ajustar el diseño del collage
            plt.tight_layout()
            
            # Guardar el collage como imagen
            ruta_collage_sin_marco = os.path.join(carpeta_salida, f"collage_sin_marco_{consulta}.png")
            plt.savefig(ruta_collage_sin_marco, bbox_inches='tight', dpi=300)
            plt.close(fig)
            del imagenes  # Liberar memoria explícitamente  # Cierra la figura para liberar memoria

            # Añadir un marco alrededor del collage usando la imagen proporcionada
            try:
                img_collage = Image.open(ruta_collage_sin_marco)  # Cargar la imagen del collage previamente guardado
                ruta_marco = os.path.join(os.getcwd(), 'Imagen_de_marco.png')
                if not os.path.exists(ruta_marco):
                    raise FileNotFoundError(f"No se encontró la imagen del marco en: {ruta_marco}")
                img_marco = Image.open(ruta_marco).convert('RGBA')

                # Redimensionar el collage para mantener su relación de aspecto y encajar dentro del marco
                relacion_collage = img_collage.width / img_collage.height
                nuevo_ancho = img_marco.width - 400
                nueva_altura = int(nuevo_ancho / relacion_collage)
                if nueva_altura > img_marco.height - 400:
                    nueva_altura = img_marco.height - 400
                    nuevo_ancho = int(nueva_altura * relacion_collage)
                collage_redimensionado = img_collage.resize((nuevo_ancho, nueva_altura), Image.LANCZOS)
                
                # Crear una nueva imagen con el fondo del color del collage y pegar el collage centrado
                collage_con_fondo = Image.new('RGBA', img_marco.size, (211, 211, 211, 255))
                margen_x = (img_marco.width - nuevo_ancho) // 2
                margen_y = (img_marco.height - nueva_altura) // 2
                collage_con_fondo.paste(collage_redimensionado, (margen_x, margen_y))
                
                # Pegar el marco sobre la imagen del collage
                collage_con_marco = Image.alpha_composite(collage_con_fondo, img_marco)

                # Añadir la consulta de búsqueda en la parte inferior del cuadro
                draw = ImageDraw.Draw(collage_con_marco)
                posicion_texto = (10, img_marco.height - 50)
                draw.text(posicion_texto, f"The Metropolitan Museum of Art Collection: {consulta}", fill="black", size=80)
                
                # Guardar la imagen final
                ruta_collage_con_marco = os.path.join(carpeta_salida, f"Collage_{consulta}.png")
                collage_con_marco.save(ruta_collage_con_marco)

                # Eliminar el archivo del collage original
                if os.path.exists(ruta_collage_sin_marco):
                    os.remove(ruta_collage_sin_marco)

                print(f"Collage con marco guardado en: {ruta_collage_con_marco}")
            except Exception as e:
                print(f"Error al añadir el marco al collage: {e}")
    else:
        print(f"No se encontraron objetos relacionados con '{consulta}'.")
else:
    print(f"Error: {respuesta.status_code}")