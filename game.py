"""
game.py — Main Game class
===========================
Orchestrates input, update, draw, and all sub-systems.
"""

import pygame
import sys

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    STARTING_MONEY, STARTING_HEALTH,
    C_BG, TOWER_TEMPLATES,
)
from grid import Grid
from entities import Tower, Village
from wave_manager import WaveManager
from ui import InfoPanel, ShopPanel, VillagePanel, EscapeMenu
from save_load import save_game, load_game, build_save_dict, restore_from_dict


class GameState:
    PLAYING   = "playing"
    PAUSED    = "paused"
    GAME_OVER = "game_over"


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._init_state()

    def _init_state(self) -> None:
        """(Re-)initialise every piece of mutable game state. Called on
        both first launch and restart."""
        self.money = STARTING_MONEY
        self.state = GameState.PLAYING

        self.grid         = Grid()
        self.village      = Village(STARTING_HEALTH)
        self.wave_manager = WaveManager()

        self.info_panel    = InfoPanel()
        self.shop_panel    = ShopPanel()
        self.village_panel = VillagePanel()
        self.escape_menu   = EscapeMenu()

        self.selected_tower = None
        self._hover_cell    = None

        # Pre-build the restart button rect (reused every frame)
        btn_w, btn_h = 220, 50
        self._restart_rect = pygame.Rect(
            SCREEN_WIDTH  // 2 - btn_w // 2,
            SCREEN_HEIGHT // 2 + 40,
            btn_w, btn_h,
        )
        self._restart_hover = False

        self.wave_manager.start_next_wave()

    # ── Public API ────────────────────────────────────────────────────────────

    def handle_events(self) -> None:
        mx, my = pygame.mouse.get_pos()

        self._hover_cell = self.grid.cell_at_mouse(mx, my)
        self.shop_panel.update_hover(mx, my)
        self.village_panel.update_hover(mx, my)
        self.escape_menu.update_hover(mx, my)
        self._restart_hover = (
            self.state == GameState.GAME_OVER
            and self._restart_rect.collidepoint(mx, my)
        )

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self._quit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.GAME_OVER:
                        pass   # Escape does nothing on game-over screen
                    else:
                        self.escape_menu.toggle()
                        self.state = (GameState.PAUSED
                                      if self.escape_menu.visible
                                      else GameState.PLAYING)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(mx, my)

    def update(self, dt: float) -> None:
        if self.state != GameState.PLAYING:
            return

        money_earned = self.wave_manager.update(dt, self.grid, self.village)
        self.money  += money_earned

        self.grid.update(dt, self.wave_manager.active_zombies)

        if self.selected_tower and not self.selected_tower.alive:
            self.selected_tower = None

        if not self.village.alive:
            self.state = GameState.GAME_OVER

    def draw(self) -> None:
        self.screen.fill(C_BG)

        # Determine range preview for placement
        placement_range = 0
        if self.shop_panel.selected_key:
            tmpl = TOWER_TEMPLATES.get(self.shop_panel.selected_key, {})
            placement_range = tmpl.get("range", 0)

        self.grid.draw(
            self.screen,
            self._hover_cell,
            self.selected_tower,
            placement_range=placement_range,
        )
        self.wave_manager.draw(self.screen)

        self.info_panel.draw(
            self.screen,
            self.selected_tower,
            self.money,
            self.wave_manager.wave_number,
            self.wave_manager.seconds_until_next_wave(),
        )
        self.shop_panel.draw(self.screen, self.money, self.village)
        self.village_panel.draw(self.screen, self.village, self.money)
        self.escape_menu.draw(self.screen)

        if self.state == GameState.GAME_OVER:
            self._draw_game_over()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _handle_click(self, mx: int, my: int) -> None:
        # ── Restart button (game over screen) ────────────────────────────
        if self.state == GameState.GAME_OVER:
            if self._restart_rect.collidepoint(mx, my):
                self._init_state()
            return

        # ── Escape menu ───────────────────────────────────────────────────
        action = self.escape_menu.handle_click(mx, my)
        if action:
            self._handle_escape_action(action)
            return

        if self.state != GameState.PLAYING:
            return

        # ── Shop ──────────────────────────────────────────────────────────
        shop_key = self.shop_panel.handle_click(mx, my)
        if shop_key is not None:
            self.selected_tower = None
            return

        # ── Village upgrades ──────────────────────────────────────────────
        spent = self.village_panel.handle_click(mx, my, self.money, self.village)
        if spent:
            self.money -= spent
            return

        # ── Grid click ────────────────────────────────────────────────────
        cell = self.grid.cell_at_mouse(mx, my)
        if cell is not None:
            col, row = cell
            existing = self.grid.get_tower(col, row)

            if existing:
                self.selected_tower = (
                    None if existing is self.selected_tower else existing
                )
                self.shop_panel.selected_key = None
            elif self.shop_panel.selected_key:
                self._try_place_tower(col, row)

    def _try_place_tower(self, col: int, row: int) -> None:
        key = self.shop_panel.selected_key
        if key not in TOWER_TEMPLATES:
            return

        tmpl = TOWER_TEMPLATES[key]
        cost = self.village.effective_cost(tmpl["cost"])

        if self.money < cost:
            return

        tower = Tower(tmpl, col, row)
        if self.grid.place_tower(tower, col, row):
            self.money -= cost

    def _handle_escape_action(self, action: str) -> None:
        if action == "Resume":
            self.escape_menu.visible = False
            self.state = GameState.PLAYING
        elif action == "Save Game":
            save_game(build_save_dict(self))
        elif action == "Settings":
            print("[Settings] Not yet implemented.")
        elif action == "Quit":
            self._quit()

    def _draw_game_over(self) -> None:
        # Dim overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # "GAME OVER" title
        font  = pygame.font.SysFont("monospace", 48, bold=True)
        msg   = font.render("GAME OVER", True, (220, 60, 60))
        cx    = SCREEN_WIDTH  // 2 - msg.get_width()  // 2
        cy    = SCREEN_HEIGHT // 2 - msg.get_height() // 2 - 30
        self.screen.blit(msg, (cx, cy))

        # Restart button
        btn_color = (60, 100, 70) if self._restart_hover else (35, 65, 45)
        pygame.draw.rect(self.screen, btn_color,
                         self._restart_rect, border_radius=8)
        pygame.draw.rect(self.screen, (80, 200, 120),
                         self._restart_rect, 2, border_radius=8)

        btn_font = pygame.font.SysFont("monospace", 20, bold=True)
        btn_lbl  = btn_font.render("Play Again", True, (200, 255, 210))
        self.screen.blit(btn_lbl, btn_lbl.get_rect(center=self._restart_rect.center))

    @staticmethod
    def _quit() -> None:
        pygame.quit()
        sys.exit()