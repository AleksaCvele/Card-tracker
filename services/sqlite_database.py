import sqlite3
import os
import json
from typing import List
from models.card import Card

class SQLiteCardDatabase:
    def __init__(self, db_path="scryfall.db", jsonl_path="scryfall_default_cards.jsonl"):
        self.db_path = db_path
        self.jsonl_path = jsonl_path
        self.cards = []
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                set_name TEXT,
                set_code TEXT,
                collector_number TEXT,
                type_line TEXT,
                raw_json TEXT
            )
        """)

        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS cards_fts USING fts5(
                name, set_name, type_line, collector_number,
                content='cards', content_rowid='id'
            )
        """)
        
        conn.commit()
        conn.close()

    def load_cards(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM cards")
        count = cursor.fetchone()[0]

        if count == 0:
            if os.path.exists(self.jsonl_path):
                print(f"Pronađen JSONL fajl: {self.jsonl_path}. Inicijalizujem SQLite bazu...")
                batch = []
                with open(self.jsonl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            card_data = json.loads(line)
                            if Card.has_valid_price(card_data):
                                raw_json = json.dumps(card_data)
                                name = card_data.get("name", "")
                                set_name = card_data.get("set_name", "")
                                set_code = str(card_data.get("set", "")).lower()
                                col_num = str(card_data.get("collector_number", ""))
                                type_line = card_data.get("type_line", "")
                                
                                batch.append((name, set_name, set_code, col_num, type_line, raw_json))
                                
                                if len(batch) >= 5000:
                                    cursor.executemany(
                                        "INSERT INTO cards (name, set_name, set_code, collector_number, type_line, raw_json) VALUES (?, ?, ?, ?, ?, ?)",
                                        batch
                                    )
                                    conn.commit()
                                    batch = []
                        except Exception:
                            continue
                
                if batch:
                    cursor.executemany(
                        "INSERT INTO cards (name, set_name, set_code, collector_number, type_line, raw_json) VALUES (?, ?, ?, ?, ?, ?)",
                        batch
                    )
                    conn.commit()

                cursor.execute("INSERT INTO cards_fts(cards_fts) VALUES('rebuild')")
                conn.commit()
            else:
                print(f"GREŠKA: JSONL fajl '{self.jsonl_path}' nije pronađen u root folderu!")

        cursor.execute("SELECT raw_json FROM cards")
        rows = cursor.fetchall()
        conn.close()

        self.cards = []
        for row in rows:
            try:
                card_data = json.loads(row[0])
                self.cards.append(Card(card_data))
            except Exception:
                continue

        print(f"Uspešno učitano {len(self.cards)} karata iz SQLite baze.")

    def search(self, query: str) -> List[Card]:
        if not query.strip():
            return self.cards

        query_terms = query.lower().split()
        results = []
        
        for card in self.cards:
            if card.matches_query(query_terms):
                results.append(card)
        return results

    def update_from_scryfall(self) -> bool:
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            self._init_db()
            self.load_cards()
            return True
        except Exception as e:
            print(f"Greška pri ažuriranju SQLite baze: {e}")
            return False