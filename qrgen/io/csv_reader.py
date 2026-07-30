import csv

from pathlib import Path

def read_csv(path: Path, column: str) -> list[str]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        idents = []
        for row in reader:
            val = row.get(column)
            if not val:
                continue
            val = val.strip()
            if val:
                idents.append(val)
    return idents

def read_headers(path: Path) -> list[str]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames