import re
from typing import Any

from collection import CollectionStorage


class CardImporter:
    """Parsira tekstualne liste kartica i uparuje ih sa bazom."""

    @staticmethod
    def parse_universal_line(line: str) -> tuple[int, str, str | None, str | None] | None:
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("//") or cleaned.startswith("#"):
            return None

        pattern_full = r"^(\d+)\s+(.+?)\s+\(([A-Za-z0-9]+)\)\s*([A-Za-z0-9\-]+)?"
        match = re.match(pattern_full, cleaned)
        if match:
            qty = int(match.group(1))
            name = match.group(2).strip()
            set_code = match.group(3).strip().lower()
            coll_num = match.group(4).strip() if match.group(4) else None
            return qty, name, set_code, coll_num

        pattern_simple = r"^(\d+)\s+(.+)"
        match_simple = re.match(pattern_simple, cleaned)
        if match_simple:
            qty = int(match_simple.group(1))
            name = match_simple.group(2).strip()
            return qty, name, None, None

        return 1, cleaned, None, None

    @staticmethod
    def match_cards_with_database(
        parsed_items: list[tuple[int, str, str | None, str | None]],
        all_cards_database: list[Any],
    ) -> tuple[list[Any], list[str]]:
        """Vraca (uparene karte, opisi onih koje nismo nasli)."""
        db_exact_map: dict[tuple[str, str, str], Any] = {}
        for card in all_cards_database:
            c_dict = card.to_dict() if hasattr(card, "to_dict") else card
            key = (
                c_dict.get("name", "").lower(),
                c_dict.get("set", "").lower(),
                str(c_dict.get("collector_number", "")),
            )
            if key not in db_exact_map:
                db_exact_map[key] = card

        db_cheapest_map = CollectionStorage._find_cheapest_versions_map(all_cards_database)

        matched_cards = []
        unmatched: list[str] = []

        for qty, name, set_code, coll_num in parsed_items:
            name_key = name.lower()
            found_card = None

            if set_code and coll_num:
                exact_key = (name_key, set_code.lower(), str(coll_num))
                found_card = db_exact_map.get(exact_key)

            if not found_card:
                found_card = db_cheapest_map.get(name_key)

            if found_card:
                matched_cards.append(CollectionStorage._with_quantity(found_card, qty))
            else:
                unmatched.append(f"{qty}x {name}")

        return matched_cards, unmatched

    @classmethod
    def parse_lines(cls, text_content: str) -> list[tuple[int, str, str | None, str | None]]:
        """Tekst -> (kolicina, ime, set, kolekcijski broj), bez diranja baze."""
        parsed_items = []
        for line in text_content.splitlines():
            item = cls.parse_universal_line(line)
            if item:
                parsed_items.append(item)
        return parsed_items

    @classmethod
    def parse_card_list_text(cls, text_content: str, all_cards_database: list[Any]) -> tuple[list[Any], list[str]]:
        return cls.match_cards_with_database(cls.parse_lines(text_content), all_cards_database)


def parse_universal_line(line: str):
    return CardImporter.parse_universal_line(line)


def parse_lines(text_content: str):
    return CardImporter.parse_lines(text_content)


def match_cards_with_database(parsed_items, all_cards_database):
    return CardImporter.match_cards_with_database(parsed_items, all_cards_database)


def parse_card_list_text(text_content: str, all_cards_database: list[Any]):
    return CardImporter.parse_card_list_text(text_content, all_cards_database)
