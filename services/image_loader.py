import os
import threading
import urllib.request

from PIL import Image, ImageTk


class ImageLoader:
    _cache_dir = "image_cache"

    @classmethod
    def _ensure_cache_dir(cls):
        if not os.path.exists(cls._cache_dir):
            os.makedirs(cls._cache_dir)

    @classmethod
    def load_card_image(cls, image_url: str, callback, size=(200, 280)):

        if not image_url:
            return

        cls._ensure_cache_dir()
        
        filename = image_url.split("/")[-1].split("?")[0]
        if not filename.endswith(".jpg"):
            filename += ".jpg"
        local_path = os.path.join(cls._cache_dir, filename)

        def worker():
            try:
                if not os.path.exists(local_path):
                    req = urllib.request.Request(
                        image_url, 
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    with urllib.request.urlopen(req) as response:
                        with open(local_path, 'wb') as f:
                            f.write(response.read())

                pil_img = Image.open(local_path)
                pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)
                photo_img = ImageTk.PhotoImage(pil_img)

                if callback:
                    callback(photo_img, local_path)

            except Exception as e:
                print(f"Greška pri učitavanju slike ({image_url}): {e}")

        threading.Thread(target=worker, daemon=True).start()