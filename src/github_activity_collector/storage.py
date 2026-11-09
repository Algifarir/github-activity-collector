import csv
import json
from pathlib import Path


class LocalStorage:
    """Storage seam: replace this adapter for SharePoint or Blob later."""
    def __init__(self, root: str | Path = "data"):
        self.root = Path(root)

    def save_json(self, category: str, name: str, payload: dict) -> Path:
        folder = self.root / category; folder.mkdir(parents=True, exist_ok=True)
        target = folder / name
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return target

    def save_csv(self, category: str, name: str, rows: list[dict]) -> Path:
        folder = self.root / category; folder.mkdir(parents=True, exist_ok=True)
        target = folder / name
        fields = sorted({key for row in rows for key in row}) or ["type"]
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore"); writer.writeheader(); writer.writerows(rows)
        return target

    def load_state(self) -> dict:
        target = self.root / "state" / "collection.json"
        return json.loads(target.read_text()) if target.exists() else {}

    def save_state(self, payload: dict) -> None:
        self.save_json("state", "collection.json", payload)
