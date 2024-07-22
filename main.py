import os
import requests
import pickle
import queue
import threading
import time
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import io
import random
from config import get_config_value
from dotenv import load_dotenv
from deepface import DeepFace
import numpy as np
import customtkinter
import sys
import dotenv
import auth
import train


# Variables globales para las IDs de los últimos perfiles
last_liked_id = None
last_passed_id = None

# Creación de colas seguras para subprocesos
console_queue = queue.Queue()
liked_image_queue = queue.Queue()
passed_image_queue = queue.Queue()

# Variable para controlar si el bot está corriendo
bot_running = False

def run_bot():
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
    global bot_running
    if bot_running:
        stop_event.set()
        bot_thread.join()
        bot_running = False
        stop_button.configure(state='disabled')
        run_button.configure(state='normal')
    else:
        print("The bot is not running.")

def update_console_output():
    while not console_queue.empty():
        message = console_queue.get_nowait()
        console_output.configure(state='normal')
        console_output.insert(tk.END, message + '\n')
        console_output.configure(state='disabled')
        console_output.yview(tk.END)
    app.after(100, update_console_output)

def update_images():
    while not liked_image_queue.empty():
        image_data = liked_image_queue.get_nowait()
        img = ImageTk.PhotoImage(image_data)
        liked_image_label.configure(image=img, text="")
        liked_image_label.image = img
    while not passed_image_queue.empty():
        image_data = passed_image_queue.get_nowait()
        img = ImageTk.PhotoImage(image_data)
        passed_image_label.configure(image=img, text="")
        passed_image_label.image = img
    app.after(100, update_images)

def custom_print(*args, **kwargs):
    message = ' '.join(map(str, args))
    console_queue.put(message)

def like_last_passed_profile():
    global last_passed_id
    if not last_passed_id:
        custom_print("No profile has been passed yet.")
        return
    custom_print("Liking the last passed profile...")
    URL = f"{API_URL}/like/{last_passed_id}"
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    return response.json()

def pass_last_liked_profile():
    global last_liked_id
    if not last_liked_id:
        custom_print("No profile has been liked yet.")
        return
    custom_print("Passing the last liked profile...")
    URL = f"{API_URL}/pass/{last_liked_id}"
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    return response.json()

def load_env_vars():
    if not os.path.exists('.env'):
        with open('.env', 'w') as file:
            file.write('TINDER_API_TOKEN=\n')
            file.write('TINDER_REFRESH_TOKEN=\n')
        raise FileNotFoundError(".env file created. Please add your TINDER_API_TOKEN.")
    
    load_dotenv()
    API_URL = get_config_value('API_URL')
    X_AUTH_TOKEN = os.getenv('TINDER_API_TOKEN')
    
    if not X_AUTH_TOKEN:
        raise ValueError("TINDER_API_TOKEN is missing in the .env file.")
    
    return API_URL, X_AUTH_TOKEN

sys.stdout.write = custom_print
sys.stderr.write = custom_print

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
app.geometry("1000x800")
app.title("Tinder Bot")

image_frame = customtkinter.CTkFrame(master=app)
image_frame.pack(pady=10)

liked_image_label = customtkinter.CTkLabel(master=image_frame, text="No image")
liked_image_label.grid(row=1, column=0, padx=10)

passed_image_label = customtkinter.CTkLabel(master=image_frame, text="No image")
passed_image_label.grid(row=1, column=1, padx=10)

liked_label = customtkinter.CTkLabel(master=image_frame, text="Last Liked")
liked_label.grid(row=0, column=0, padx=10)

passed_label = customtkinter.CTkLabel(master=image_frame, text="Last Passed")
passed_label.grid(row=0, column=1, padx=10)

button_frame = customtkinter.CTkFrame(master=app)
button_frame.pack(pady=10)

run_button = customtkinter.CTkButton(master=button_frame, text="Run Tinder Bot", command=run_bot)
run_button.grid(row=0, column=1, padx=10)

stop_button = customtkinter.CTkButton(master=button_frame, text="Stop Tinder Bot", command=stop_bot)
stop_button.grid(row=0, column=2, padx=10)

