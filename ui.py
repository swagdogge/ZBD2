"""
ui.py — All UI panels and overlays
=====================================
InfoPanel    — left side: selected tower details + money
ShopPanel    — right side: buy towers
VillagePanel — bottom: village status + upgrades
EscapeMenu   — pause / save / settings overlay
"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    LEFT_PANEL_WIDTH, RIGHT_PANEL_WIDTH, BOTTOM_PANEL_HEIGHT,
    GRID_X, GRID_Y, GRID_WIDTH, GRID_HEIGHT,
    SHOP_COLS, SHOP_CELL_SIZE,
    C_PANEL_BG, C_PANEL_BORDER, C_TEXT, C_TEXT_DIM, C_ACCENT,
    C_DANGER, C_HIGHLIGHT, C_BUTTON, C_BUTTON_HOVER,
    C_SHOP_HOVER, C_SHOP_SELECTED,
    TOWER_TEMPLATES, VILLAGE_UPGRADES,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _draw_panel(surface, rect, border=True):
    pygame.draw.rect(surface, C_PANEL_BG, rect)
    if border:
        pygame.draw.rect(surface, C_PANEL_BORDER, rect, 1)


def _text(surface, txt, x, y, font, color=C_TEXT, max_width=None):
    """Render text with optional word-wrap."""
    if max_width is None:
        surf = font.render(txt, True, color)
        surface.blit(surf, (x, y))
        return y + surf.get_height() + 2

    words = txt.split()
    line, lines = [], []
    for w in words:
        test = " ".join(line + [w])
        if font.size(test)[0] <= max_width:
            line.append(w)
        else:
            if line:
                lines.append(" ".join(line))
            line = [w]
    if line:
        lines.append(" ".join(line))

    for l in lines:
        surf = font.render(l, True, color)
        surface.blit(surf, (x, y))
        y += surf.get_height() + 2
    return y


def _health_bar(surface, x, y, w, h, ratio, bg=(40, 40, 40)):
    pygame.draw.rect(surface, bg, (x, y, w, h))
    color = C_ACCENT if ratio > 0.5 else C_DANGER
    pygame.draw.rect(surface, color, (x, y, int(w * ratio), h))
    pygame.draw.rect(surface, C_PANEL_BORDER, (x, y, w, h), 1)


# ── Fonts (loaded once) ───────────────────────────────────────────────────────

pygame.font.init()
FONT_TITLE  = pygame.font.SysFont("monospace", 15, bold=True)
FONT_BODY   = pygame.font.SysFont("monospace", 12)
FONT_SMALL  = pygame.font.SysFont("monospace", 11)
FONT_BIG    = pygame.font.SysFont("monospace", 22, bold=True)


# ── InfoPanel ────────────────────────────────────────────────────────────────

class InfoPanel:
    """Left panel — shows selected tower info and player money."""

    RECT = pygame.Rect(0, 0, LEFT_PANEL_WIDTH, SCREEN_HEIGHT - BOTTOM_PANEL_HEIGHT)

    def draw(self, surface: pygame.Surface, selected_tower, money: int,
             wave_number: int, seconds_until_wave: float) -> None:
        _draw_panel(surface, self.RECT)
        pad = 10
        x = pad
        y = pad

        # ── Money ──
        y = _text(surface, "MONEY", x, y, FONT_TITLE, C_TEXT_DIM)
        money_surf = FONT_BIG.render(f"${money}", True, C_ACCENT)
        surface.blit(money_surf, (x, y))
        y += money_surf.get_height() + 10

        # ── Wave info ──
        y = _text(surface, f"Wave  {wave_number}", x, y, FONT_TITLE, C_TEXT_DIM)
        if seconds_until_wave > 0:
            y = _text(surface, f"Next in {seconds_until_wave:.1f}s", x, y, FONT_BODY, C_TEXT_DIM)
        y += 8

        pygame.draw.line(surface, C_PANEL_BORDER,
                         (x, y), (LEFT_PANEL_WIDTH - x, y))
        y += 8

        # ── Selected tower ──
        if selected_tower is None:
            _text(surface, "Click a tower", x, y, FONT_BODY, C_TEXT_DIM)
            return

        y = _text(surface, "SELECTED", x, y, FONT_TITLE, C_TEXT_DIM)
        y = _text(surface, selected_tower.name, x, y, FONT_TITLE, C_HIGHLIGHT)
        y += 4

        # Health bar
        w = LEFT_PANEL_WIDTH - 2 * pad
        _health_bar(surface, x, y, w, 10,
                    selected_tower.health / selected_tower.max_health)
        y += 14
        y = _text(surface, f"HP: {selected_tower.health}/{selected_tower.max_health}",
                  x, y, FONT_SMALL, C_TEXT_DIM)

        # Stats
        if selected_tower.fire_rate > 0:
            y = _text(surface, f"Rate:   {selected_tower.fire_rate:.1f}/s",
                      x, y, FONT_BODY)
            y = _text(surface, f"Dmg:    {selected_tower.damage}",
                      x, y, FONT_BODY)
            y = _text(surface, f"Range:  {selected_tower.range} cells",
                      x, y, FONT_BODY)
        else:
            y = _text(surface, "(passive)", x, y, FONT_BODY, C_TEXT_DIM)

        y += 6
        pygame.draw.line(surface, C_PANEL_BORDER,
                         (x, y), (LEFT_PANEL_WIDTH - x, y))
        y += 6

        # Description
        _text(surface, selected_tower.description,
              x, y, FONT_SMALL, C_TEXT_DIM,
              max_width=LEFT_PANEL_WIDTH - 2 * pad)


# ── ShopPanel ────────────────────────────────────────────────────────────────

class ShopPanel:
    """Right panel — tower purchase grid."""

    RECT = pygame.Rect(
        SCREEN_WIDTH - RIGHT_PANEL_WIDTH, 0,
        RIGHT_PANEL_WIDTH, SCREEN_HEIGHT - BOTTOM_PANEL_HEIGHT
    )

    def __init__(self):
        # Ordered list of tower keys for consistent rendering
        self.tower_keys = list(TOWER_TEMPLATES.keys())
        self.selected_key: str | None = None
        self._hover_key:   str | None = None

        # Build cell rects
        self._cells: dict[str, pygame.Rect] = {}
        self._rebuild_cells()

    def _rebuild_cells(self):
        pad = 10
        cell_w = SHOP_CELL_SIZE
        cell_h = SHOP_CELL_SIZE
        for i, key in enumerate(self.tower_keys):
            col = i % SHOP_COLS
            row = i // SHOP_COLS
            x = self.RECT.x + pad + col * (cell_w + 4)
            y = self.RECT.y + 40 + row * (cell_h + 4)
            self._cells[key] = pygame.Rect(x, y, cell_w, cell_h)

    def handle_click(self, mx: int, my: int) -> str | None:
        """Return tower key if a shop cell was clicked, else None."""
        for key, rect in self._cells.items():
            if rect.collidepoint(mx, my):
                self.selected_key = key if self.selected_key != key else None
                return self.selected_key
        return None

    def update_hover(self, mx: int, my: int) -> None:
        self._hover_key = None
        for key, rect in self._cells.items():
            if rect.collidepoint(mx, my):
                self._hover_key = key

    def draw(self, surface: pygame.Surface, money: int, village) -> None:
        _draw_panel(surface, self.RECT)
        x = self.RECT.x + 10
        y = self.RECT.y + 8
        _text(surface, "SHOP", x, y, FONT_TITLE, C_TEXT_DIM)

        for key, rect in self._cells.items():
            tmpl = TOWER_TEMPLATES[key]
            cost = village.effective_cost(tmpl["cost"])

            # Background
            if key == self.selected_key:
                bg = C_SHOP_SELECTED
            elif key == self._hover_key:
                bg = C_SHOP_HOVER
            else:
                bg = (30, 42, 58)

            pygame.draw.rect(surface, bg, rect, border_radius=4)
            pygame.draw.rect(surface, C_PANEL_BORDER, rect, 1, border_radius=4)

            # Tower color swatch
            swatch = pygame.Rect(rect.x + 4, rect.y + 4, 18, 18)
            pygame.draw.rect(surface, tmpl["color"], swatch, border_radius=3)

            # Name
            name_surf = FONT_SMALL.render(tmpl["name"], True, C_TEXT)
            surface.blit(name_surf, (rect.x + 26, rect.y + 5))

            # Cost
            can_afford = money >= cost
            cost_color = C_ACCENT if can_afford else C_DANGER
            cost_surf  = FONT_SMALL.render(f"${cost}", True, cost_color)
            surface.blit(cost_surf, (rect.x + 26, rect.y + 18))

        # Hint
        hint_y = self.RECT.bottom - 30
        _text(surface, "Click grid to place", self.RECT.x + 6,
              hint_y, FONT_SMALL, C_TEXT_DIM)


# ── VillagePanel ─────────────────────────────────────────────────────────────

class VillagePanel:
    """Bottom panel — village health, upgrades."""

    RECT = pygame.Rect(
        0, SCREEN_HEIGHT - BOTTOM_PANEL_HEIGHT,
        SCREEN_WIDTH, BOTTOM_PANEL_HEIGHT
    )

    def __init__(self):
        self._upgrade_rects: list[pygame.Rect] = []
        self._hover_idx: int | None = None

    def handle_click(self, mx: int, my: int, money: int, village) -> int:
        """
        Try to purchase a village upgrade.
        Returns amount spent (0 if nothing purchased).
        """
        for i, rect in enumerate(self._upgrade_rects):
            if rect.collidepoint(mx, my):
                upg = VILLAGE_UPGRADES[i]
                if upg["name"] not in village.upgrades_applied and money >= upg["cost"]:
                    village.apply_upgrade(upg)
                    return upg["cost"]
        return 0

    def update_hover(self, mx: int, my: int) -> None:
        self._hover_idx = None
        for i, rect in enumerate(self._upgrade_rects):
            if rect.collidepoint(mx, my):
                self._hover_idx = i

    def draw(self, surface: pygame.Surface, village, money: int) -> None:
        _draw_panel(surface, self.RECT)
        pad = 12
        x   = pad
        y   = self.RECT.y + pad

        # Village name + health
        _text(surface, "YOUR VILLAGE", x, y, FONT_TITLE, C_TEXT_DIM)
        y += 18
        bar_w = 200
        ratio = village.health / village.max_health
        _health_bar(surface, x, y, bar_w, 12, ratio)
        y += 14
        _text(surface, f"HP: {village.health} / {village.max_health}", x, y, FONT_SMALL, C_TEXT)

        # Upgrades
        self._upgrade_rects = []
        btn_x = 260
        btn_y = self.RECT.y + 10
        btn_w = 160
        btn_h = 38

        for i, upg in enumerate(VILLAGE_UPGRADES):
            rect = pygame.Rect(btn_x + i * (btn_w + 8), btn_y, btn_w, btn_h)
            self._upgrade_rects.append(rect)

            purchased = upg["name"] in village.upgrades_applied
            can_buy   = not purchased and money >= upg["cost"]

            if purchased:
                bg = (30, 60, 40)
                border = C_ACCENT
            elif self._hover_idx == i and can_buy:
                bg = C_BUTTON_HOVER
                border = C_HIGHLIGHT
            else:
                bg = C_BUTTON
                border = C_PANEL_BORDER

            pygame.draw.rect(surface, bg, rect, border_radius=5)
            pygame.draw.rect(surface, border, rect, 1, border_radius=5)

            label_color = C_TEXT if can_buy or purchased else C_TEXT_DIM
            _text(surface, upg["name"], rect.x + 6, rect.y + 5, FONT_SMALL, label_color)

            if purchased:
                _text(surface, "✓ Purchased", rect.x + 6, rect.y + 20, FONT_SMALL, C_ACCENT)
            else:
                cost_c = C_ACCENT if can_buy else C_DANGER
                _text(surface, f"${upg['cost']}", rect.x + 6, rect.y + 20, FONT_SMALL, cost_c)


# ── EscapeMenu ────────────────────────────────────────────────────────────────

class EscapeMenu:
    """Pause / save / settings overlay triggered by Escape."""

    _BUTTONS = ["Resume", "Save Game", "Settings", "Quit"]
    BTN_W, BTN_H = 220, 44
    _overlay_color = (0, 0, 0, 160)

    def __init__(self):
        self.visible = False
        self._hover_idx: int | None = None
        self._rects: list[pygame.Rect] = []

    def toggle(self) -> None:
        self.visible = not self.visible

    def handle_click(self, mx: int, my: int) -> str | None:
        """Return button label if clicked, else None."""
        if not self.visible:
            return None
        for i, rect in enumerate(self._rects):
            if rect.collidepoint(mx, my):
                return self._BUTTONS[i]
        return None

    def update_hover(self, mx: int, my: int) -> None:
        if not self.visible:
            return
        self._hover_idx = None
        for i, rect in enumerate(self._rects):
            if rect.collidepoint(mx, my):
                self._hover_idx = i

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        # Dim overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(self._overlay_color)
        surface.blit(overlay, (0, 0))

        # Card
        card_w, card_h = 300, len(self._BUTTONS) * (self.BTN_H + 10) + 70
        cx = SCREEN_WIDTH  // 2 - card_w // 2
        cy = SCREEN_HEIGHT // 2 - card_h // 2
        card = pygame.Rect(cx, cy, card_w, card_h)
        pygame.draw.rect(surface, (20, 28, 40), card, border_radius=10)
        pygame.draw.rect(surface, C_PANEL_BORDER, card, 2, border_radius=10)

        title_surf = FONT_BIG.render("PAUSED", True, C_HIGHLIGHT)
        surface.blit(title_surf, (cx + card_w // 2 - title_surf.get_width() // 2, cy + 14))

        self._rects = []
        for i, label in enumerate(self._BUTTONS):
            bx = cx + card_w // 2 - self.BTN_W // 2
            by = cy + 55 + i * (self.BTN_H + 8)
            rect = pygame.Rect(bx, by, self.BTN_W, self.BTN_H)
            self._rects.append(rect)

            bg = C_BUTTON_HOVER if self._hover_idx == i else C_BUTTON
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            pygame.draw.rect(surface, C_PANEL_BORDER, rect, 1, border_radius=6)

            lbl_surf = FONT_TITLE.render(label, True, C_TEXT)
            surface.blit(lbl_surf, (bx + self.BTN_W // 2 - lbl_surf.get_width() // 2,
                                    by + self.BTN_H // 2 - lbl_surf.get_height() // 2))