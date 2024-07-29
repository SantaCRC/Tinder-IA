from dotenv import load_dotenv
import requests
import os
import numpy as np
from sklearn.svm import OneClassSVM
import matplotlib.pyplot as plt
from deepface import DeepFace
from config import get_config_value
from PIL import Image
import urllib.request, pickle

# Load environment variables
load_dotenv()

# Configuration variables
API_URL = get_config_value('API_URL')
X_AUTH_TOKEN = os.getenv('TINDER_API_TOKEN')

def get_headers():
    """Generate the headers for the API requests."""
    return {
        'app_version': '6.9.4',
        'platform': 'ios',
        "User-agent": "Tinder/7.5.3 (iPhone; iOS 10.3.2; Scale/2.00)",
        "Accept": "application/json",
        "content-type": "application/json",
        "X-Auth-Token": X_AUTH_TOKEN
    }

def get_photos_train():
    """Retrieve the list of photos for training."""
    url = f"{API_URL}/v2/my-likes"
    photo_urls = []
    page_token = None

    while True:
        # Actualizar la URL con el page_token si existe
        paginated_url = url if page_token is None else f"{url}?page_token={page_token}"
        
        try:
            response = requests.get(paginated_url, headers=get_headers())
            response.raise_for_status()
            response_json = response.json()
            results = response_json.get('data', {}).get('results', [])
            photo_urls.extend([photo.get('url') for result in results for photo in result.get('user', {}).get('photos', [])])
            
            # Obtener el siguiente page_token
            page_token = response_json.get('data', {}).get('page_token')
            
            # Salir del bucle si no hay más page_token
            if not page_token:
                break
                
        except requests.RequestException as e:
            print(f"Error: {e} and token: {X_AUTH_TOKEN}")
            break

    return photo_urls

def detect_face(photo_url):
    """Detect faces in a given photo URL."""
    try:
        result = DeepFace.extract_faces(photo_url, detector_backend='ssd')
        embeddings = DeepFace.represent(photo_url)
        if result and result[0]['facial_area']:
            return result, embeddings
    except Exception as e:
        print(f"Error: this photo does not contain a face.")
    return None, None

def main():
    """Main function to process photos and detect faces."""
    valid_photos = []
    photo_urls = get_photos_train()

    if not isinstance(photo_urls, list):
        print(photo_urls)  # Handle the error message from get_photos_train
        return

    id_number = 0
    while id_number < len(photo_urls) and len(valid_photos) < 100:
        photo_url = photo_urls[id_number]
        print(f"Processing: {photo_url}")
        result, embeddings = detect_face(photo_url)
        if result and embeddings:
            valid_photos.append(embeddings[0]['embedding'])
            #plt.imshow(result[0]['face'])
            #plt.show()
        id_number += 1
            
    return np.array(valid_photos)

def train():
    valid_for_train = main()
    if valid_for_train is None:
        print("No valid photos found.")
    else:
        # check if the model is already trained
        if os.path.exists('model.pkl'):
            with open('model.pkl', 'rb') as file:
                model = pickle.load(file)
        else:
            # Entrenar el modelo One-Class SVM con los datos positivos
            model = OneClassSVM(gamma='auto').fit(valid_for_train)
            # create a file to save the model
            with open('model.pkl', 'wb') as file:
                pickle.dump(model, file)
            
        # Ejemplo de clasificación de una nueva imagen
        new_image_path = 'https://images-ssl.gotinder.com/u/mq1Js6nKbaZakpgMBCYKjQ/ueMzN1tRx8AdvNmU37LLad.jpeg?Policy=eyJTdGF0ZW1lbnQiOiBbeyJSZXNvdXJjZSI6IiovdS9tcTFKczZuS2JhWmFrcGdNQkNZS2pRLyoiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3MjA4MzYyOTB9fX1dfQ__&Signature=ruSHafX6QGFg~eXjfThL8RiQv2cqA924S6zFpbFJanH1DBNy7SxCuLgV~EDMHKU64TyEa8nosZpmDowGVHJqUvmKGIsAVqR~Bqp7rOQJSG-TsiQWutw9VPv8KnZ-0z1X21Rzl3R2qREjt1VAkrisILt9d1wLuE3qCcsdyIub7ofwb3S2vQpE2VZIMiEzEI5ZsiuYO1X6OthrCjSy6IJz269mb3haGYRxq1HxkRXdLk5ssG5qiSM6SXFFpyqkbzr6l5ihx-0BKo1lKlaBbODtffypsODQ0XRuowhxXhGmE2pI5gvQM75PSAPqg~aAHLANlm1Zvfl6FotLYmobKve78Q__&Key-Pair-Id=K368TLDEUPA6OI'
        img = np.array(Image.open(urllib.request.urlopen(new_image_path)))
        plt.imshow(img)
        plt.show()
        new_image_features = detect_face(new_image_path)[1]
        if new_image_features:
            new_image_embedding = new_image_features[0]['embedding']
            result = model.predict(np.array(new_image_embedding).reshape(1, -1))
            print(f'The new image is classified as: {"Positive" if result == 1 else "Negative"}')
        else:
            print("No face detected in the new image.")
