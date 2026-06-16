import pygame

from environment.map import (
    DisasterMap,
    EMPTY,
    OBSTACLE,
    HAZARD,
    SURVIVOR
)

CELL_SIZE = 30

GRID_WIDTH = 25
GRID_HEIGHT = 20

WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE

pygame.init()

screen = pygame.display.set_mode(
    (WINDOW_WIDTH, WINDOW_HEIGHT)
)

pygame.display.set_caption(
    "Multi-Agent UAV Swarm Simulation"
)

clock = pygame.time.Clock()

disaster_map = DisasterMap(
    GRID_WIDTH,
    GRID_HEIGHT
)

disaster_map.generate()

def draw_map():

    colors = {
        EMPTY: (240, 240, 240),
        OBSTACLE: (60, 60, 60),
        HAZARD: (255, 140, 0),
        SURVIVOR: (0, 200, 0)
    }

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):

            value = disaster_map.grid[y][x]

            rect = pygame.Rect(
                x * CELL_SIZE,
                y * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )

            pygame.draw.rect(
                screen,
                colors[value],
                rect
            )

            pygame.draw.rect(
                screen,
                (180, 180, 180),
                rect,
                1
            )
            

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    screen.fill((255, 255, 255))

    draw_map()

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
