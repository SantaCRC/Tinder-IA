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
import customtkinter
import threading
import sys
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import queue
from PIL import Image, ImageTk
import io


# last profile liked and passed id
last_liked_id = None
last_passed_id = None

# Create thread-safe queues for console output and images
console_queue = queue.Queue()
liked_image_queue = queue.Queue()
passed_image_queue = queue.Queue()

# Variable to track if the bot is running
bot_running = False

def run_bot():
    """Helper function to run the bot in another thread and reset the stop event."""
    global bot_thread, bot_running
    if not bot_running:
        stop_event.clear()
        bot_thread = threading.Thread(target=run)
        bot_thread.start()
        bot_running = True
        run_button.configure(state='disabled')
        stop_button.configure(state='normal')
    else:
        print("The bot is already running.")

def stop_bot():
    """Helper function to stop the bot thread."""
    global bot_running
    if bot_running:
        stop_event.set()
        bot_thread.join()
        bot_running = False
        stop_button.configure(state='disabled')
        run_button.configure(state='normal')
    else:
        print("The bot is not running.")

# Function to update the console output in the GUI
def update_console_output():
    while not console_queue.empty():
        message = console_queue.get_nowait()
        console_output.configure(state='normal')
        console_output.insert(tk.END, message)
        console_output.configure(state='disabled')
        console_output.yview(tk.END)  # Scroll to the end
    app.after(100, update_console_output)  # Schedule next update

def update_images():
    while not liked_image_queue.empty():
        image_data = liked_image_queue.get_nowait()
        img = ImageTk.PhotoImage(image_data)
        liked_image_label.configure(image=img, text="")
        liked_image_label.image = img  # Keep a reference to avoid garbage collection
    while not passed_image_queue.empty():
        image_data = passed_image_queue.get_nowait()
        img = ImageTk.PhotoImage(image_data)
        passed_image_label.configure(image=img, text="")
        passed_image_label.image = img  # Keep a reference to avoid garbage collection
    app.after(100, update_images)  # Schedule next update

# Custom print function to put messages in the queue
def custom_print(*args, **kwargs):
    message = ' '.join(map(str, args))
    console_queue.put(message)

# Redirect stdout and stderr to custom_print function
sys.stdout.write = custom_print
sys.stderr.write = custom_print

# Set appearance and theme for customtkinter
customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

# Create CTk window
app = customtkinter.CTk()
app.geometry("1000x800")
app.title("Tinder Bot")

# Create a frame for the images
image_frame = customtkinter.CTkFrame(master=app)
image_frame.pack(pady=10)

# Create labels for displaying the images
liked_image_label = customtkinter.CTkLabel(master=image_frame, text="No image")
liked_image_label.grid(row=1, column=0, padx=10)

passed_image_label = customtkinter.CTkLabel(master=image_frame, text="No image")
passed_image_label.grid(row=1, column=1, padx=10)

# Create labels for the image descriptions
liked_label = customtkinter.CTkLabel(master=image_frame, text="Last Liked")
liked_label.grid(row=0, column=0, padx=10)

passed_label = customtkinter.CTkLabel(master=image_frame, text="Last Passed")
passed_label.grid(row=0, column=1, padx=10)

# Create a frame for the buttons
button_frame = customtkinter.CTkFrame(master=app)
button_frame.pack(pady=10)

# Create buttons to run and stop the bot
run_button = customtkinter.CTkButton(master=button_frame, text="Run Tinder Bot", command=run_bot)
run_button.grid(row=0, column=1, padx=10)

stop_button = customtkinter.CTkButton(master=button_frame, text="Stop Tinder Bot", command=stop_bot)
stop_button.grid(row=0, column=2, padx=10)

# Create buttons to like and pass profiles manually
like_button = customtkinter.CTkButton(master=button_frame, text="Like last passed profile", command=like_last_passed_profile)
like_button.grid(row=0, column=3, padx=10)

pass_button = customtkinter.CTkButton(master=button_frame, text="Pass last liked profile", command=pass_last_liked_profile)
pass_button.grid(row=0, column=0, padx=10)

