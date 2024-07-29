import customtkinter as ctk
from PIL import Image
import io
import requests
import threading
from config import get_config_value

class ProfileWindow(ctk.CTkToplevel):
    def __init__(self, user_id, name, photos, bio, age, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.after(0, lambda:self.state('zoomed'))
        self.lift()

        self.title(f"Profile of {name}")

        self.user_id = user_id
        self.name = name
        self.photos = photos
        self.bio = bio
        self.age = age

        self.frame = ctk.CTkFrame(master=self)
        self.frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.name_label = ctk.CTkLabel(master=self.frame, text=str(self.name)+str(",") + str(self.age), font=("Arial", 24))
        self.name_label.pack(pady=10)

        self.photo_frame = ctk.CTkFrame(master=self.frame)
        self.photo_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.bio_frame = ctk.CTkFrame(master=self.frame)
        self.bio_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.bio_label = ctk.CTkLabel(master=self.bio_frame, text=self.bio, font=("Arial", 12))
        self.bio_label.pack(pady=10)
        
        self_botton_frame = ctk.CTkFrame(master=self.bio_frame)
        self_botton_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.pass_button = ctk.CTkButton(master=self_botton_frame, text="Pass", command=lambda: pass_profile(self.user_id, self.pass_button))
        self.pass_button.pack(pady=10, padx=10, side="left")
        

        self.load_photos()

    def load_photos(self):
        row = 0
        col = 0
        for photo_url in self.photos:
            threading.Thread(target=self.display_photo, args=(photo_url.get("url"), row, col), daemon=True).start()
            col += 1
            if col >= 5:
                col = 0
                row += 1

    def display_photo(self, photo_url, row, col):
        img = self.fetch_image(photo_url)
        if img:
            photo_label = ctk.CTkLabel(master=self.photo_frame, image=img, text="")
            photo_label.grid(row=row, column=col, padx=5, pady=5)
            photo_label.image = img  # Keep a reference to avoid garbage collection

    def fetch_image(self, url):
        try:
            response = requests.get(url)
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((200, 200))  # Resize image to fit in grid
            return ctk.CTkImage(light_image=image, dark_image=image, size=(200, 200))
        except Exception as e:
            return None
        
def pass_profile(user_id, button):
    button.configure(state="disabled")
    API_URL = get_config_value("api_url")
    URL = f"{API_URL}/pass/{user_id}"
    url = get_config_value("api_url") + "/pass_profile"
    # Add code here to pass the profile

def show_profile(user_id, name, photos,bio, age):
    ProfileWindow(user_id, name, photos,bio, age)