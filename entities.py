"""
entities.py — Game entities
=============================
Tower, Projectile, Zombie, Village classes.

Projectile system:
  - Towers spawn Projectile objects instead of dealing instant damage
  - Archer fires a fast, small blue bolt (single target)
  - Cannon fires a slow, heavy ball with splash damage on impact
  - Projectiles home in on their target; on arrival deal damage (+ splash)
  - Grid owns the projectile list and passes it into tower.update()
"""

import pygame
import copy
import random
import math
from config import CELL_SIZE, GRID_X, GRID_Y, C_DANGER, C_ACCENT


# ─────────────────────────────────────────────────────────────────────────────
# Projectile
# ─────────────────────────────────────────────────────────────────────────────

PROJECTILE_STYLES = {
    #  key          speed px/s  radius  color             splash_radius (0=none)
    "arrow":      dict(speed=600, radius=3,  color=(180, 220, 255), splash_radius=0),
    "cannonball": dict(speed=280, radius=7,  color=(220, 160,  50), splash_radius=CELL_SIZE * 1.4),
}


class Projectile:
    """
    Homing projectile spawned by a Tower.
    Flies toward its target zombie; on impact deals damage.
    splash_radius > 0 → damages all zombies within that pixel radius.
    """

    def __init__(self, style: str, x: float, y: float,
                 target: "Zombie", damage: int):
        s = PROJECTILE_STYLES[style]
        self.style         = style
        self.x             = float(x)
        self.y             = float(y)
        self.target        = target
        self.damage        = damage
        self.speed         = s["speed"]
        self.radius        = s["radius"]
        self.color         = s["color"]
        self.splash_radius = s["splash_radius"]
        self.alive         = True
        # Tiny jitter so simultaneous shots don't stack identically
        self._jitter = random.uniform(-4, 4)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float, zombies: list) -> None:
        # Re-home if original target died
        if not self.target.alive:
            self.target = self._nearest(zombies)
            if self.target is None:
                self.alive = False
                return

        tx = self.target.x + self._jitter
        ty = self.target.y
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        # Arrived?
        if dist <= self.speed * dt + self.radius:
            self._on_impact(zombies)
            self.alive = False
            return

        # Move toward target
        self.x += (dx / dist) * self.speed * dt
        self.y += (dy / dist) * self.speed * dt

    def _on_impact(self, zombies: list) -> None:
        if self.splash_radius > 0:
            for z in zombies:
                d = math.sqrt((z.x - self.x) ** 2 + (z.y - self.y) ** 2)
                if d <= self.splash_radius:
                    z.take_damage(self.damage)
        else:
            if self.target.alive:
                self.target.take_damage(self.damage)

    def _nearest(self, zombies: list) -> "Zombie | None":
        best, best_d = None, float("inf")
        for z in zombies:
            if not z.alive:
                continue
            d = math.sqrt((z.x - self.x) ** 2 + (z.y - self.y) ** 2)
            if d < best_d:
                best, best_d = z, d
        return best

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        ix, iy = int(self.x), int(self.y)
        pygame.draw.circle(surface, self.color, (ix, iy), self.radius)
        # Bright core for cannonballs
        if self.radius > 3:
            pygame.draw.circle(surface, (255, 255, 220), (ix, iy), self.radius // 2)


# ─────────────────────────────────────────────────────────────────────────────
# Tower
# ─────────────────────────────────────────────────────────────────────────────

# Maps tower name → projectile style.  Add entries here for new tower types.
# The key must match the "name" field in TOWER_TEMPLATES in config.py.
_TOWER_PROJ_STYLE: dict[str, str] = {
    "Rifle":      "arrow",
    "Machinegun": "arrow",
    "Sniper":     "arrow",
    "Cannon":     "cannonball",
}


class Tower:
    def __init__(self, template: dict, grid_col: int, grid_row: int):
        data = copy.deepcopy(template)

        self.name        = data["name"]
        self.description = data["description"]
        self.color       = data["color"]

        self.health      = data["health"]
        self.max_health  = data["max_health"]
        self.fire_rate   = data["fire_rate"]
        self.damage      = data["damage"]
        self.range       = data["range"]

        self.col = grid_col
        self.row = grid_row

        self._fire_timer  = 0.0
        self.alive        = True
        self._proj_style  = _TOWER_PROJ_STYLE.get(self.name)   # None → no shooting

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            GRID_X + self.col * CELL_SIZE,
            GRID_Y + self.row * CELL_SIZE,
            CELL_SIZE, CELL_SIZE,
        )

    def center(self) -> tuple[int, int]:
        return (
            GRID_X + self.col * CELL_SIZE + CELL_SIZE // 2,
            GRID_Y + self.row * CELL_SIZE + CELL_SIZE // 2,
        )

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float, zombies: list, projectiles: list) -> None:
        """
        Tick the fire timer.  When it expires, find the nearest zombie in
        range and append a new Projectile to *projectiles*.
        Walls (fire_rate == 0) do nothing.
        """
        if self.fire_rate == 0 or self._proj_style is None:
            return

        self._fire_timer += dt
        if self._fire_timer >= 1.0 / self.fire_rate:
            self._fire_timer = 0.0
            target = self._find_target(zombies)
            if target:
                cx, cy = self.center()
                projectiles.append(
                    Projectile(self._proj_style, cx, cy, target, self.damage)
                )

    def _find_target(self, zombies: list) -> "Zombie | None":
        closest, closest_dist = None, float("inf")
        cx, cy = self.center()
        for z in zombies:
            dx = z.x - cx
            dy = z.y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= self.range * CELL_SIZE and dist < closest_dist:
                closest, closest_dist = z, dist
        return closest

    # ── Damage ────────────────────────────────────────────────────────────────

    def take_damage(self, amount: int) -> None:
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, selected: bool = False) -> None:
        r = self.rect
        pygame.draw.rect(surface, self.color, r, border_radius=4)

        border_color = (255, 220, 80) if selected else (0, 0, 0)
        border_width = 3 if selected else 1
        pygame.draw.rect(surface, border_color, r, border_width, border_radius=4)

        # Health bar
        bar_w = r.width - 4
        ratio = self.health / self.max_health
        bar_color = C_ACCENT if ratio > 0.5 else C_DANGER
        pygame.draw.rect(surface, (40, 40, 40), (r.x + 2, r.y + 2, bar_w, 5))
        pygame.draw.rect(surface, bar_color,    (r.x + 2, r.y + 2, int(bar_w * ratio), 5))

        # Letter label
        font  = pygame.font.SysFont("monospace", 14, bold=True)
        label = font.render(self.name[0], True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=r.center))