# Create a frame for the console output
frame = customtkinter.CTkFrame(master=app)
frame.pack(pady=10, padx=10, fill="both", expand=True)

# Create a ScrolledText widget for displaying the console output
console_output = ScrolledText(frame, wrap=tk.WORD, state='disabled', bg="black", fg="white")
console_output.pack(fill="both", expand=True)

# Load environment variables from a .env file
load_dotenv()

stop_event = threading.Event()

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
    
    while True:
        try:
            response = requests.get(URL, headers=headers)
            
            if response.status_code == 401:
                print("Invalid AUTH Token. Please update the TINDER_API_TOKEN in the .env file.")
                auth.main()
                auth_token = os.getenv("TINDER_API_TOKEN")  # Refresh the token after auth.main()
                headers = {'X-Auth-Token': auth_token}
                break  # Retry the connection
            
            print("Successfully connected to the Tinder API.")
            return response.json()
        
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
            time.sleep(5)  # Wait before retrying

def like_last_passed_profile(api_url, headers):
    """Like the last passed profile."""
    if not last_passed_id:
        print("No profile has been passed yet.")
        return
    URL = f"{api_url}/like/{last_passed_id}"
    response = requests.get(URL, headers=headers)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    return response.json()

def pass_last_liked_profile(api_url, headers):
    """Pass the last liked profile."""
    if not last_liked_id:
        print("No profile has been liked yet.")
        return
    URL = f"{api_url}/pass/{last_liked_id}"
    response = requests.get(URL, headers=headers)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    return response.json()


def like_profile(api_url, user_id, headers):
    """Like a profile."""
    URL = f"{api_url}/like/{user_id}"
    last_liked_id = user_id
    response = requests.get(URL, headers=headers)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    return response.json()

def pass_profile(api_url, user_id, headers):
    """Pass a profile."""
    URL = f"{api_url}/pass/{user_id}"
    last_passed_id = user_id
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

def save_tokens_to_env(key, value):
    """Save tokens to the .env file without adding quotes."""
    env_path = dotenv.find_dotenv()
    if not env_path:
        env_path = '.env'
    with open(env_path, 'r') as file:
        lines = file.readlines()
    with open(env_path, 'w') as file:
        for line in lines:
            if line.startswith(key + '='):
                file.write(f"{key}={value}\n")
            else:
                file.write(line)
        if not any(line.startswith(key + '=') for line in lines):
            file.write(f"{key}={value}\n")

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
        while not stop_event.is_set():
            recs = get_recs(api_url, headers)
            for rec in recs:
                if stop_event.is_set():
                    break
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
                                image_data = display_image(photo_url)
                                if result == 1:
                                    liked_image_queue.put(image_data)
                                else:
                                    passed_image_queue.put(image_data)
                                break
                    except Exception as e:
                        print(f"Error processing image {photo_url}: {e}")
                        continue

                user_id = rec['user']['_id']
                if result == 1:
                    print(f"User ID: {user_id}")
                    like_profile(api_url, user_id, headers)
                elif result == 0:
                    print(f"User ID: {user_id}")
                    pass_profile(api_url, user_id, headers)
                    passed_image_queue.put(display_image(photo_urls[0]))
                else:
                    print(f"No valid result for user ID: {user_id}, swiping left.")
                    pass_profile(api_url, user_id, headers)
                    passed_image_queue.put(display_image(photo_urls[0]))

                total_wait_time = random.randint(1, 5)
                elapsed_time = 0
                interval = 1  # Check for stop event every second
                print(f"Waiting {total_wait_time} seconds...")
                while elapsed_time < total_wait_time and not stop_event.is_set():
                    time.sleep(interval)
                    elapsed_time += interval

def display_image(image_url):
    """Display the image."""
    response = requests.get(image_url)
    image_data = response.content
    image = Image.open(io.BytesIO(image_data))
    image = image.resize((400, 400))  # Resize image for display

    return image

# Schedule the console output update
app.after(100, update_console_output)
app.after(100, update_images)

# Start the customtkinter main loop
app.mainloop()