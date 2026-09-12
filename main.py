import os
import tkinter as tk

from downloader import ScryfallDownloader

from services.sqlite_database import SQLiteCardDatabase

from services.card_collection import CardCollection

from ui.app import ScryfallApp

DATABASE_FILE = "scryfall_default_cards.jsonl"

COLLECTION_FILE = "my_collection.json"

import threading

def load_database_background(database, on_complete_callback):
    """Učitava bazu u pozadinskoj niti da ne bi blokirala GUI."""
    def worker():
        try:
            database.load_cards()
            on_complete_callback(success=True)
        except Exception as e:
            print(f"Greška u pozadinskoj niti: {e}")
            on_complete_callback(success=False, error=str(e))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


def display_app(input_filename: str = DATABASE_FILE, collection_filename: str = COLLECTION_FILE):

    if not os.path.exists(input_filename):
        print(
            "Fajl nije pronađen. "
            "Započinjem prvobitno "
            "preuzimanje sa Scryfall-a..."
        )

        downloader = ScryfallDownloader()

        success = downloader.download_and_extract(input_filename)

        if not success:
            print("Preuzimanje baze nije uspelo.")


    database = SQLiteCardDatabase(db_path="scryfall.db", jsonl_path="scryfall_default_cards.jsonl")


    collection = CardCollection(collection_filename)

    root = tk.Tk()

    root.lift()

    root.attributes("-topmost",True)

    root.after_idle(root.attributes,"-topmost",False)

    ScryfallApp(root,database,collection)

    root.mainloop()

if __name__ == "__main__":

    display_app()