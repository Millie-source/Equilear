# main.py
import sys, os, pygame, cv2, random, math, time
sys.path.insert(0, os.path.dirname(__file__))

from modules.ui.layout import L
from modules.gesture_engine import GestureEngine, HoldDetector
from main_menu import run_main_menu
from lessons.numbers.addition import run_addition

TITLE = "Touchless Tutor"
FPS   = 60


def _loading_screen(screen, message):
    screen.fill((15, 12, 30))
    try:
        from modules.ui.renderer import Fonts, Colors, draw_text_centered
        draw_text_centered(screen, message,
                           Fonts.body(L.font_size(36)), Colors.TEXT_MUTED,
                           (L.cx, L.cy))
    except Exception:
        f = pygame.font.Font(None, 40)
        s = f.render(message, True, (180, 175, 210))
        screen.blit(s, s.get_rect(center=(L.cx, L.cy)))
    pygame.display.flip()


def _show_coming_soon(screen, ge, name):
    from modules.ui.renderer import (Colors, Fonts, draw_text_centered,
                                     draw_stars_bg, hold_ring, rounded_rect,
                                     glow_circle, draw_hand_skeleton)
    stars = [(random.randint(0, L.sw), random.randint(0, L.sh),
              random.randint(1, 2), random.uniform(0, 6.28))
             for _ in range(80)]
    hold  = HoldDetector(hold_seconds=1.5)
    clock = pygame.time.Clock()
    t     = 0.0

    # Back button centred horizontally, near bottom of UI zone
    btn_w, btn_h = L.s(200), L.s(60)
    back_rect = pygame.Rect(L.cx - btn_w // 2,
                            L.ui_bottom - btn_h - L.s(10),
                            btn_w, btn_h)

    while True:
        dt = clock.tick(FPS) / 1000.0
        t += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return

        gf  = ge.get()
        cx, cy = gf.cursor
        active = back_rect.collidepoint(cx, cy) and gf.is_pinching
        _, fired = hold.update("back", active)
        if fired: return

        screen.fill(Colors.BG_DEEP)
        draw_stars_bg(screen, stars, t)

        # Safe zone overlay
        _draw_safe_zone(screen)

        draw_text_centered(screen, name,
                           Fonts.title(L.font_size(64)), Colors.TEXT_WHITE,
                           (L.cx, L.cy - L.s(50)),
                           shadow=True, shadow_color=(60, 30, 120))
        draw_text_centered(screen, "Coming soon  🚀",
                           Fonts.body(L.font_size(34)), Colors.TEXT_MUTED,
                           (L.cx, L.cy + L.s(10)))

        rounded_rect(screen, back_rect, Colors.BG_CARD, radius=L.s(16),
                     border_color=Colors.PURPLE_LIGHT if active else None)
        draw_text_centered(screen, "← Back",
                           Fonts.body(L.font_size(28)), Colors.TEXT_LIGHT,
                           back_rect.center)
        st = hold._start.get("back")
        if st:
            p = min((time.time() - st) / 1.5, 1.0)
            hold_ring(screen, back_rect.center, L.s(36), p)

        if gf.hand_visible:
            draw_hand_skeleton(screen, gf.landmarks, gf.is_pinching)
            if gf.is_pinching:
                glow_circle(screen, (cx, cy), L.s(14), Colors.CYAN, layers=3)
            else:
                pygame.draw.circle(screen, Colors.TEXT_WHITE, (cx, cy), L.s(10), 2)
                pygame.draw.circle(screen, Colors.CYAN, (cx, cy), L.s(4))
        pygame.display.flip()


def _draw_safe_zone(screen):
    """Subtle visual hint showing where UI lives vs gesture margin."""
    from modules.ui.renderer import Colors
    # Gesture border — very faint outer strip to show what's "gesture only"
    border_surf = pygame.Surface((L.sw, L.sh), pygame.SRCALPHA)
    # Outer full-screen rect
    pygame.draw.rect(border_surf, (255, 255, 255, 8),
                     (0, 0, L.sw, L.sh))
    # Cut out the UI zone (make it slightly brighter)
    pygame.draw.rect(border_surf, (255, 255, 255, 14),
                     (L.ui_x, L.ui_y, L.ui_w, L.ui_h),
                     border_radius=L.s(20))
    # UI zone border line
    pygame.draw.rect(border_surf, (255, 255, 255, 30),
                     (L.ui_x, L.ui_y, L.ui_w, L.ui_h),
                     width=1, border_radius=L.s(20))
    screen.blit(border_surf, (0, 0))


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)

    # ── Detect screen resolution and go fullscreen ─────────────────────────
    info    = pygame.display.Info()
    sw, sh  = info.current_w, info.current_h
    # Windowed fullscreen (no mode switch, works on all displays)
    screen  = pygame.display.set_mode((sw, sh), pygame.NOFRAME)

    # Initialise the layout singleton — everything else reads from L
    L.init(screen)
    print(f"Display: {L}")

    _loading_screen(screen, "Starting camera…")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        _loading_screen(screen, "Camera not found — check your webcam.")
        pygame.time.wait(3000)
        pygame.quit()
        sys.exit(1)

    _loading_screen(screen, "Loading hand tracker…")
    # Gesture engine uses FULL screen dimensions — gestures work everywhere
    ge = GestureEngine(cap, screen_w=L.sw, screen_h=L.sh, mirror=True)
    _loading_screen(screen, "Ready!")
    pygame.time.wait(400)

    scene = "menu"
    while True:
        if scene == "menu":
            scene = run_main_menu(screen, ge)
        elif scene == "numbers":
            run_addition(screen, ge)
            scene = "menu"
        elif scene in ("letters", "shapes", "drawing", "progress"):
            labels = {"letters": "Letters", "shapes": "Shapes & Colors",
                      "drawing": "Drawing", "progress": "Progress"}
            _show_coming_soon(screen, ge, labels[scene])
            scene = "menu"
        elif scene == "quit" or scene is None:
            break
        else:
            scene = "menu"

    ge.stop()
    cap.release()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