# ─────────────────────────────────────────────────────────────────────────────
# Zombie
# ─────────────────────────────────────────────────────────────────────────────

SEPARATION_FORCE = 400.0
DRAG             = 8.0
PROBE_AHEAD      = CELL_SIZE * 0.55
ATTACK_INTERVAL  = 0.8
ATTACK_DAMAGE    = 8


class Zombie:
    def __init__(self, template: dict, start_col: int):
        data = copy.deepcopy(template)

        self.name       = data["name"]
        self.health     = data["health"]
        self.max_health = data["health"]
        self.speed      = data["speed"]
        self.damage     = data["damage"]
        self.reward     = data["reward"]
        self.color      = data["color"]

        self.x = float(GRID_X + start_col * CELL_SIZE + CELL_SIZE // 2)
        self.y = float(GRID_Y - CELL_SIZE // 2)

        self.size = random.randint(CELL_SIZE // 3, CELL_SIZE // 2)
        self.vx   = 0.0
        self.vy   = 0.0
        self.alive = True
        self._attack_timer = 0.0

    # ── Helpers ───────────────────────────────────────────────────────────────

    def grid_pos(self) -> tuple[int, int]:
        return (
            int((self.x - GRID_X) // CELL_SIZE),
            int((self.y - GRID_Y) // CELL_SIZE),
        )

    def _pixel_to_cell(self, px: float, py: float) -> tuple[int, int]:
        return int((px - GRID_X) // CELL_SIZE), int((py - GRID_Y) // CELL_SIZE)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float, grid, village, zombies: list) -> None:
        from config import GRID_COLS, GRID_HEIGHT

        blocking = self._find_blocking_tower(grid)

        if blocking is not None:
            self._attack_timer += dt
            if self._attack_timer >= ATTACK_INTERVAL:
                self._attack_timer = 0.0
                blocking.take_damage(ATTACK_DAMAGE)
            self.vx += random.uniform(-40, 40)
            self.vy  = 0.0
        else:
            self._attack_timer = 0.0
            self.vx += (random.uniform(-15, 15) - self.vx) * min(1.0, dt * 6)
            self.vy += (self.speed * CELL_SIZE   - self.vy) * min(1.0, dt * 6)

        sx, sy = self._separation_force(zombies)
        self.vx += sx * dt
        self.vy += sy * dt

        f = max(0.0, 1.0 - DRAG * dt)
        self.vx *= f
        self.vy *= f

        nx = self.x + self.vx * dt
        ny = self.y + self.vy * dt

        nx, ny = self._resolve_tower_collisions(nx, ny, grid)

        half = self.size // 2
        nx = max(GRID_X + half, min(GRID_X + GRID_COLS * CELL_SIZE - half, nx))

        self.x, self.y = nx, ny

        if self.y > GRID_Y + GRID_HEIGHT:
            village.take_damage(self.damage)
            self.alive = False

    def _find_blocking_tower(self, grid) -> "Tower | None":
        col, row = self._pixel_to_cell(self.x, self.y + PROBE_AHEAD)
        t = grid.get_tower(col, row)
        if t:
            return t
        col0, row0 = self.grid_pos()
        return grid.get_tower(col0, row0)

    def _resolve_tower_collisions(self, nx: float, ny: float, grid) -> tuple[float, float]:
        r = self.size // 2
        cc, rc = self._pixel_to_cell(nx, ny)
        for dr in range(-1, 3):
            for dc in range(-1, 2):
                tower = grid.get_tower(cc + dc, rc + dr)
                if tower is None:
                    continue
                tr = tower.rect
                cx_ = max(tr.left, min(nx, tr.right))
                cy_ = max(tr.top,  min(ny, tr.bottom))
                dx, dy = nx - cx_, ny - cy_
                d2 = dx * dx + dy * dy
                if d2 < r * r and d2 > 0:
                    d   = math.sqrt(d2)
                    nx += (dx / d) * (r - d)
                    ny += (dy / d) * (r - d)
                    dot = self.vx * (dx / d) + self.vy * (dy / d)
                    if dot < 0:
                        self.vx -= dot * (dx / d)
                        self.vy -= dot * (dy / d)
        return nx, ny

    def _separation_force(self, zombies: list) -> tuple[float, float]:
        fx = fy = 0.0
        for other in zombies:
            if other is self:
                continue
            dx, dy = self.x - other.x, self.y - other.y
            d2     = dx * dx + dy * dy
            min_d  = (self.size + other.size) * 0.7
            if d2 < min_d * min_d and d2 > 0:
                d   = math.sqrt(d2)
                ov  = min_d - d
                fx += (dx / d) * ov * SEPARATION_FORCE
                fy += (dy / d) * ov * SEPARATION_FORCE
        return fx, fy

    def take_damage(self, amount: int) -> None:
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        r = pygame.Rect(
            int(self.x - self.size // 2),
            int(self.y - self.size // 2),
            self.size, self.size,
        )
        pygame.draw.ellipse(surface, self.color, r)
        pygame.draw.ellipse(surface, (0, 0, 0), r, 1)
        bar_w = self.size
        ratio = self.health / self.max_health
        pygame.draw.rect(surface, (40, 40, 40), (r.x, r.y - 6, bar_w, 4))
        pygame.draw.rect(surface, C_DANGER,      (r.x, r.y - 6, int(bar_w * ratio), 4))


# ─────────────────────────────────────────────────────────────────────────────
# Village
# ─────────────────────────────────────────────────────────────────────────────

class Village:
    def __init__(self, starting_health: int):
        self.max_health        = starting_health
        self.health            = starting_health
        self.upgrades_applied: list[str] = []
        self.income_bonus      = 0
        self.tower_discount    = 0.0

    def take_damage(self, amount: int) -> None:
        self.health = max(0, self.health - amount)

    def apply_upgrade(self, upgrade: dict) -> None:
        effect, value = upgrade["effect"], upgrade["value"]
        if effect == "village_health":
            self.max_health += value
            self.health     += value
        elif effect == "income_bonus":
            self.income_bonus += value
        elif effect == "tower_discount":
            self.tower_discount = min(0.5, self.tower_discount + value)
        self.upgrades_applied.append(upgrade["name"])

    @property
    def alive(self) -> bool:
        return self.health > 0

    def effective_cost(self, base_cost: int) -> int:
        return max(1, int(base_cost * (1 - self.tower_discount)))