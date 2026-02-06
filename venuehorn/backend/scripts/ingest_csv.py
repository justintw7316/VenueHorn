import argparse
import csv
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.vector_store import vector_store  # noqa: E402


FIELD_ORDER = [
    "Venue Holding Company",
    "Venue Brand",
    "Venue Name",
    "Venue Website",
    "Venue Description",
    "Venue Type",
    "Space Name",
    "Space Description",
    "Number of Spaces",
    "Total Number of Attendees",
    "Number of Meeting Rooms",
    "Space Type",
    "Space Location",
    "Total Space",
    "Space Catering",
    "Venue Email",
    "Venue Phone",
    "Venue Address",
    "Venue City",
    "Venue State",
    "Venue Zip Code",
]


def _row_to_text(row: dict) -> str:
    parts = []
    for field in FIELD_ORDER:
        value = (row.get(field) or "").strip()
        if value:
            parts.append(f"{field}: {value}")
    return "\n".join(parts)


def ingest_csv(path: Path) -> int:
    docs = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader, start=1):
            text = _row_to_text(row)
            if not text:
                continue
            venue_name = (row.get("Venue Name") or "").strip()
            source = f"{path.name}#row{idx}"
            if venue_name:
                source = f"{path.name}#row{idx}:{venue_name}"
            docs.append((text, source))

    return vector_store.add_documents(docs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a venues CSV into the vector index.")
    parser.add_argument("csv_path", type=Path, help="Path to the venues CSV file")
    args = parser.parse_args()

    if not args.csv_path.exists():
        raise SystemExit(f"CSV not found: {args.csv_path}")

    count = ingest_csv(args.csv_path)
    print(f"Chunks added: {count}")


if __name__ == "__main__":
    main()
