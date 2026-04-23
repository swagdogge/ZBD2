"""
grid.py — The game grid
=========================
Manages the 2-D cell array of placed towers AND the live projectile list.

Towers now receive the projectile list in update() so they can spawn shots.
Projectiles are updated and drawn here alongside towers.
"""

import pygame
from config import (
    GRID_COLS, GRID_ROWS, CELL_SIZE,
    GRID_X, GRID_Y, GRID_WIDTH, GRID_HEIGHT,
    C_GRID_BG, C_GRID_LINE, C_HIGHLIGHT,
)


class Grid:
    def __init__(self):
        # 2-D array: cells[row][col] = Tower | None
        self.cells: list[list] = [[None] * GRID_COLS for _ in range(GRID_ROWS)]
        # All live projectiles — towers append here; Grid ticks & culls them
        self.projectiles: list = []

    # ── Placement helpers ────────────────────────────────────────────────────

    def place_tower(self, tower, col: int, row: int) -> bool:
        if not self._in_bounds(col, row):
            return False
        if self.cells[row][col] is not None:
            return False
        tower.col = col
        tower.row = row
        self.cells[row][col] = tower
        return True

    def remove_tower(self, col: int, row: int):
        if not self._in_bounds(col, row):
            return None
        tower = self.cells[row][col]
        self.cells[row][col] = None
        return tower

    def get_tower(self, col: int, row: int):
        if not self._in_bounds(col, row):
            return None
        return self.cells[row][col]

    def all_towers(self) -> list:
        return [t for row in self.cells for t in row if t is not None]

    # ── Mouse helpers ────────────────────────────────────────────────────────

    def cell_at_mouse(self, mx: int, my: int):
        if not (GRID_X <= mx < GRID_X + GRID_WIDTH and
                GRID_Y <= my < GRID_Y + GRID_HEIGHT):
            return None
        col = (mx - GRID_X) // CELL_SIZE
        row = (my - GRID_Y) // CELL_SIZE
        if self._in_bounds(col, row):
            return (col, row)
        return None

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, dt: float, zombies: list) -> None:
        # Tick towers — they may append to self.projectiles
        for tower in self.all_towers():
            tower.update(dt, zombies, self.projectiles)

        # Remove dead towers
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                t = self.cells[r][c]
                if t is not None and not t.alive:
                    self.cells[r][c] = None

        # Tick projectiles
        for p in self.projectiles:
            p.update(dt, zombies)

        # Cull spent projectiles
        self.projectiles = [p for p in self.projectiles if p.alive]

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface,
             hover_cell=None, selected_tower=None,
             placement_range: int = 0) -> None:
        """
        placement_range — range (in cells) of the shop-selected tower type;
                          when >0 a preview circle is drawn on hover_cell.
        """
        # Grid background
        pygame.draw.rect(surface, C_GRID_BG,
                         pygame.Rect(GRID_X, GRID_Y, GRID_WIDTH, GRID_HEIGHT))

        # Cell hover tint + grid lines
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = GRID_X + col * CELL_SIZE
                y = GRID_Y + row * CELL_SIZE
                cell_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                if hover_cell == (col, row):
                    s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    s.fill((255, 255, 255, 30))
                    surface.blit(s, (x, y))

                pygame.draw.rect(surface, C_GRID_LINE, cell_rect, 1)

        # Towers
        for tower in self.all_towers():
            tower.draw(surface, selected=(selected_tower is tower))

        # ── Range circles (drawn after towers so they sit on top) ────────────

        # Selected tower: yellow outline
        if selected_tower is not None and selected_tower.range > 0:
            _draw_range_circle(surface, selected_tower.center(),
                               selected_tower.range,
                               color=(255, 220, 80), alpha=170, width=2)

        # Placement preview: soft white/blue outline on hovered cell
        if hover_cell is not None and placement_range > 0:
            col, row = hover_cell
            cx = GRID_X + col * CELL_SIZE + CELL_SIZE // 2
            cy = GRID_Y + row * CELL_SIZE + CELL_SIZE // 2
            _draw_range_circle(surface, (cx, cy),
                               placement_range,
                               color=(200, 210, 255), alpha=120, width=2)

        # Projectiles — on top of towers, under zombies
        for p in self.projectiles:
            p.draw(surface)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS


# ── Module-level helper ───────────────────────────────────────────────────────

def _draw_range_circle(surface: pygame.Surface, center: tuple,
                       range_cells: int, color: tuple,
                       alpha: int = 150, width: int = 2) -> None:
    """Blit a semi-transparent circle outline onto *surface*."""
    radius   = int(range_cells * CELL_SIZE)
    diameter = radius * 2 + 4
    tmp      = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    c        = radius + 2          # centre within tmp
    pygame.draw.circle(tmp, (*color, alpha), (c, c), radius, width)
    surface.blit(tmp, (center[0] - c, center[1] - c))