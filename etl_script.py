import requests
import json
import os
from urllib.parse import urlparse
from PIL import Image, ImageOps
import matplotlib.pyplot as plt

# Definir la palabra clave de búsqueda
query = "Spain"

# URL del endpoint de búsqueda
url = "https://collectionapi.metmuseum.org/public/collection/v1/search"

# Parámetros de la solicitud
params = {
    "q": query,             # La consulta de búsqueda
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
    
    objects_with_images = []
    
    if object_ids:
        print(f"Se encontraron {len(object_ids)} objetos relacionados con '{query}'.")
        # Crear una carpeta para almacenar las imágenes descargadas con el nombre del query
        images_folder = f"downloaded_images_{query}"
        if not os.path.exists(images_folder):
            os.makedirs(images_folder)
        
        # Lista para almacenar las rutas de las imágenes descargadas
        image_paths = []
        
        # Iterar sobre la lista de IDs de objetos para obtener la imagen principal de cada uno
        for object_id in object_ids:  # Iterar sobre todos los objetos
            object_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}"
            object_response = requests.get(object_url)
            
            if object_response.status_code == 200:
                object_data = object_response.json()
                # Descargar y almacenar la imagen si está disponible y es de dominio público
                if 'primaryImage' in object_data and object_data['primaryImage'] and object_data.get('isPublicDomain', False):
                    image_url = object_data['primaryImage']
                    print(f"Object ID: {object_id}")
                    print(f"Image URL: {image_url}")
                    print("----------------------------------------")
                    
                    # Agregar el objeto con la URL de la imagen a la lista
                    objects_with_images.append({"objectID": object_id, "imageURL": image_url})
                    
                    # Descargar la imagen
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                        # Obtener el nombre del archivo de la URL
                        image_name = os.path.basename(urlparse(image_url).path)
                        image_path = os.path.join(images_folder, image_name)
                        
                        # Guardar la imagen en la carpeta
                        with open(image_path, 'wb') as img_file:
                            img_file.write(image_response.content)
                        
                        # Agregar la ruta de la imagen a la lista
                        image_paths.append(image_path)
                    else:
                        print(f"Error al descargar la imagen con URL {image_url}: {image_response.status_code}")
            else:
                print(f"Error al obtener el objeto con ID {object_id}: {object_response.status_code}")
        
        # Exportar la lista de objetos con sus URLs de imagen a un archivo JSON con el nombre del query
        json_filename = f'objects_with_images_{query}.json'
        with open(json_filename, 'w') as json_file:
            json.dump(objects_with_images, json_file, indent=4)
        
        # Crear un collage a partir de las imágenes descargadas
        if image_paths:
            images = [Image.open(image_path) for image_path in image_paths if os.path.exists(image_path)]
            
            # Añadir bordes a las imágenes para separarlas visualmente
            images = [ImageOps.expand(img, border=5, fill='white') for img in images]
            
            # Determinar el tamaño del collage
            num_images = len(images)
            collage_columns = min(14, num_images)  # Máximo 14 columnas
            collage_rows = (num_images // collage_columns) + int(num_images % collage_columns > 0)
            
            # Crear una figura para el collage con un fondo de color suave
            fig, axes = plt.subplots(collage_rows, collage_columns, figsize=(35, 3 * collage_rows), facecolor='lightgray')
            axes = axes.flatten() if num_images > 1 else [axes]
            
            for ax, img in zip(axes, images):
                ax.imshow(img)
                ax.axis('off')
            
            # Eliminar ejes vacíos
            for ax in axes[len(images):]:
                ax.axis('off')
            
            plt.tight_layout()
            collage_path = f"collage_{query}.png"
            # Añadir un marco dorado al collage completo antes de guardarlo
            plt.savefig(collage_path)
            collage_img = Image.open(collage_path)
            collage_with_border = ImageOps.expand(collage_img, border=20, fill='gold')
            collage_with_border.save(collage_path)            
            print(f"Collage guardado en: {collage_path}")
    else:
        print(f"No se encontraron objetos relacionados con '{query}'.")
else:
    print(f"Error: {response.status_code}")
