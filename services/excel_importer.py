
import openpyxl


class ExcelImporter:
    """Uvozi kolekciju iz Excel fajla."""

    NAME_KEYWORDS = ["naziv", "name", "kartica", "card", "title"]
    QUANTITY_KEYWORDS = ["količina", "kolicina", "qty", "count", "kom"]

    @classmethod
    def import_file(cls, file_path: str, database, collection) -> tuple[int, list[str]]:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))

        if not rows:
            return 0, []

        name_idx = -1
        qty_idx = -1
        start_row = 0

        for i, row in enumerate(rows[:10]):
            if not row:
                continue

            row_vals = [str(v).strip().lower() for v in row if v is not None]

            for j, val in enumerate(row_vals):
                if any(keyword in val for keyword in cls.NAME_KEYWORDS):
                    name_idx = j
                elif any(keyword in val for keyword in cls.QUANTITY_KEYWORDS):
                    qty_idx = j

            if name_idx != -1:
                start_row = i + 1
                break

        if name_idx == -1:
            name_idx = 0
            qty_idx = 1 if len(rows[0]) > 1 else -1
            start_row = 0

        db_lookup = {}

        for card in database.cards:
            clean_name = card.name.strip().lower()

            if clean_name not in db_lookup:
                db_lookup[clean_name] = card

        added_count = 0
        unmatched = []

        for row in rows[start_row:]:
            if not row or name_idx >= len(row) or row[name_idx] is None:
                continue

            raw_name = str(row[name_idx]).strip()

            if not raw_name:
                continue

            if raw_name.lower().startswith(("ukupno", "total", "naziv", "name")):
                continue

            qty = 1

            if qty_idx != -1 and qty_idx < len(row) and row[qty_idx] is not None:
                try:
                    qty = int(float(str(row[qty_idx]).strip()))
                except (ValueError, TypeError):
                    qty = 1

            if qty <= 0:
                continue

            clean_name = raw_name.lower()
            matched_card = db_lookup.get(clean_name)

            if not matched_card:
                clean_alpha = "".join(filter(str.isalnum, clean_name))

                for db_name, db_card in db_lookup.items():
                    db_alpha = "".join(filter(str.isalnum, db_name))

                    if db_alpha == clean_alpha:
                        matched_card = db_card
                        break

            if matched_card:
                new_card = matched_card.clone(is_foil=False, quantity=qty)
                collection.add_card(new_card)
                added_count += qty
            else:
                unmatched.append(f"{qty}x {raw_name}")

        return added_count, unmatched