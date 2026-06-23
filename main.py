import random
import pygame

from agents.uav import UAV

from swarm.coordinator import (
    SwarmCoordinator
)

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

NUM_UAVS = 5

pygame.init()

screen = pygame.display.set_mode(
    (WINDOW_WIDTH, WINDOW_HEIGHT)
)

pygame.display.set_caption(
    "Sector Coordinated UAV Swarm"
)

clock = pygame.time.Clock()

font = pygame.font.SysFont(
    None,
    28
)

disaster_map = DisasterMap(
    GRID_WIDTH,
    GRID_HEIGHT
)

disaster_map.generate()

coordinator = SwarmCoordinator(
    GRID_WIDTH,
    GRID_HEIGHT,
    NUM_UAVS
)


def get_random_empty_cell():

    while True:

        x = random.randint(
            0,
            GRID_WIDTH - 1
        )

        y = random.randint(
            0,
            GRID_HEIGHT - 1
        )

        if disaster_map.grid[y][x] == EMPTY:
            return x, y


uav_colors = [
    (0, 100, 255),
    (255, 0, 0),
    (0, 180, 0),
    (180, 0, 180),
    (255, 180, 0)
]

uavs = []

for i in range(NUM_UAVS):

    spawn_x, spawn_y = get_random_empty_cell()

    uavs.append(
        UAV(
            i + 1,
            spawn_x,
            spawn_y,
            uav_colors[i]
        )
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

            rect = pygame.Rect(
                x * CELL_SIZE,
                y * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )

            pygame.draw.rect(
                screen,
                colors[
                    disaster_map.grid[y][x]
                ],
                rect
            )

            pygame.draw.rect(
                screen,
                (180, 180, 180),
                rect,
                1
            )


def draw_uavs():

    for uav in uavs:

        center_x = (
            uav.x * CELL_SIZE +
            CELL_SIZE // 2
        )

        center_y = (
            uav.y * CELL_SIZE +
            CELL_SIZE // 2
        )

        pygame.draw.circle(
            screen,
            uav.color,
            (
                center_x,
                center_y
            ),
            CELL_SIZE // 3
        )


def draw_status():

    coverage = set()

    battery_sum = 0

    for uav in uavs:

        coverage.update(
            uav.visited_cells
        )

        battery_sum += uav.battery

    avg_battery = (
        battery_sum /
        NUM_UAVS
    )

    text1 = font.render(
        f"Coverage: {len(coverage)}",
        True,
        (0, 0, 0)
    )

    text2 = font.render(
        f"Avg Battery: {avg_battery:.1f}%",
        True,
        (0, 0, 0)
    )

    text3 = font.render(
        f"Shared Survivors: {len(coordinator.get_survivors())}",
        True,
        (0, 0, 0)
    )

    screen.blit(text1, (10, 10))
    screen.blit(text2, (10, 35))
    screen.blit(text3, (10, 60))


running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == MOVE_EVENT:

            for uav in uavs:

                sector = coordinator.get_sector(
                    uav.id
                )

                uav.move(
                    disaster_map,
                    sector
                )

                uav.scan(
                    disaster_map,
                    coordinator
                )

    screen.fill(
        (255, 255, 255)
    )

    draw_map()

    draw_uavs()

    draw_status()

    pygame.display.flip()

    clock.tick(60)

pygame.quit()