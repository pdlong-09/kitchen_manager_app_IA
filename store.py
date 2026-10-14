from __future__ import annotations
import csv
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

HEADERS = ["item_id", "name", "item_type", "category", "quantity", "unit", "location_code", "expiry_date",
           "low_stock_level", "restock_date", "notes"]
FIELDS = HEADERS[1:]

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    item_type       TEXT    NOT NULL DEFAULT '',
    category        TEXT    NOT NULL,
    quantity        REAL    NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    unit            TEXT    NOT NULL,
    location_code   TEXT    NOT NULL,
    expiry_date     TEXT    NOT NULL DEFAULT '',
    low_stock_level REAL    NOT NULL DEFAULT 0 CHECK (low_stock_level >= 0),
    restock_date    TEXT    NOT NULL DEFAULT '',
    notes           TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_items_location ON items (location_code);
CREATE INDEX IF NOT EXISTS idx_items_name ON items (name);
"""

@dataclass
class Item:
    item_id: int
    name: str
    item_type: str
    category: str
    quantity: float
    unit: str
    location_code: str
    expiry_date: str
    low_stock_level: float
    restock_date: str
    notes: str

class SQLiteItemStore:
    def __init__(self, db_path: Path, csv_path: Path | None = None) -> None:
        self.db_path = Path(db_path)
        self.csv_path = Path(csv_path) if csv_path else None
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.commit()
        if self.is_empty() and self.csv_path and self.csv_path.exists():
            self.import_csv(self.csv_path)

    def is_empty(self) -> bool:
        return self.connection.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0

    @staticmethod
    def _to_item(row: sqlite3.Row) -> Item:
        return Item(**dict(row))

    @staticmethod
    def _clean(item_data: dict) -> dict:
        cleaned = {}
        for field in FIELDS:
            value = item_data.get(field) or ""
            if field in ("quantity", "low_stock_level"):
                cleaned[field] = float(value or 0)
            elif field == "location_code":
                cleaned[field] = str(value).strip().upper()
            else:
                cleaned[field] = str(value).strip()
        return cleaned

    def _insert(self, item_data: dict) -> int:
        values = self._clean(item_data)
        sql = f"INSERT INTO items ({', '.join(FIELDS)}) VALUES ({', '.join('?' * len(FIELDS))})"
        return self.connection.execute(sql, [values[field] for field in FIELDS]).lastrowid

    def get_items(self, search: str = "") -> list[Item]:
        search = search.strip()
        if search:
            pattern = f"%{search}%"
            rows = self.connection.execute(
                """
                SELECT * FROM items
                 WHERE name          LIKE ? COLLATE NOCASE
                    OR category      LIKE ? COLLATE NOCASE
                    OR item_type     LIKE ? COLLATE NOCASE
                    OR location_code LIKE ? COLLATE NOCASE
                 ORDER BY name COLLATE NOCASE
                """,
                (pattern, pattern, pattern, pattern),
            ).fetchall()
        else:
            rows = self.connection.execute("SELECT * FROM items ORDER BY name COLLATE NOCASE").fetchall()
        return [self._to_item(row) for row in rows]

    def get_item(self, item_id: int) -> Item | None:
        row = self.connection.execute("SELECT * FROM items WHERE item_id = ?", (item_id,)).fetchone()
        return self._to_item(row) if row else None

    def get_items_at_location(self, location_code: str) -> list[Item]:
        rows = self.connection.execute("SELECT * FROM items WHERE location_code = ? COLLATE NOCASE ORDER BY name COLLATE NOCASE",
                                       (location_code.upper(),)).fetchall()
        return [self._to_item(row) for row in rows]

    def find_location_for_search(self, text: str, valid_codes: set[str]) -> str | None:
        search = text.strip()
        if search.upper() in valid_codes:
            return search.upper()
        pattern = f"%{search}%"
        row = self.connection.execute(
            """
            SELECT location_code FROM items
             WHERE name     LIKE ? COLLATE NOCASE   -- ? placeholders: user text is data, never SQL
                OR category LIKE ? COLLATE NOCASE
             ORDER BY name COLLATE NOCASE
             LIMIT 1
            """,
            (pattern, pattern),
        ).fetchone()
        return row["location_code"].upper() if row else None

    def add_item(self, item_data: dict) -> Item:
        with self.connection:
            item_id = self._insert(item_data)
        self._mirror_to_csv()
        return self.get_item(item_id)

    def update_item(self, item_id: int, item_data: dict) -> Item | None:
        if self.get_item(item_id) is None:
            return None
        values = self._clean(item_data)
        assignments = ", ".join(f"{field} = ?" for field in FIELDS)
        with self.connection:
            self.connection.execute(f"UPDATE items SET {assignments} WHERE item_id = ?",
                                    [values[field] for field in FIELDS] + [item_id])
        self._mirror_to_csv()
        return self.get_item(item_id)

    def update_quantity(self, item_id: int, new_quantity: float) -> None:
        with self.connection:
            self.connection.execute("UPDATE items SET quantity = ? WHERE item_id = ?", (max(0.0, float(new_quantity)), item_id))
        self._mirror_to_csv()

    def delete_item(self, item_id: int) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
        self._mirror_to_csv()

    def import_csv(self, path: Path) -> int:
        with Path(path).open("r", newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        added = 0
        with self.connection:
            for line, row in enumerate(rows, start=2):
                # a broken row gets skipped so the rest still loads
                try:
                    self._insert(row)
                    added += 1
                except (ValueError, sqlite3.IntegrityError) as error:
                    print(f"[store] skipped row {line} of {Path(path).name}: {error}", file=sys.stderr)
        return added

    def export_csv(self, path: Path) -> int:
        items = sorted(self.get_items(), key=lambda item: item.item_id)
        with Path(path).open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows(asdict(item) for item in items)
        return len(items)

    def _mirror_to_csv(self) -> None:
        if self.csv_path:
            self.export_csv(self.csv_path)

    def close(self) -> None:
        self.connection.close()
