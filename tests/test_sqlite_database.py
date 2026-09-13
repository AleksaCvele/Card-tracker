import json

import pytest

from services.sqlite_database import SQLiteCardDatabase


@pytest.fixture
def jsonl_file(tmp_path, bolt_data, forest_data):
    """Mini Scryfall bulk fajl: dve validne karte, jedna bez cene, jedan smece-red."""
    priceless = {"name": "Ghost Card", "set_name": "Nowhere", "prices": {}}

    path = tmp_path / "bulk.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for row in (bolt_data, forest_data, priceless):
            f.write(json.dumps(row) + "\n")
        f.write("\n")
        f.write("{ not valid json\n")
    return path


@pytest.fixture
def db(tmp_path, jsonl_file):
    return SQLiteCardDatabase(db_path=str(tmp_path / "cards.db"), jsonl_path=str(jsonl_file))


def test_init_creates_the_database_file(tmp_path, jsonl_file):
    db_path = tmp_path / "cards.db"
    SQLiteCardDatabase(db_path=str(db_path), jsonl_path=str(jsonl_file))
    assert db_path.exists()


def test_load_imports_cards_from_jsonl(db):
    db.load_cards()
    assert sorted(c.name for c in db.cards) == ["Forest", "Lightning Bolt"]


def test_load_skips_priceless_cards(db):
    db.load_cards()
    assert "Ghost Card" not in [c.name for c in db.cards]


def test_load_survives_malformed_lines(db):
    """Neispravan JSON red ne sme da obori ucitavanje cele baze."""
    db.load_cards()
    assert len(db.cards) == 2


def test_second_load_reuses_the_index(db, jsonl_file):
    db.load_cards()
    jsonl_file.unlink()  # indeks je vec izgradjen, JSONL vise nije potreban

    db.load_cards()
    assert len(db.cards) == 2


def test_missing_jsonl_yields_an_empty_database(tmp_path):
    db = SQLiteCardDatabase(
        db_path=str(tmp_path / "cards.db"),
        jsonl_path=str(tmp_path / "ne-postoji.jsonl"),
    )
    db.load_cards()
    assert db.cards == []


def test_search_matches_substrings(db):
    db.load_cards()
    assert [c.name for c in db.search("light")] == ["Lightning Bolt"]


def test_search_requires_every_term(db):
    db.load_cards()
    assert db.search("lightning beta")
    assert db.search("lightning bloomburrow") == []


def test_empty_search_returns_everything(db):
    db.load_cards()
    assert len(db.search("   ")) == 2


def test_update_downloads_before_rebuilding(db, monkeypatch):
    """Regresija: update je ranije samo brisao indeks i citao isti fajl."""
    calls = []

    def fake_download(self, output_filename="scryfall_default_cards.jsonl"):
        calls.append(output_filename)
        return True

    monkeypatch.setattr(
        "services.sqlite_database.ScryfallDownloader.download_and_extract",
        fake_download,
    )

    assert db.update_from_scryfall() is True
    assert calls == [db.jsonl_path]


def test_update_fails_loudly_when_the_download_fails(db, monkeypatch):
    monkeypatch.setattr(
        "services.sqlite_database.ScryfallDownloader.download_and_extract",
        lambda self, output_filename="": False,
    )
    assert db.update_from_scryfall() is False
