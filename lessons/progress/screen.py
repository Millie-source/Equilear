# lessons/progress/screen.py
import pygame, math, random, time
from modules.ui.layout import L
from modules.ui.renderer import (
    Colors, Fonts, gradient_rect, glow_circle,
    draw_text_centered, draw_stars_bg, hold_ring,
    rounded_rect, particle_burst, draw_hand_skeleton,
)
from modules.gesture_engine import GestureEngine, HoldDetector
from modules.progress_tracker import PT

FPS = 60

# ── colour palette ────────────────────────────────────────────────────────────
C_MASTERED  = ( 50, 220, 100)
C_STARTED   = ( 50, 180, 255)
C_UNTOUCHED = ( 55,  50,  85)
C_GOLD      = (255, 210,  40)
C_PANEL_BG  = ( 22,  18,  44)


# ── drawing helpers ───────────────────────────────────────────────────────────
def _status_color(status: str) -> tuple:
    return {
        "mastered":  C_MASTERED,
        "started":   C_STARTED,
        "untouched": C_UNTOUCHED,
    }.get(status, C_UNTOUCHED)


def _draw_star(surface, cx, cy, r, color):
    pts = []
    for k in range(10):
        a      = math.radians(-90 + k * 36)
        radius = r if k % 2 == 0 else r * 0.42
        pts.append((int(cx + radius * math.cos(a)),
                    int(cy + radius * math.sin(a))))
    pygame.draw.polygon(surface, color, pts)


