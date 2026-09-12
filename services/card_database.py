import json
import os
from typing import List

from downloader import ScryfallDownloader
from models.card import Card


class CardDatabase:

    import json
from models.card import Card

class CardDatabase:
    def __init__(self, filepath):
        self.filepath = filepath
        self.cards = []

    def load_cards(self):
        self.cards = []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    card_data = json.loads(line)
                    
                    if Card.has_valid_price(card_data):
                        
                        card_obj = Card(card_data)
                        self.cards.append(card_obj)
                        
            print(f"Uspešno učitano {len(self.cards)} karata u bazu.")
        except Exception as e:
            print(f"Greška pri učitavanju baze: {e}")

    def update_from_scryfall(self) -> bool:

        downloader = ScryfallDownloader()
        success = downloader.download_and_extract(self.filename)

        if success:
            self.load_cards()

        return success

    def search(self, query: str) -> List[Card]:

        query_terms = query.strip().lower().split()

        if not query_terms:
            return self.cards

        return [card for card in self.cards if card.matches_query(query_terms)]