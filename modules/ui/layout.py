# modules/ui/layout.py
"""
Single source of truth for all screen dimensions.
Import L (the Layout singleton) anywhere after calling L.init(screen).

Coordinate model
────────────────
  Gestures  →  full screen  (0, 0) → (SW, SH)
              The hand can roam the whole window; no gesture zone clipping.

  UI margin →  20% inset on each side
              All cards, buttons, labels live inside this zone so the child
              never needs extreme wrist extension to reach a target.

  Scale     →  everything is authored at BASE 1024×640.
              L.s(px) converts a base-resolution pixel value to the actual
              screen size proportionally, so layouts look identical at any res.
"""

import pygame


class Layout:
    # Authoring resolution  (design is done at this size)
    BASE_W: int = 1024
    BASE_H: int = 640

    # Fraction of screen reserved as gesture-only border on each side
    # UI elements must not enter this zone
    MARGIN_FRAC: float = 0.20

    def __init__(self):
        self.sw: int   = self.BASE_W
        self.sh: int   = self.BASE_H
        self.sx: float = 1.0    # horizontal scale factor
        self.sy: float = 1.0    # vertical scale factor
        self._ready    = False

    def init(self, screen: pygame.Surface):
        """Call once after pygame.display.set_mode(). Reads actual size."""
        self.sw, self.sh = screen.get_size()
        self.sx = self.sw / self.BASE_W
        self.sy = self.sh / self.BASE_H
        self._ready = True

    # ── Coordinate helpers ─────────────────────────────────────────────────

    def s(self, px: int) -> int:
        """Scale a base-resolution pixel value (uses mean scale factor)."""
        return int(px * (self.sx + self.sy) / 2)

    def sx_(self, px: int) -> int:
        return int(px * self.sx)

    def sy_(self, px: int) -> int:
        return int(px * self.sy)

    # ── UI zone ────────────────────────────────────────────────────────────

    @property
    def margin_x(self) -> int:
        """Left / right pixel margin — UI must stay inward of this."""
        return int(self.sw * self.MARGIN_FRAC)

    @property
    def margin_y(self) -> int:
        """Top / bottom pixel margin."""
        return int(self.sh * self.MARGIN_FRAC)

    @property
    def ui_x(self) -> int:
        """Left edge of the UI zone."""
        return self.margin_x

    @property
    def ui_y(self) -> int:
        """Top edge of the UI zone."""
        return self.margin_y

    @property
    def ui_w(self) -> int:
        """Width of the UI zone."""
        return self.sw - self.margin_x * 2

    @property
    def ui_h(self) -> int:
        """Height of the UI zone."""
        return self.sh - self.margin_y * 2

    @property
    def ui_right(self) -> int:
        return self.ui_x + self.ui_w

    @property
    def ui_bottom(self) -> int:
        return self.ui_y + self.ui_h

    @property
    def cx(self) -> int:
        """Horizontal centre of screen."""
        return self.sw // 2

    @property
    def cy(self) -> int:
        """Vertical centre of screen."""
        return self.sh // 2

    # ── Font sizing ────────────────────────────────────────────────────────

    def font_size(self, base_pt: int) -> int:
        """Scale a font point size to the current resolution."""
        return max(10, int(base_pt * (self.sx + self.sy) / 2))

    # ── Card grid ──────────────────────────────────────────────────────────

    def card_grid(self, n_cards: int, cols: int,
                  gap_frac: float = 0.03) -> list[pygame.Rect]:
        """
        Return a list of Rects for n_cards laid out in `cols` columns,
        all inside the UI zone. Rows are calculated automatically.
        gap_frac = gap between cards as a fraction of ui_w.
        """
        rows     = (n_cards + cols - 1) // cols
        gap_x    = int(self.ui_w * gap_frac)
        gap_y    = int(self.ui_h * gap_frac * 1.2)
        card_w   = (self.ui_w - gap_x * (cols - 1)) // cols
        card_h   = (self.ui_h - gap_y * (rows - 1)) // rows

        # Reserve top portion for title  (30% of ui_h)
        title_h  = int(self.ui_h * 0.30)
        avail_h  = self.ui_h - title_h
        card_h   = (avail_h - gap_y * (rows - 1)) // rows
        grid_y   = self.ui_y + title_h

        rects = []
        for i in range(n_cards):
            col = i % cols
            row = i // cols
            x   = self.ui_x + col * (card_w + gap_x)
            y   = grid_y    + row * (card_h + gap_y)
            rects.append(pygame.Rect(x, y, card_w, card_h))
        return rects

    def __repr__(self):
        return (f"Layout({self.sw}×{self.sh}  "
                f"scale={self.sx:.2f}×{self.sy:.2f}  "
                f"UI zone={self.ui_x},{self.ui_y} "
                f"{self.ui_w}×{self.ui_h}  "
                f"margin={self.MARGIN_FRAC*100:.0f}%)")


# ── Singleton ──────────────────────────────────────────────────────────────
L = Layout()
