# modules/progress_tracker.py
import json, os

SAVE_PATH = "data/progress.json"

class ProgressTracker:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(SAVE_PATH):
            with open(SAVE_PATH) as f:
                self._data = json.load(f)
        else:
            self._data = {}

    def _save(self):
        with open(SAVE_PATH, "w") as f:
            json.dump(self._data, f, indent=2)

    def record(self, symbol: str, stage: int, accuracy: float):
        entry = self._data.setdefault(symbol, {"stage": 1, "history": []})
        entry["history"].append({
            "stage": stage,
            "accuracy": round(accuracy, 3),
            "ts": __import__("time").time()
        })
        self._save()

    def get_stage(self, symbol: str) -> int:
        return self._data.get(symbol, {}).get("stage", 1)

    def set_stage(self, symbol: str, stage: int):
        self._data.setdefault(symbol, {})["stage"] = stage
        self._save()

    def get_history(self, symbol: str) -> list:
        return self._data.get(symbol, {}).get("history", [])

    def summary(self) -> dict:
        """Returns {symbol: latest_accuracy} for all practiced symbols."""
        out = {}
        for sym, entry in self._data.items():
            hist = entry.get("history", [])
            if hist:
                out[sym] = hist[-1]["accuracy"]
        return out