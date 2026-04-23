"""
config.py — Central configuration file
========================================
All constants live here. Tweak freely.
"""

# ── Window ──────────────────────────────────────────────────────────────────
TITLE        = "Tower Defense"
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 800
FPS           = 60

# ── Layout regions (pixel coordinates) ──────────────────────────────────────
#
#   ┌──────────┬──────────────────────┬──────────┐
#   │          │                      │          │
#   │  INFO    │      GRID            │  SHOP    │
#   │  PANEL   │                      │  PANEL   │
#   │  (left)  │                      │  (right) │
#   ├──────────┴──────────────────────┴──────────┤
#   │              VILLAGE PANEL (bottom)         │
#   └─────────────────────────────────────────────┘

LEFT_PANEL_WIDTH   = 220
RIGHT_PANEL_WIDTH  = 220
BOTTOM_PANEL_HEIGHT = 160

GRID_X      = LEFT_PANEL_WIDTH
GRID_Y      = 0
GRID_WIDTH  = SCREEN_WIDTH - LEFT_PANEL_WIDTH - RIGHT_PANEL_WIDTH
GRID_HEIGHT = SCREEN_HEIGHT - BOTTOM_PANEL_HEIGHT

# ── Grid ────────────────────────────────────────────────────────────────────
GRID_COLS = 11   # number of columns
GRID_ROWS = 15   # number of rows
CELL_SIZE  = min(GRID_WIDTH // GRID_COLS, GRID_HEIGHT // GRID_ROWS)

# ── Shop ────────────────────────────────────────────────────────────────────
SHOP_COLS = 2
SHOP_ROWS = 4
SHOP_CELL_SIZE = (RIGHT_PANEL_WIDTH - 20) // SHOP_COLS   # padding = 10 each side

# ── Colors ───────────────────────────────────────────────────────────────────
C_BG            = (15,  20,  30)   # main background
C_GRID_BG       = (25,  35,  45)   # grid background
C_GRID_LINE     = (40,  55,  70)   # grid lines
C_PANEL_BG      = (20,  28,  40)   # side / bottom panels
C_PANEL_BORDER  = (50,  70,  90)   # panel borders
C_TEXT          = (200, 215, 230)  # primary text
C_TEXT_DIM      = (100, 120, 140)  # secondary / dimmed text
C_ACCENT        = (80,  200, 120)  # green accent (money, health)
C_DANGER        = (220,  70,  60)  # red (damage, low health)
C_HIGHLIGHT     = (255, 220,  80)  # yellow highlight / selection
C_TOWER         = (60,  140, 220)  # default tower color
C_ZOMBIE        = (100, 200,  80)  # zombie color
C_CELL_HOVER    = (255, 255, 255)  # cell hover tint (alpha overlay)
C_SHOP_HOVER    = (40,  60,  80)
C_SHOP_SELECTED = (50,  80, 110)
C_BUTTON        = (35,  50,  70)
C_BUTTON_HOVER  = (55,  80, 110)

# ── Player ───────────────────────────────────────────────────────────────────
STARTING_MONEY  = 200
STARTING_HEALTH = 100   # village health

# ── Waves ────────────────────────────────────────────────────────────────────
WAVE_SPAWN_INTERVAL = 0.2   # seconds between zombies in a wave
WAVE_REST_TIME      = 8.0   # seconds between waves

# ── Towers (template data — add more freely) ─────────────────────────────────
TOWER_TEMPLATES = {
    "rifle": {
        "name":        "Rifle",
        "description": "Cheapest shit available.",
        "cost":        15,
        "health":      80,
        "max_health":  80,
        "fire_rate":   1,    # shots per second
        "damage":      5,
        "range":       6,      # in grid cells
        "color":       (100, 180, 255),
    },
    "machinegun": {
        "name":        "Machinegun",
        "description": "Fast but weak. Good for early waves.",
        "cost":        50,
        "health":      80,
        "max_health":  80,
        "fire_rate":   4,    # shots per second
        "damage":      2,
        "range":       4,      # in grid cells
        "color":       (100, 180, 255),
    },
    "sniper": {
        "name":        "Sniper",
        "description": "High range, high damage, very low fire rate",
        "cost":        150,
        "health":      80,
        "max_health":  80,
        "fire_rate":   0.3,    # shots per second
        "damage":      50,
        "range":       11,      # in grid cells
        "color":       (100, 180, 255),
    },
    "cannon": {
        "name":        "Cannon",
        "description": "Slow but deals massive splash damage.",
        "cost":        120,
        "health":      150,
        "max_health":  150,
        "fire_rate":   0.5,
        "damage":      20,
        "range":       4,
        "color":       (200, 140,  60),
    },
    "wall": {
        "name":        "Wall",
        "description": "Blocks zombies. Cannot attack.",
        "cost":        30,
        "health":      300,
        "max_health":  300,
        "fire_rate":   0,
        "damage":      0,
        "range":       0,
        "color":       (160, 160, 160),
    },
}

# ── Zombies (template data) ───────────────────────────────────────────────────
ZOMBIE_TEMPLATES = {
    "basic": {
        "name":    "Walker",
        "health":  5,
        "speed":   2,    # grid cells per second
        "damage":  10,     # damage to tower on contact
        "reward":  5,     # money on kill
        "color":   C_ZOMBIE,
    },
    "basic_plus": {
        "name":    "Walker",
        "health":  25,
        "speed":   2,    # grid cells per second
        "damage":  15,     # damage to tower on contact
        "reward":  5,     # money on kill
        "color":   C_ZOMBIE,
    },
    "brute": {
        "name":    "Brute",
        "health":  50,
        "speed":   1,
        "damage":  30,
        "reward":  25,
        "color":   (180, 100, 60),
    },
    "boss": {
        "name":    "Boss",
        "health":  250,
        "speed":   0.5,
        "damage":  30,
        "reward":  100,
        "color":   (180, 180, 60),
    },
}

# ── Village upgrades ──────────────────────────────────────────────────────────
VILLAGE_UPGRADES = [
    {"name": "Fortify Walls",  "cost": 100, "effect": "village_health", "value": 50},
    {"name": "Market",         "cost": 150, "effect": "income_bonus",   "value": 10},
    {"name": "Barracks",       "cost": 200, "effect": "tower_discount", "value": 0.10},
]