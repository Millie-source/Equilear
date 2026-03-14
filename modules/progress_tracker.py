# modules/progress_tracker.py
"""
Single shared instance — import PT from this module everywhere.
Never instantiate ProgressTracker() yourself; use the PT singleton.

JSON structure
──────────────
{
  "_streak": 3,
  "_last_played": "2026-03-14",
  "_total_stars": 12,

  "lesson_addition": {
    "best_streak":    10,     ← highest correct streak ever
    "correct_streak": 7,      ← current streak (resets on wrong)
    "total_attempts": 20,
    "total_correct":  15,
    "sessions":       3,      ← number of times lesson was opened
    "history": [{"correct": true, "ts": 123456}]
  },

  "letter_A": {
    "stage":    3,
    "attempts": 5,
    "history":  [{"stage":1,"accuracy":0.9,"ts":123456}]
  }
}

Mastery rules (used by progress screen)
────────────────────────────────────────
  Lesson mastered   = best_streak >= 10  OR  accuracy >= 80% over last 10 attempts
  Letter mastered   = stage >= 5 AND any stage-5 accuracy >= 0.80
  Lesson started    = total_attempts >= 1
  Letter started    = stage > 1  OR  any history exists
"""
import json, os, time, math
from datetime import date

DATA_DIR  = "data"
DATA_PATH = os.path.join(DATA_DIR, "progress.json")

# How many consecutive correct answers = mastered
MASTERY_STREAK = 10


class ProgressTracker:

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._data: dict = {}
        self._load()
        self._update_streak()

    # ── persistence ───────────────────────────────────────────────────────
    def _load(self):
        if os.path.exists(DATA_PATH):
            try:
                with open(DATA_PATH, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception as e:
                print(f"[Progress] Load failed: {e} — starting fresh")
                self._data = {}

    def _save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = DATA_PATH + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            # Atomic replace — avoids corrupt file on crash mid-write
            os.replace(tmp, DATA_PATH)
        except Exception as e:
            print(f"[Progress] Save failed: {e}")

    # ── streak ────────────────────────────────────────────────────────────
    def _update_streak(self):
        today = str(date.today())
        last  = self._data.get("_last_played", "")
        if last == today:
            return
        streak = self._data.get("_streak", 0)
        yesterday = str(date.fromordinal(date.today().toordinal() - 1))
        streak = streak + 1 if last == yesterday else 1
        self._data["_streak"]      = streak
        self._data["_last_played"] = today
        self._save()

    # ── lesson recording ──────────────────────────────────────────────────
    def record_lesson(self, lesson_id: str, correct: bool):
        key   = f"lesson_{lesson_id}"
        entry = self._data.setdefault(key, {
            "best_streak":    0,
            "correct_streak": 0,
            "total_attempts": 0,
            "total_correct":  0,
            "sessions":       0,
            "history":        [],
        })

        entry["total_attempts"] += 1
        if correct:
            entry["total_correct"]  += 1
            entry["correct_streak"] += 1
            # Track all-time best streak
            if entry["correct_streak"] > entry.get("best_streak", 0):
                entry["best_streak"] = entry["correct_streak"]
                # Award a star for each mastery milestone
                if entry["best_streak"] in (5, 10, 20):
                    self._data["_total_stars"] = \
                        self._data.get("_total_stars", 0) + 1
        else:
            entry["correct_streak"] = 0

        entry["history"].append({"correct": correct, "ts": time.time()})
        if len(entry["history"]) > 300:
            entry["history"] = entry["history"][-300:]

        self._save()

    def start_lesson(self, lesson_id: str):
        """Call when a lesson screen opens — increments session count."""
        key   = f"lesson_{lesson_id}"
        entry = self._data.setdefault(key, {
            "best_streak": 0, "correct_streak": 0,
            "total_attempts": 0, "total_correct": 0,
            "sessions": 0, "history": [],
        })
        entry["sessions"] = entry.get("sessions", 0) + 1
        self._save()

    def get_lesson(self, lesson_id: str) -> dict:
        return self._data.get(f"lesson_{lesson_id}", {
            "best_streak": 0, "correct_streak": 0,
            "total_attempts": 0, "total_correct": 0, "sessions": 0,
        })

    def lesson_status(self, lesson_id: str) -> str:
        """Returns 'mastered' | 'started' | 'untouched'"""
        entry = self.get_lesson(lesson_id)
        if entry["total_attempts"] == 0:
            return "untouched"
        # Mastered = best streak >= 10 OR ≥ 80% accuracy over all attempts
        if entry.get("best_streak", 0) >= MASTERY_STREAK:
            return "mastered"
        total = entry["total_attempts"]
        correct = entry["total_correct"]
        if total >= 10 and correct / total >= 0.80:
            return "mastered"
        return "started"

    # ── letter recording ──────────────────────────────────────────────────
    def record_letter(self, letter: str, stage: int, accuracy: float):
        key   = f"letter_{letter}"
        entry = self._data.setdefault(key, {"stage": 1, "attempts": 0,
                                             "history": []})
        entry["attempts"] = entry.get("attempts", 0) + 1
        entry["history"].append({
            "stage": stage, "accuracy": round(accuracy, 3),
            "ts": time.time(),
        })
        if len(entry["history"]) > 100:
            entry["history"] = entry["history"][-100:]
        self._save()

    def get_letter_stage(self, letter: str) -> int:
        return self._data.get(f"letter_{letter}", {}).get("stage", 1)

    def set_letter_stage(self, letter: str, stage: int):
        key = f"letter_{letter}"
        self._data.setdefault(key, {"stage": 1, "attempts": 0,
                                    "history": []})["stage"] = stage
        self._save()

    def letter_status(self, letter: str) -> str:
        """Returns 'mastered' | 'started' | 'untouched'"""
        key   = f"letter_{letter}"
        entry = self._data.get(key, {})
        hist  = entry.get("history", [])
        if not hist:
            return "untouched"
        stage = entry.get("stage", 1)
        if stage >= 5 and any(h.get("accuracy", 0) >= 0.80
                              for h in hist if h.get("stage", 0) >= 5):
            return "mastered"
        return "started"

    # ── global stats ──────────────────────────────────────────────────────
    @property
    def streak(self) -> int:
        return self._data.get("_streak", 0)

    @property
    def total_stars(self) -> int:
        return self._data.get("_total_stars", 0)

    def all_stats(self) -> dict:
        """Everything the progress screen needs in one call."""
        import string
        lessons = [
            "addition", "subtraction", "multiplication", "division",
            "counting", "odd_even", "fill_missing",
        ]
        shapes = ["shapes", "colors"]

        return {
            "streak":       self.streak,
            "total_stars":  self.total_stars,
            "letters":      {l: self.letter_status(l)
                             for l in string.ascii_uppercase},
            "lessons":      {l: self.lesson_status(l) for l in lessons},
            "shapes":       {l: self.lesson_status(l) for l in shapes},
            "lesson_detail":{l: self.get_lesson(l) for l in lessons + shapes},
        }


# ── Singleton — import this everywhere ───────────────────────────────────────
PT = ProgressTracker()
