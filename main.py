import os
import tkinter as tk

from downloader import ScryfallDownloader
from services.card_collection import CardCollection
from services.sqlite_database import SQLiteCardDatabase
from ui.app import ScryfallApp

DATABASE_FILE = "scryfall_default_cards.jsonl"
COLLECTION_FILE = "my_collection.json"
SQLITE_FILE = "scryfall.db"


def display_app(
    input_filename: str = DATABASE_FILE,
    collection_filename: str = COLLECTION_FILE,
    db_path: str = SQLITE_FILE,
):
    if not os.path.exists(input_filename):
        print("Fajl nije pronađen. Započinjem prvobitno preuzimanje sa Scryfall-a...")

        downloader = ScryfallDownloader()

        if not downloader.download_and_extract(input_filename):
            print("Preuzimanje baze nije uspelo.")

    database = SQLiteCardDatabase(db_path=db_path, jsonl_path=input_filename)
    collection = CardCollection(collection_filename)

    root = tk.Tk()

    # Podigni prozor iznad ostalih, ali ne ostavljaj ga trajno "topmost".
    root.lift()
    root.attributes("-topmost", True)
    root.after_idle(root.attributes, "-topmost", False)

    ScryfallApp(root, database, collection)

    root.mainloop()


if __name__ == "__main__":
    display_app()
