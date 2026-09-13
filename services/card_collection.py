import bisect

from collection import CollectionStorage
from importer import match_cards_with_database, parse_card_list_text
from models.card import Card


class CardCollection:
    def __init__(self, filename: str = ""):
        self.filename = filename
        self.items: list[Card] = []

    def add_card(self, card: Card):

        card_qty = getattr(card, "quantity", 1)

        for item in self.items:
            if item == card:
                current_qty = getattr(item, "quantity", 1)
                item.quantity = current_qty + card_qty
                return

        if not hasattr(card, "quantity"):
            card.quantity = card_qty

        idx = bisect.bisect_left(self.items, card)
        self.items.insert(idx, card)

    def remove_card(self, card: Card):

        for item in self.items:
            if item == card:
                current_qty = getattr(item, "quantity", 1)

                if current_qty > 1:
                    item.quantity = current_qty - 1
                else:
                    self.items.remove(item)

                return

    def load(self, database, filename: str | None = None) -> list[Card]:

        target_filename = filename or self.filename
        raw_dict_cards = [card.to_dict() for card in database.cards]
        loaded_dicts = CollectionStorage.load_from_file(target_filename, raw_dict_cards)

        self.items = [Card(data, data.get("is_foil", False)) for data in loaded_dicts]
        self.items.sort()
        self.filename = target_filename

        return self.items

    def save(self, filename: str | None = None) -> tuple[bool, str]:

        target_filename = filename or self.filename
        dict_items = [card.to_dict() for card in self.items]
        result = CollectionStorage.save_to_file(dict_items, target_filename)

        if result[0]:
            self.filename = target_filename

        return result

    def import_from_text(self, raw_text: str, database) -> tuple[int, list[str]]:

        db_raw_dicts = [card.to_dict() for card in database.cards]
        parsed_items = parse_card_list_text(raw_text, db_raw_dicts)

        if not parsed_items:
            return 0, []

        formatted_items = []

        for item in parsed_items:
            if isinstance(item, dict):
                qty = item.get("quantity", item.get("qty", 1))
                name = item.get("name", "")
                set_code = item.get("set_code", item.get("set", ""))
                collector_number = item.get("collector_number", item.get("collector_num", ""))
                formatted_items.append((qty, name, set_code, collector_number))

            elif isinstance(item, (list, tuple)):
                formatted_items.append(tuple(item[:4]))

        result = match_cards_with_database(formatted_items, db_raw_dicts)

        if isinstance(result, tuple) and len(result) == 2:
            matched_dicts, unmatched = result
        else:
            matched_dicts = result
            unmatched = []

        for card_dict in matched_dicts:
            self.add_card(Card(card_dict))

        return len(matched_dicts), unmatched

    def get_total_value(self) -> float:
        return sum(card.price_numeric * card.quantity for card in self.items)

    def get_total_value_eur(self) -> float:
        total = 0.0
        for card in self.items:
            qty = getattr(card, "quantity", 1)
            # Proveravamo da li je foil ili obična i uzimamo odgovarajuću cenu
            if getattr(card, "is_foil", False):
                price = getattr(card, "price_foil_val", 0.0) or 0.0
            else:
                price = getattr(card, "price_normal_val", 0.0) or 0.0
            total += price * qty
        return total

    def get_total_value_rsd(self) -> int:

        return sum(card.price_rsd * card.quantity for card in self.items)

    def get_total_count(self) -> int:

        return sum(card.quantity for card in self.items)

    def get_normal_count(self) -> int:

        return sum(card.quantity for card in self.items if not card.is_foil)

    def get_foil_count(self) -> int:

        return sum(card.quantity for card in self.items if card.is_foil)

    def get_unique_count(self) -> int:

        return len({card.name.lower() for card in self.items})