like_button = customtkinter.CTkButton(master=button_frame, text="Like last passed profile", command=lambda: like_last_passed_profile())
like_button.grid(row=0, column=3, padx=10)

pass_button = customtkinter.CTkButton(master=button_frame, text="Pass last liked profile", command=lambda: pass_last_liked_profile())
pass_button.grid(row=0, column=0, padx=10)

frame = customtkinter.CTkFrame(master=app)
frame.pack(pady=10, padx=10, fill="both", expand=True)

console_output = ScrolledText(frame, wrap=tk.WORD, state='disabled', bg="black", fg="white")
console_output.pack(fill="both", expand=True)

API_URL, auth_token = load_env_vars()
headers = {'X-Auth-Token': auth_token}

stop_event = threading.Event()

def check_api_connection(api_url, auth_token):
    URL = f"{api_url}/v2/profile"
    headers = {'X-Auth-Token': auth_token}
    
    while True:
        try:
            response = requests.get(URL, headers=headers)
            
            if response.status_code == 401:
                custom_print("Invalid AUTH Token. Please update the TINDER_API_TOKEN in the .env file.")
                auth.main()
                auth_token = os.getenv("TINDER_API_TOKEN")
                headers = {'X-Auth-Token': auth_token}
                break
            
            custom_print("Successfully connected to the Tinder API.")
            return response.json()
        
        except requests.RequestException as e:
            custom_print(f"An error occurred: {e}")
            time.sleep(5)

def like_profile(api_url, user_id, headers):
    global last_liked_id
    URL = f"{api_url}/like/{user_id}"
    last_liked_id = user_id
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    return response.json()

def pass_profile(api_url, user_id, headers):
    global last_passed_id
    URL = f"{api_url}/pass/{user_id}"
    last_passed_id = user_id
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    return response.json()

def like_to_you(api_url, headers):
    URL = f"{api_url}/v2/fast-match"
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    return response.json()

def get_recs(api_url, headers):
    URL = f"{api_url}/v2/recs/core"
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    return response.json()['data']['results']

def save_tokens_to_env(key, value):
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
    global model
    try:
        api_url, auth_token = load_env_vars()
    except (FileNotFoundError, ValueError) as e:
        custom_print(e)
        return

    try:
        check_api_connection(api_url, auth_token)
    except PermissionError as e:
        custom_print(e)
        return

    headers = {'X-Auth-Token': auth_token}

    if not os.path.exists('model.pkl'):
        train.train()
    else:
        custom_print("The model is already trained.")
        with open('model.pkl', 'rb') as file:
            model = pickle.load(file)
        
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
                            custom_print(f'The new image is classified as: {"Positive" if result == 1 else "Negative"}')
                            if result in (0, 1):
                                image_data = display_image(photo_url)
                                if result == 1:
                                    liked_image_queue.put(image_data)
                                else:
                                    passed_image_queue.put(image_data)
                                break
                    except Exception as e:
                        custom_print(f"Error processing image {photo_url}: {e}")
                        continue

                user_id = rec['user']['_id']
                if result == 1:
                    custom_print(f"User ID: {user_id}")
                    like_profile(api_url, user_id, headers)
                elif result == 0:
                    custom_print(f"User ID: {user_id}")
                    pass_profile(api_url, user_id, headers)
                    passed_image_queue.put(display_image(photo_urls[0]))
                else:
                    custom_print(f"No valid result for user ID: {user_id}, swiping left.")
                    pass_profile(api_url, user_id, headers)
                    passed_image_queue.put(display_image(photo_urls[0]))

                total_wait_time = random.randint(1, 5)
                elapsed_time = 0
                interval = 1
                custom_print(f"Waiting {total_wait_time} seconds...")
                while elapsed_time < total_wait_time and not stop_event.is_set():
                    time.sleep(interval)
                    elapsed_time += interval

def display_image(image_url):
    response = requests.get(image_url)
    image_data = response.content
    image = Image.open(io.BytesIO(image_data))
    image = image.resize((400, 400))
    return image

app.after(100, update_console_output)
app.after(100, update_images)

app.mainloop()