"""
save_load.py — Save and load game state
=========================================
Uses JSON for easy inspection and editing.
"""

import json
import os
from pathlib import Path

SAVE_PATH = Path("save.json")


def save_game(game_state: dict) -> bool:
    """Serialize and write game state to disk. Returns True on success."""
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(game_state, f, indent=2)
        print(f"[Save] Game saved to {SAVE_PATH.resolve()}")
        return True
    except Exception as e:
        print(f"[Save] Failed: {e}")
        return False


def load_game() -> dict | None:
    """Read and return game state dict, or None if no save exists."""
    if not SAVE_PATH.exists():
        return None
    try:
        with open(SAVE_PATH, "r") as f:
            data = json.load(f)
        print(f"[Load] Game loaded from {SAVE_PATH.resolve()}")
        return data
    except Exception as e:
        print(f"[Load] Failed: {e}")
        return None


def build_save_dict(game) -> dict:
    """
    Convert the live Game object into a JSON-serialisable dict.
    Extend this when you add more persistent state.
    """
    towers = []
    for tower in game.grid.all_towers():
        towers.append({
            "template_key": _find_template_key(tower),
            "col": tower.col,
            "row": tower.row,
            "health": tower.health,
        })

    return {
        "money":            game.money,
        "wave_number":      game.wave_manager.wave_number,
        "village_health":   game.village.health,
        "village_max_health": game.village.max_health,
        "village_upgrades": game.village.upgrades_applied,
        "income_bonus":     game.village.income_bonus,
        "tower_discount":   game.village.tower_discount,
        "towers":           towers,
    }


def restore_from_dict(game, data: dict) -> None:
    """
    Restore live Game from a save dict.
    Call after creating a fresh Game instance.
    """
    from config import TOWER_TEMPLATES, VILLAGE_UPGRADES
    from entities import Tower

    game.money = data.get("money", game.money)
    game.wave_manager.wave_number = data.get("wave_number", 0)

    v = game.village
    v.health     = data.get("village_health", v.health)
    v.max_health = data.get("village_max_health", v.max_health)
    v.upgrades_applied = data.get("village_upgrades", [])
    v.income_bonus     = data.get("income_bonus", 0)
    v.tower_discount   = data.get("tower_discount", 0.0)

    for t_data in data.get("towers", []):
        key = t_data.get("template_key")
        if key and key in TOWER_TEMPLATES:
            tower = Tower(TOWER_TEMPLATES[key], t_data["col"], t_data["row"])
            tower.health = t_data.get("health", tower.health)
            game.grid.place_tower(tower, t_data["col"], t_data["row"])


def _find_template_key(tower) -> str:
    """Reverse-lookup the template key from a tower's name."""
    from config import TOWER_TEMPLATES
    for key, tmpl in TOWER_TEMPLATES.items():
        if tmpl["name"] == tower.name:
            return key
    return "archer"   # fallback