
"""
Tower Defense Game - Main Entry Point
======================================
Run this file to start the game.
"""

import pygame
from game import Game
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    game = Game(screen)

    while True:
        dt = clock.tick(FPS) / 1000.0  # Delta time in seconds
        game.handle_events()
        game.update(dt)
        game.draw()
        pygame.display.flip()


if __name__ == "__main__":
    main()
