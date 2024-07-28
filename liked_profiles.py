from dotenv import load_dotenv
import requests
import os
import customtkinter as ctk
import threading
from config import get_config_value
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Configuration variables
API_URL = get_config_value('API_URL')
X_AUTH_TOKEN = os.getenv('TINDER_API_TOKEN')

# Lista global para almacenar los datos de los likes
all_likes = []

stop_event = threading.Event()

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

def fetch_all_likes():
    """Retrieve all likes sent by the user and store them globally."""
    global all_likes
    url = f"{API_URL}/v2/my-likes"
    likes = []
    page_token = None

    while not stop_event.is_set():
        # Update the URL with the page_token if it exists
        paginated_url = url if page_token is None else f"{url}?page_token={page_token}"

        try:
            response = requests.get(paginated_url, headers=get_headers())
            response.raise_for_status()
            response_json = response.json()
            results = response_json.get('data', {}).get('results', [])
            likes.extend(results)

            # Get the next page_token
            page_token = response_json.get('data', {}).get('page_token')

            # Break the loop if no more page_token
            if not page_token:
                break

        except requests.RequestException as e:
            print(f"Error: {e} and token: {X_AUTH_TOKEN}")
            break

    all_likes = likes

def fetch_and_display_like(like, image_frame, row, col):
    user = like.get('user', {})
    name = user.get('name')
    photos = user.get('photos', [])
    user_id = user.get('_id')
    if photos:
        photo_url = photos[0].get('url')
        print(f"User: {name}")
        print(f"User ID: {user_id}")
        print(f"Photo URL: {photo_url}")
        img = fetch_image(photo_url)
        if img:
            if not image_frame.winfo_exists():
                return
            profile_frame = ctk.CTkFrame(master=image_frame)
            profile_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            name_label = ctk.CTkLabel(master=profile_frame, text=name, anchor="w")
            name_label.pack(padx=5, pady=(5, 0))
            label = ctk.CTkLabel(master=profile_frame, text="")
            label.pack(padx=5, pady=(0, 5))
            button_frame = ctk.CTkFrame(master=profile_frame, fg_color="transparent")
            button_frame.pack(padx=5, pady=(0, 5))
            pass_button = ctk.CTkButton(master=button_frame, text="Pass", command=lambda user_id=user_id: pass_profile(user_id), fg_color="red")
            pass_button.grid(row=0, column=0, padx=5)
            see_more_button = ctk.CTkButton(master=button_frame, text="See profile", command=lambda photos=photos: see_more_photos(photos))
            see_more_button.grid(row=0, column=1, padx=5)
            label.image = img  # Keep a reference to avoid garbage collection
            label.configure(image=img)
        print("-----")

def start_like_thread(like, image_frame, row, col):
    threading.Thread(target=fetch_and_display_like, args=(like, image_frame, row, col), daemon=True).start()

def fetch_and_display_likes(image_frame, page_index=0, batch_size=8):
    global all_likes

    start_index = page_index * batch_size
    likes = all_likes[start_index:start_index + batch_size]

    if not likes:
        print("No likes found or an error occurred.")
    else:
        print(f"Total likes found: {len(likes)}")
        row = 0
        col = 0
        for like in likes:
            if stop_event.is_set():
                break
            start_like_thread(like, image_frame, row, col)
            col += 1
            if col >= 4:  # 4 columnas por fila
                col = 0
                row += 1

def start_likes_thread(image_frame, page_index=0, batch_size=8):
    global stop_event
    stop_event.clear()
    threading.Thread(target=fetch_and_display_likes, args=(image_frame, page_index, batch_size), daemon=True).start()

def fetch_image(url):
    try:
        response = requests.get(url)
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        image = image.resize((200, 200))  # Resize image to fit in grid
        return ctk.CTkImage(light_image=image, dark_image=image, size=(200, 200))
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None

def pass_profile(user_id):
    print(f"Passing user ID: {user_id}")
    headers = get_headers()
    URL = f"{API_URL}/pass/{user_id}"
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    print(response.json())

def see_more_photos(photos):
    print(f"Seeing more photos: {photos}")
    # Aquí puedes añadir la lógica para ver más fotos del perfil

class LikedProfilesWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("1000x800")
        self.title("Liked Profiles")

        self.page_index = 0
        self.batch_size = 8

        self.frame = ctk.CTkFrame(master=self)
        self.frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.image_frame = ctk.CTkFrame(master=self.frame)
        self.image_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.nav_frame = ctk.CTkFrame(master=self.frame)
        self.nav_frame.pack(pady=10)

        self.prev_button = ctk.CTkButton(master=self.nav_frame, text="Previous", command=self.load_previous_page)
        self.prev_button.grid(row=0, column=0, padx=5)

        self.next_button = ctk.CTkButton(master=self.nav_frame, text="Next", command=self.load_next_page)
        self.next_button.grid(row=0, column=1, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        fetch_all_likes()
        self.load_page(self.page_index)

    def load_page(self, page_index):
        for widget in self.image_frame.winfo_children():
            widget.destroy()
        self.page_index = page_index
        start_likes_thread(self.image_frame, page_index, self.batch_size)

    def load_previous_page(self):
        if self.page_index > 0:
            self.load_page(self.page_index - 1)

    def load_next_page(self):
        self.load_page(self.page_index + 1)

    def on_closing(self):
        global stop_event
        stop_event.set()
        self.destroy()

def main(is_main=False):
    app = LikedProfilesWindow()
    if is_main:
        app.mainloop()

if __name__ == "__main__":
    main(is_main=True)
