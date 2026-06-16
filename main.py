import random
import pygame

from agents.uav import UAV

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

font = pygame.font.SysFont(None, 28)

disaster_map = DisasterMap(
    GRID_WIDTH,
    GRID_HEIGHT
)

disaster_map.generate()


def get_random_empty_cell():

    while True:

        x = random.randint(0, GRID_WIDTH - 1)
        y = random.randint(0, GRID_HEIGHT - 1)

        if disaster_map.grid[y][x] == EMPTY:
            return x, y


spawn_x, spawn_y = get_random_empty_cell()

uav = UAV(
    drone_id=1,
    x=spawn_x,
    y=spawn_y
)

MOVE_EVENT = pygame.USEREVENT + 1

pygame.time.set_timer(
    MOVE_EVENT,
    500
)


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


def draw_sensor_range():

    center_x = uav.x * CELL_SIZE + CELL_SIZE // 2
    center_y = uav.y * CELL_SIZE + CELL_SIZE // 2

    radius = uav.sensor_range * CELL_SIZE

    pygame.draw.circle(
        screen,
        (100, 180, 255),
        (center_x, center_y),
        radius,
        1
    )


def draw_uav():

    center_x = uav.x * CELL_SIZE + CELL_SIZE // 2
    center_y = uav.y * CELL_SIZE + CELL_SIZE // 2

    pygame.draw.circle(
        screen,
        (0, 100, 255),
        (center_x, center_y),
        CELL_SIZE // 3
    )


def draw_status():

    battery_text = font.render(
        f"Battery: {uav.battery}%",
        True,
        (0, 0, 0)
    )

    visited_text = font.render(
        f"Visited: {len(uav.visited_cells)}",
        True,
        (0, 0, 0)
    )

    survivors_text = font.render(
        f"Detected Survivors: {len(uav.detected_survivors)}",
        True,
        (0, 0, 0)
    )

    screen.blit(battery_text, (10, 10))
    screen.blit(visited_text, (10, 35))
    screen.blit(survivors_text, (10, 60))


running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == MOVE_EVENT:

            uav.move(disaster_map)
            uav.scan(disaster_map)

    screen.fill((255, 255, 255))

    draw_map()
    draw_sensor_range()
    draw_uav()
    draw_status()

    pygame.display.flip()

    clock.tick(60)

pygame.quit()