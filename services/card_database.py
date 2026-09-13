import json

from downloader import ScryfallDownloader
from models.card import Card


class CardDatabase:
    """Ucitava Scryfall bazu direktno iz JSONL fajla (bez SQLite indeksa)."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.cards: list[Card] = []

    def load_cards(self) -> None:
        self.cards = []
        try:
            with open(self.filepath, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    card_data = json.loads(line)

                    if Card.has_valid_price(card_data):
                        self.cards.append(Card(card_data))

            print(f"Uspešno učitano {len(self.cards)} karata u bazu.")
        except Exception as e:
            print(f"Greška pri učitavanju baze: {e}")

    def update_from_scryfall(self) -> bool:
        downloader = ScryfallDownloader()
        success = downloader.download_and_extract(self.filepath)

        if success:
            self.load_cards()

        return success

    def search(self, query: str) -> list[Card]:
        query_terms = query.strip().lower().split()

        if not query_terms:
            return self.cards

        return [card for card in self.cards if card.matches_query(query_terms)]
