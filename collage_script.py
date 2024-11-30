import requests
import os
from urllib.parse import urlparse
from PIL import Image, ImageOps, ImageDraw
import matplotlib.pyplot as plt
import math
from io import BytesIO

# Solicitar al usuario la palabra clave de búsqueda y la ubicación geográfica
query = input("Introduce la palabra clave y/o la ubicación geográfica para la búsqueda: ")

# URL del endpoint de búsqueda
url = "https://collectionapi.metmuseum.org/public/collection/v1/search"

# Parámetros de la solicitud
params = {
    "q": query,    # La consulta de búsqueda ingresada por el usuario
    "geoLocation": query,  # Utilizar la misma entrada para la geolocalización
    "hasImages": True       # Filtrar solo objetos con imágenes disponibles
}

# Realizar la solicitud GET
response = requests.get(url, params=params)

# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    # Convertir la respuesta JSON a un diccionario de Python
    data = response.json()
    
    # Obtener la lista de IDs de objetos
    object_ids = data.get("objectIDs", [])
    
    if object_ids:
        print(f"Se encontraron {len(object_ids)} objetos relacionados con '{query}'.")

        # Crear la carpeta output si no existe
        output_folder = "output"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Lista para almacenar las imágenes descargadas
        images = []

        # Iterar sobre la lista de IDs de objetos para obtener la imagen principal de cada uno
        for object_id in object_ids:  # Sin límite, itera sobre todos los objetos
            object_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}"
            object_response = requests.get(object_url)
            
            if object_response.status_code == 200:
                object_data = object_response.json()
                # Descargar y usar la imagen si está disponible
                if 'primaryImage' in object_data and object_data['primaryImage']:
                    image_url = object_data['primaryImage']
                    print(f"Descargando imagen del Object ID: {object_id}")
                    
                    # Descargar la imagen
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                        # Cargar la imagen directamente en la memoria
                        try:
                            img = Image.open(BytesIO(image_response.content))
                            # Añadir bordes a la imagen para separarla visualmente
                            img.thumbnail((1000, 1000), Image.LANCZOS)  # Redimensionar la imagen para reducir el uso de memoria
                            img_with_border = ImageOps.expand(img, border=5, fill='white')
                            images.append(img_with_border)
                        except Exception as e:
                            print(f"Error al abrir la imagen desde la URL {image_url}: {e}")
                    else:
                        print(f"Error al descargar la imagen con URL {image_url}: {image_response.status_code}")
            else:
                print(f"Error al obtener el objeto con ID {object_id}: {object_response.status_code}")

        # Crear un collage a partir de las imágenes descargadas
        if images:
            # Determinar el tamaño del collage para que tenga una forma rectangular
            num_images = len(images)
            frame_path = os.path.join(os.getcwd(), 'Imagen_de_marco.png')
            frame_img = Image.open(frame_path) if os.path.exists(frame_path) else None
            if frame_img:
                frame_aspect_ratio = frame_img.width / frame_img.height
                collage_columns = round(math.sqrt(num_images * frame_aspect_ratio))
                collage_rows = math.ceil(num_images / collage_columns)
            else:
                collage_columns = math.ceil(math.sqrt(num_images * 1.5))
                collage_rows = math.ceil(num_images / collage_columns)

            print(f"Collage tendrá {collage_rows} filas y {collage_columns} columnas (basado en la relación de aspecto del marco)")

            # Crear una figura para el collage con un fondo de color suave
            fig, axes = plt.subplots(collage_rows, collage_columns, figsize=(collage_columns * 3, collage_rows * 3), facecolor='lightgray')
            axes = axes.flatten() if num_images > 1 else [axes]
            
            for ax, img in zip(axes, images):
                # Mostrar la imagen en el eje correspondiente
                ax.imshow(img)
                # Desactivar los ejes para que no se muestren las marcas o bordes alrededor de la imagen
                ax.axis('off')
            
            # Eliminar ejes vacíos
            for ax in axes[len(images):]:
                ax.axis('off')
            
            # Ajustar el diseño del collage
            plt.tight_layout()
            
            # Guardar el collage como imagen
            collage_path = os.path.join(output_folder, f"collage_{query}.png")
            plt.savefig(collage_path, bbox_inches='tight', dpi=300)
            plt.close(fig)
            del images  # Liberar memoria explícitamente  # Cierra la figura para liberar memoria

            # Añadir un marco alrededor del collage usando la imagen proporcionada
            try:
                collage_img = Image.open(collage_path)  # Cargar la imagen del collage previamente guardado
                frame_path = os.path.join(os.getcwd(), 'Imagen_de_marco.png')
                if not os.path.exists(frame_path):
                    raise FileNotFoundError(f"No se encontró la imagen del marco en: {frame_path}")
                frame_img = Image.open(frame_path).convert('RGBA')

                # Redimensionar el collage para mantener su relación de aspecto y encajar dentro del marco
                collage_ratio = collage_img.width / collage_img.height
                new_width = frame_img.width - 400
                new_height = int(new_width / collage_ratio)
                if new_height > frame_img.height - 400:
                    new_height = frame_img.height - 400
                    new_width = int(new_height * collage_ratio)
                collage_resized = collage_img.resize((new_width, new_height), Image.LANCZOS)
                
                # Crear una nueva imagen con el fondo del color del collage y pegar el collage centrado
                collage_with_background = Image.new('RGBA', frame_img.size, (211, 211, 211, 255))
                margin_x = (frame_img.width - new_width) // 2
                margin_y = (frame_img.height - new_height) // 2
                collage_with_background.paste(collage_resized, (margin_x, margin_y))
                
                # Pegar el marco sobre la imagen del collage
                framed_collage = Image.alpha_composite(collage_with_background, frame_img)

                # Añadir la consulta de búsqueda en la parte inferior del cuadro
                draw = ImageDraw.Draw(framed_collage)
                text_position = (10, frame_img.height - 50)
                draw.text(text_position, f"The Metropolitan Museum of Art Collection: {query}", fill="black", size=36)
                
                # Guardar la imagen final
                framed_collage_path = os.path.join(output_folder, f"framed_collage_{query}.png")
                framed_collage.save(framed_collage_path)

                # Eliminar el archivo del collage original
                if os.path.exists(collage_path):
                    os.remove(collage_path)

                print(f"Collage con marco guardado en: {framed_collage_path}")
            except Exception as e:
                print(f"Error al añadir el marco al collage: {e}")
    else:
        print(f"No se encontraron objetos relacionados con '{query}'.")
else:
    print(f"Error: {response.status_code}")
