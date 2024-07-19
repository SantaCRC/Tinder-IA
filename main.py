import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import train
import requests
import pickle
from config import get_config_value
from dotenv import load_dotenv
from deepface import DeepFace
import numpy as np
import random
import time
import auth

# Load environment variables from a .env file
load_dotenv()

def load_env_vars():
    """Load environment variables and handle if .env file does not exist."""
    if not os.path.exists('.env'):
        with open('.env', 'w') as file:
            file.write('TINDER_API_TOKEN=\n')  # Add the API token placeholder
            file.write('TINDER_REFRESH_TOKEN=\n')  # Add the refresh token placeholder
        raise FileNotFoundError(".env file created. Please add your TINDER_API_TOKEN.")
    
    API_URL = get_config_value('API_URL')
    X_AUTH_TOKEN = os.getenv('TINDER_API_TOKEN')
    
    if not X_AUTH_TOKEN:
        raise ValueError("TINDER_API_TOKEN is missing in the .env file.")
    
    return API_URL, X_AUTH_TOKEN

def check_api_connection(api_url, auth_token):
    """Check if it is possible to connect to the Tinder API and validate the AUTH Token."""
    URL = f"{api_url}/v2/profile"
    headers = {'X-Auth-Token': auth_token}
    response = requests.get(URL, headers=headers)
    
    if response.status_code == 401:
        print("Invalid AUTH Token. Please update the TINDER_API_TOKEN in the .env file.")
        auth.main()
        check_api_connection(api_url, auth_token)
        
    print("Successfully connected to the Tinder API.")
    return response.json()

def like_profile(api_url, user_id, headers):
    """Like a profile."""
    URL = f"{api_url}/like/{user_id}"
    response = requests.get(URL, headers=headers)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    return response.json()

def pass_profile(api_url, user_id, headers):
    """Pass a profile."""
    URL = f"{api_url}/pass/{user_id}"
    response = requests.get(URL, headers=headers)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    return response.json()

def like_to_you(api_url, headers):
    """Get the list of users that liked you."""
    URL = f"{api_url}/v2/fast-match"
    response = requests.get(URL, headers=headers)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    return response.json()

def get_recs(api_url, headers):
    """Get recommendations for Tinder users."""
    URL = f"{api_url}/v2/recs/core"
    response = requests.get(URL, headers=headers)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    return response.json()['data']['results']

def run():
    """Run the auto Tinder bot, liking or passing profiles using an AI model."""
    try:
        api_url, auth_token = load_env_vars()
    except (FileNotFoundError, ValueError) as e:
        print(e)
        return

    # Check if the API connection is valid
    try:
        check_api_connection(api_url, auth_token)
    except PermissionError as e:
        print(e)
        return

    headers = {'X-Auth-Token': auth_token}

    # Check if the model is already trained
    if not os.path.exists('model.pkl'):
        train.train()  # Train the model if not trained
    else:
        print("The model is already trained.")
        with open('model.pkl', 'rb') as file:
            model = pickle.load(file)
        
        # Get recommendations at random time intervals
        while True:
            recs = get_recs(api_url, headers)
            for rec in recs:
                photo_urls = [photo['url'] for photo in rec['user']['photos']]
                result = None
                for photo_url in photo_urls:
                    try:
                        new_image_features = train.detect_face(photo_url)[1]
                        if new_image_features:
                            new_image_embedding = new_image_features[0]['embedding']
                            result = model.predict(np.array(new_image_embedding).reshape(1, -1))[0]
                            print(f'The new image is classified as: {"Positive" if result == 1 else "Negative"}')
                            if result in (0, 1):
                                break
                    except Exception as e:
                        print(f"Error processing image {photo_url}: {e}")
                        continue

                user_id = rec['user']['_id']
                if result == 1:
                    print(f"User ID: {user_id}")
                    print(like_profile(api_url, user_id, headers))
                    break
                elif result == 0:
                    print(f"User ID: {user_id}")
                    print(pass_profile(api_url, user_id, headers))
                else:
                    print(f"No valid result for user ID: {user_id}")

            random_time = random.randint(20, 90)  # Wait for a random time between 20 and 90 seconds
            print(f"Waiting {random_time} seconds...")
            time.sleep(random_time)

run()
