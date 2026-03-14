# Touchless Tutor — Pygame Edition

## Setup

```bash
pip install -r requirements.txt
```

## Fonts (required for best appearance)

Download **Nunito** from Google Fonts:
https://fonts.google.com/specimen/Nunito

Place these files in  `assets/fonts/`:
- `Nunito-ExtraBold.ttf`
- `Nunito-SemiBold.ttf`
- `Nunito-Regular.ttf`

If the font files are missing the app falls back to Pygame's built-in font
automatically — it still works, just less polished.

## Project structure

```
main.py                         ← entry point
main_menu.py                    ← animated main menu
requirements.txt

assets/
  fonts/                        ← Nunito TTF files here
  sounds/
    correct.mp3
    wrong.mp3
    well_done.mp3
    welcome.mp3
  letters/                      ← A.png … Z.png  (grayscale outlines, 200×280)
  numbers/                      ← 0.png … 9.png

modules/
  ui/
    __init__.py
    renderer.py                 ← all drawing primitives
  gesture_engine.py             ← MediaPipe wrapper + HoldDetector
  sound_player.py               ← unchanged from original
  progress_tracker.py           ← JSON progress persistence

lessons/
  numbers/
    __init__.py
    addition.py                 ← complete ✅
    subtraction.py              ← coming soon
    multiplication.py           ← coming soon
    division.py                 ← coming soon
```

## Running

```bash
python main.py
```

## Gesture reference

| Gesture | Action |
|---|---|
| Index finger pointing | Move cursor |
| Thumb + index pinch | "Press" / hold to select |
| Hold pinch on button 1.2s | Confirm selection |
| Escape key | Back / quit (development shortcut) |

## Adding a new lesson

1. Create `lessons/your_module/your_lesson.py`
2. Define `run_your_lesson(screen, gesture_engine) -> str`
3. Add a card entry to `CARDS` in `main_menu.py`
4. Route it in `main.py`
