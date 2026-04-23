"""
wave_manager.py — Wave spawning logic
=======================================
Controls when and which zombies appear.
Add new wave definitions to WAVE_DEFINITIONS to extend the game.
"""

import random
from config import (
    GRID_COLS, WAVE_SPAWN_INTERVAL, WAVE_REST_TIME,
    ZOMBIE_TEMPLATES
)
from entities import Zombie


# ── Wave definitions ──────────────────────────────────────────────────────────
# Each wave is a list of (zombie_type_key, count) pairs.
# ZOMBIE_TEMPLATES keys: "basic", "brute"
WAVE_DEFINITIONS = [
    [("basic", 10)],
    [("basic", 50), ("brute", 2)],
    [("basic", 20), ("brute", 10)],
    [("basic_plus", 20), ("brute", 10)],
    [("basic_plus", 10), ("boss", 1)],
    [("basic_plus", 100), ("brute", 10), ("boss", 2)],
    # Add more waves freely — the manager loops back at the end
]


class WaveManager:
    def __init__(self):
        self.wave_number = 0       # current wave (0-indexed)
        self.in_progress = False
        self._queue: list = []      # zombies left to spawn this wave
        self._spawn_timer = 0.0
        self._rest_timer = 0.0
        self._rest_active = False

        self.active_zombies: list[Zombie] = []

    # ── Public API

    def start_next_wave(self) -> None:
        if self.in_progress:
            return
        defn_index = self.wave_number % len(WAVE_DEFINITIONS)
        defn = WAVE_DEFINITIONS[defn_index]

        self._queue = []
        for zombie_key, count in defn:
            template = ZOMBIE_TEMPLATES[zombie_key]
            for _ in range(count):
                self._queue.append(template)

        random.shuffle(self._queue)
        self._spawn_timer = 0.0
        self.in_progress = True
        self._rest_active = False

    @property
    def wave_cleared(self) -> bool:
        """True when all zombies are dead and none left to spawn."""
        return self.in_progress and not self._queue and not self.active_zombies

    # ── Update

    def update(self, dt: float, grid, village) -> int:
        """
        Update zombies and spawning. Returns money earned this tick.
        """
        money_earned = 0

        # Spawn next zombie in queue
        if self._queue and self.in_progress:
            self._spawn_timer += dt
            if self._spawn_timer >= WAVE_SPAWN_INTERVAL:
                self._spawn_timer = 0.0
                template = self._queue.pop(0)
                col = random.randint(0, GRID_COLS - 1)
                self.active_zombies.append(Zombie(template, col))

        # Update active zombies
        for z in self.active_zombies:
            z.update(dt, grid, village, self.active_zombies)

        # Collect dead zombies
        dead = [z for z in self.active_zombies if not z.alive]
        for z in dead:
            if z.health <= 0:          # killed, not just reached village
                money_earned += z.reward
        self.active_zombies = [z for z in self.active_zombies if z.alive]

        # Check wave completion
        if self.wave_cleared:
            self.in_progress = False
            self._rest_active = True
            self._rest_timer = 0.0
            self.wave_number += 1

        # Auto-start next wave after rest period
        if self._rest_active:
            self._rest_timer += dt
            if self._rest_timer >= WAVE_REST_TIME:
                self._rest_active = False
                self.start_next_wave()

        return money_earned

    # ── Draw

    def draw(self, surface) -> None:
        for z in self.active_zombies:
            z.draw(surface)

    # ── Status helpers

    def seconds_until_next_wave(self) -> float:
        if self._rest_active:
            return max(0.0, WAVE_REST_TIME - self._rest_timer)
        return 0.0