def _draw_flame(surface, cx, cy, size, t):
    for col, scale, speed, phase in [
        ((255,  80, 20), 1.0, 3.0, 0.0),
        ((255, 160, 20), 0.7, 4.0, 0.5),
        ((255, 240, 80), 0.4, 5.0, 1.0),
    ]:
        flicker = 0.85 + 0.15 * math.sin(t * speed + phase)
        w = int(size * scale * 0.6 * flicker)
        h = int(size * scale * flicker)
        pts = [(cx, cy-h),(cx-w, cy),(cx-w//2, cy-h//3),
               (cx, cy-h//2),(cx+w//2, cy-h//3),(cx+w, cy)]
        surf = pygame.Surface((size*3, size*3), pygame.SRCALPHA)
        shifted = [(x-cx+size, y-cy+size) for x, y in pts]
        pygame.draw.polygon(surf, (*col, 190), shifted)
        surface.blit(surf, (cx-size, cy-size))


def _accuracy_label(detail: dict) -> str:
    total   = detail.get("total_attempts", 0)
    correct = detail.get("total_correct", 0)
    if total == 0:
        return "—"
    pct = int(correct / total * 100)
    return f"{pct}%  ({correct}/{total})"


# ── panel drawing ─────────────────────────────────────────────────────────────
def _draw_panel(surface, rect: pygame.Rect, title: str,
                items: list[dict], detail: dict, t: float):
    """
    One subject panel.
    items  = [{"label": str, "status": str, "circle": bool}]
    detail = {lesson_id: get_lesson() dict}  — for tooltip stats
    """
    rounded_rect(surface, rect, C_PANEL_BG, radius=L.s(16),
                 border_color=(70, 60, 110), border_width=1)

    # Panel title
    draw_text_centered(surface, title,
                       Fonts.body(L.font_size(24)), Colors.TEXT_WHITE,
                       (rect.centerx, rect.y + L.s(26)))

    # Mastered count + mini bar
    n_mastered = sum(1 for it in items if it["status"] == "mastered")
    n_started  = sum(1 for it in items if it["status"] == "started")
    n_total    = len(items)

    count_txt = f"{n_mastered}/{n_total}  mastered"
    draw_text_centered(surface, count_txt,
                       Fonts.label(L.font_size(16)), Colors.TEXT_MUTED,
                       (rect.centerx, rect.y + L.s(48)))

    bar = pygame.Rect(rect.x + L.s(14), rect.y + L.s(58),
                      rect.w - L.s(28), L.s(7))
    pygame.draw.rect(surface, (40, 36, 70), bar, border_radius=L.s(4))
    if n_total:
        # mastered segment
        if n_mastered:
            fw = int(bar.w * n_mastered / n_total)
            pygame.draw.rect(surface, C_MASTERED,
                             pygame.Rect(bar.x, bar.y, fw, bar.h),
                             border_radius=L.s(4))
        # started segment
        if n_started:
            sw_ = int(bar.w * n_started / n_total)
            sx_ = bar.x + int(bar.w * n_mastered / n_total)
            started_surf = pygame.Surface((sw_, bar.h), pygame.SRCALPHA)
            pygame.draw.rect(started_surf, (*C_STARTED, 160),
                             started_surf.get_rect(), border_radius=L.s(4))
            surface.blit(started_surf, (sx_, bar.y))

    # ── item grid ─────────────────────────────────────────────────────────
    n     = len(items)
    if n == 0:
        return
    cols  = min(n, 9)
    rows  = math.ceil(n / cols)
    gap   = L.s(5)
    iw    = (rect.w - L.s(18) - gap * (cols - 1)) // cols
    ih    = iw
    gh    = rows * ih + (rows - 1) * gap
    avail_top = rect.y + L.s(72)
    avail_bot = rect.bottom - L.s(8)
    avail_h   = avail_bot - avail_top
    # If grid is taller than available, shrink items
    if gh > avail_h:
        ih = (avail_h - gap * (rows - 1)) // rows
        iw = ih
        gh = rows * ih + (rows - 1) * gap
    gy = avail_top + (avail_h - gh) // 2
    gx = rect.x + L.s(9)

    for i, item in enumerate(items):
        col = i % cols
        row = i // cols
        ix  = gx + col * (iw + gap)
        iy  = gy + row * (ih + gap)
        icx = ix + iw // 2
        icy = iy + ih // 2
        r   = max(4, iw // 2 - L.s(1))
        col_ = _status_color(item["status"])

        if item.get("circle", True):
            if item["status"] == "mastered":
                gc = pygame.Surface((r*2+8, r*2+8), pygame.SRCALPHA)
                pygame.draw.circle(gc, (*col_, 60), (r+4, r+4), r+4)
                surface.blit(gc, (icx-r-4, icy-r-4))
            pygame.draw.circle(surface, col_, (icx, icy), r)
            pygame.draw.circle(surface, (255,255,255), (icx,icy), r, 1)
            if item["status"] == "mastered":
                _draw_star(surface, icx+r-L.s(3), icy-r+L.s(3), L.s(6), C_GOLD)
            if iw >= L.s(24):
                lf = Fonts.label(L.font_size(13))
                tc = (15,15,15) if item["status"] != "untouched" else (120,110,160)
                draw_text_centered(surface, item["label"], lf, tc, (icx, icy))
        else:
            pill = pygame.Rect(ix, iy, iw, ih)
            rounded_rect(surface, pill, col_, radius=L.s(7))
            if item["status"] == "mastered":
                _draw_star(surface, pill.right-L.s(5), pill.y+L.s(5),
                           L.s(5), C_GOLD)
            if item["status"] != "untouched":
                d   = detail.get(item["id"], {})
                acc = _accuracy_label(d)
                draw_text_centered(surface, item["label"],
                                   Fonts.label(L.font_size(12)),
                                   (15,15,15), (icx, icy - L.s(6)))
                draw_text_centered(surface, acc,
                                   Fonts.label(L.font_size(10)),
                                   (10,10,10), (icx, icy + L.s(7)))
            else:
                draw_text_centered(surface, item["label"],
                                   Fonts.label(L.font_size(12)),
                                   (120,110,160), (icx, icy))


# ── main screen ───────────────────────────────────────────────────────────────
class ProgressScreen:

    NUMBER_LESSONS = ["addition", "subtraction", "multiplication",
                      "division", "counting", "odd_even", "fill_missing"]
    SHAPE_LESSONS  = ["shapes", "colors"]

    def __init__(self, ge: GestureEngine):
        self.ge        = ge
        self.back_hold = HoldDetector(1.5)
        self._clock    = pygame.time.Clock()
        self.t         = 0.0
        self.particles = []
        self.stars     = [(random.randint(0, L.sw), random.randint(0, L.sh),
                           random.randint(1, 2), random.uniform(0, 6.28))
                          for _ in range(80)]
        self._scroll_y = 0
        self._load_data()

    def _load_data(self):
        """Reload fresh from PT singleton every time screen opens."""
        stats = PT.all_stats()
        self._letter_st  = stats["letters"]
        self._num_st     = stats["lessons"]
        self._shape_st   = stats["shapes"]
        self._detail     = stats["lesson_detail"]
        self._streak     = stats["streak"]
        self._stars      = stats["total_stars"]

        self._total_mastered = (
            sum(1 for s in self._letter_st.values()  if s == "mastered") +
            sum(1 for s in self._num_st.values()     if s == "mastered") +
            sum(1 for s in self._shape_st.values()   if s == "mastered")
        )
        self._total_items = (
            len(self._letter_st) + len(self._num_st) + len(self._shape_st)
        )
        # Celebrate if anything mastered
        if self._total_mastered > 0:
            for _ in range(min(self._total_mastered, 5)):
                self.particles += self._emit_celebrate()

    def _emit_celebrate(self):
        cx = random.randint(L.ui_x, L.ui_right)
        cy = random.randint(L.ui_y, L.cy)
        color = random.choice([C_MASTERED, C_GOLD, Colors.CYAN, Colors.PURPLE])
        return [{"x": cx, "y": cy,
                 "vx": math.cos(a)*s, "vy": math.sin(a)*s - 100,
                 "life": random.uniform(0.8, 1.4),
                 "color": color,
                 "size": random.randint(L.s(4), L.s(10))}
                for a, s in [(random.uniform(0, math.pi*2),
                               random.uniform(60, 200))
                              for _ in range(10)]]

    def run(self, screen) -> str:
        # Always reload on entry so data is fresh
        self._load_data()

        while True:
            dt = self._clock.tick(FPS) / 1000.0
            self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:  return "back"
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return "back"

            gf    = self.ge.get()
            cx,cy = gf.cursor

            br = pygame.Rect(L.ui_x, L.ui_y, L.s(130), L.s(54))
            _, fired = self.back_hold.update(
                "back", br.collidepoint(cx, cy) and gf.is_pinching)
            if fired:
                return "back"

            self.particles = particle_burst(
                pygame.display.get_surface(), self.particles, dt)

            self._draw(screen, gf)
            pygame.display.flip()

    def _draw(self, screen, gf):
        screen.fill(Colors.BG_DEEP)

        # Nebula background
        for i, (bx,by,br,bc) in enumerate([
            (int(L.sw*.2), int(L.sh*.3), L.s(200), (50,15,130)),
            (int(L.sw*.8), int(L.sh*.7), L.s(180), (15,50,150)),
            (int(L.sw*.5), int(L.sh*.5), L.s(140), (70,15,70)),
        ]):
            ox = int(L.s(10)*math.sin(self.t*.3+i))
            oy = int(L.s(7)*math.cos(self.t*.25+i))
            bl = pygame.Surface((br*2, br*2), pygame.SRCALPHA)
            pygame.draw.circle(bl, (*bc, 25), (br,br), br)
            screen.blit(bl, (bx-br+ox, by-br+oy))

        draw_stars_bg(screen, self.stars, self.t)

        # Safe zone
        ov = pygame.Surface((L.sw, L.sh), pygame.SRCALPHA)
        pygame.draw.rect(ov,(255,255,255,12),
                         (L.ui_x,L.ui_y,L.ui_w,L.ui_h), border_radius=L.s(20))
        pygame.draw.rect(ov,(255,255,255,26),
                         (L.ui_x,L.ui_y,L.ui_w,L.ui_h),
                         width=1, border_radius=L.s(20))
        screen.blit(ov,(0,0))

        # Back button
        br   = pygame.Rect(L.ui_x, L.ui_y, L.s(130), L.s(54))
        ba   = br.collidepoint(*gf.cursor) and gf.is_pinching
        rounded_rect(screen, br,
                     Colors.BG_CARD_HOVER if ba else Colors.BG_CARD,
                     radius=L.s(14),
                     border_color=Colors.PURPLE_LIGHT if ba else None)
        draw_text_centered(screen, "← Back",
                           Fonts.body(L.font_size(24)), Colors.TEXT_LIGHT,
                           br.center)
        bst = self.back_hold._start.get("back")
        if bst:
            hold_ring(screen, br.center, L.s(28),
                      min((time.time()-bst)/1.5, 1.0), Colors.PURPLE_LIGHT)

        # Title
        y_title = L.ui_y + L.s(36)
        draw_text_centered(screen, "My Progress",
                           Fonts.title(L.font_size(50)), Colors.TEXT_WHITE,
                           (L.cx, y_title),
                           shadow=True, shadow_color=(50,25,110))

        # ── Overall bar ────────────────────────────────────────────────────
        bar_y  = y_title + L.s(44)
        bar_w  = int(L.ui_w * 0.55)
        bar_h  = L.s(14)
        bar_x  = L.cx - bar_w // 2
        bar_r  = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(screen, (44,38,74), bar_r, border_radius=L.s(7))
        if self._total_mastered and self._total_items:
            fw = int(bar_w * self._total_mastered / self._total_items)
            pygame.draw.rect(screen, C_MASTERED,
                             pygame.Rect(bar_x, bar_y, fw, bar_h),
                             border_radius=L.s(7))
        draw_text_centered(
            screen,
            f"{self._total_mastered} / {self._total_items} topics mastered",
            Fonts.label(L.font_size(18)), Colors.TEXT_MUTED,
            (L.cx, bar_y + bar_h + L.s(14)))

        # ── Streak & stars ─────────────────────────────────────────────────
        if self._streak > 0:
            sx = L.ui_right - L.s(70)
            sy = y_title
            _draw_flame(screen, sx, sy, L.s(28), self.t)
            draw_text_centered(screen, str(self._streak),
                               Fonts.title(L.font_size(30)), C_GOLD,
                               (sx, sy + L.s(34)))
            draw_text_centered(screen, "day streak",
                               Fonts.label(L.font_size(14)), Colors.TEXT_MUTED,
                               (sx, sy + L.s(50)))

        if self._stars > 0:
            stx = L.ui_right - L.s(140)
            sty = y_title + L.s(8)
            ef  = pygame.font.SysFont("Segoe UI Emoji", L.font_size(24))
            ss  = ef.render("⭐", True, C_GOLD)
            screen.blit(ss, ss.get_rect(center=(stx, sty)))
            draw_text_centered(screen, f"×{self._stars}",
                               Fonts.body(L.font_size(22)), C_GOLD,
                               (stx + L.s(22), sty))

        # ── Three panels ───────────────────────────────────────────────────
        panel_y = bar_y + bar_h + L.s(48)
        panel_h = L.ui_bottom - panel_y - L.s(8)
        gap     = L.s(14)
        panel_w = (L.ui_w - gap * 2) // 3

        # Letters panel
        letter_items = [
            {"label": lt, "status": self._letter_st[lt], "circle": True}
            for lt in sorted(self._letter_st)
        ]
        letters_rect = pygame.Rect(L.ui_x, panel_y, panel_w, panel_h)
        _draw_panel(screen, letters_rect, "Letters  🔤",
                    letter_items, {}, self.t)

        # Numbers panel
        num_labels = {
            "addition": "Add", "subtraction": "Sub",
            "multiplication": "Mul", "division": "Div",
            "counting": "Count", "odd_even": "Odd/Even",
            "fill_missing": "Fill",
        }
        num_items = [
            {"label": num_labels.get(l, l), "id": l,
             "status": self._num_st[l], "circle": False}
            for l in self.NUMBER_LESSONS
        ]
        nums_rect = pygame.Rect(L.ui_x + panel_w + gap, panel_y,
                                panel_w, panel_h)
        _draw_panel(screen, nums_rect, "Numbers  🔢",
                    num_items, self._detail, self.t)

        # Shapes panel
        shape_items = [
            {"label": l.title(), "id": l,
             "status": self._shape_st[l], "circle": False}
            for l in self.SHAPE_LESSONS
        ]
        shapes_rect = pygame.Rect(L.ui_x + (panel_w + gap)*2, panel_y,
                                  panel_w, panel_h)
        _draw_panel(screen, shapes_rect, "Shapes & Colors  🔷",
                    shape_items, self._detail, self.t)

        # ── Legend ─────────────────────────────────────────────────────────
        leg_y = L.ui_bottom - L.s(8)
        for color, label, lx in [
            (C_MASTERED,  "Mastered",    L.ui_x),
            (C_STARTED,   "In progress", L.ui_x + L.s(120)),
            (C_UNTOUCHED, "Not started", L.ui_x + L.s(260)),
        ]:
            pygame.draw.circle(screen, color, (lx+L.s(7), leg_y), L.s(6))
            draw_text_centered(screen, label,
                               Fonts.label(L.font_size(15)), Colors.TEXT_MUTED,
                               (lx + L.s(44), leg_y))

        self.particles = particle_burst(screen, self.particles, 0)

        # Cursor
        if gf.hand_visible:
            draw_hand_skeleton(screen, gf.landmarks, gf.is_pinching)
            pcx, pcy = gf.cursor
            if gf.is_pinching:
                glow_circle(screen, (pcx,pcy), L.s(14), Colors.CYAN, layers=3)
            else:
                pygame.draw.circle(screen, Colors.TEXT_WHITE, (pcx,pcy), L.s(10), 2)
                pygame.draw.circle(screen, Colors.CYAN, (pcx,pcy), L.s(4))


def run_progress(screen, ge: GestureEngine) -> str:
    return ProgressScreen(ge).run(screen)
