import sqlite3
import re
from datetime import datetime
import pandas as pd

DB_NAME = "english_classes.db"
EXCEL_FILE = "CursoInglesVaughan.xlsx"   # <-- change to your file name
SHEET_NAME = 0                # 0 = first sheet, or use sheet name like "Sheet1"


def parse_class_number(value):
    """Extract integer from strings like 'Clase 001' or numbers like 1."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError("Empty class number")
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip()
    m = re.search(r"(\d+)", s)
    if not m:
        raise ValueError(f"Cannot parse class number: {s!r}")
    return int(m.group(1))


def parse_date(value):
    """Convert '13/10/2026' (DD/MM/YYYY) or datetime cells to 'YYYY-MM-DD'."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError("Empty date")
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.strftime("%Y-%m-%d")
    s = str(value).strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {s!r}")


def migrate():
    # Read the Excel file (all columns as text so we control parsing)
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
    print(f"Read {len(df)} rows, columns: {list(df.columns)}")

    # Identify the two columns: first = class number, second = date
    if len(df.columns) < 2:
        raise SystemExit("Excel file must have at least 2 columns.")
    col_class, col_date = df.columns[0], df.columns[1]
    print(f"Using '{col_class}' as class number and '{col_date}' as date.")

    inserted, skipped = 0, 0

    with sqlite3.connect(DB_NAME) as conn:
        # Make sure the schema exists (matches the tracker app)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                class_number INTEGER NOT NULL,
                date_taken   TEXT NOT NULL,
                topic        TEXT,
                notes        TEXT,
                status       TEXT DEFAULT 'Pending'
            )
        """)

        for i, row in df.iterrows():
            raw_class = row[col_class]
            raw_date = row[col_date]

            # Skip completely empty rows
            if (pd.isna(raw_class) and pd.isna(raw_date)):
                continue

            try:
                cnum = parse_class_number(raw_class)
                dt = parse_date(raw_date)
            except ValueError as e:
                print(f"  Row {i+2} skipped: {e}  (class={raw_class!r}, date={raw_date!r})")
                skipped += 1
                continue

            # Skip duplicates (same class number AND same date)
            exists = conn.execute(
                "SELECT 1 FROM classes WHERE class_number=? AND date_taken=?",
                (cnum, dt),
            ).fetchone()
            if exists:
                print(f"  Row {i+2} duplicate: class #{cnum} on {dt} — skipped.")
                skipped += 1
                
                continue

            conn.execute(
                """INSERT INTO classes (class_number, date_taken, topic, notes, status)
                   VALUES (?, ?, '', '', 'Completed')""",
                (cnum, dt),
            )
            inserted += 1

        conn.commit()

    print(f"\n✅ Done. Inserted: {inserted}   Skipped: {skipped}   DB: {DB_NAME}")


if __name__ == "__main__":
    migrate()