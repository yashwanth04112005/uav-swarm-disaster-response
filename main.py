import random
import pygame

from agents.uav import UAV
from swarm.coordinator import SwarmCoordinator
from environment.map import (
    DisasterMap,
    EMPTY,
    OBSTACLE,
    HAZARD,
    SURVIVOR,
    RESCUED
)
from viewer_3d import Viewer3D


# ==================================================
# CONFIGURATION
# ==================================================

GRID_WIDTH = 25
GRID_HEIGHT = 20
GRID_DEPTH = 6

WINDOW_WIDTH = 880
WINDOW_HEIGHT = 640

NUM_UAVS = 5

MOVE_INTERVAL = 400
HAZARD_INTERVAL = 8000


# ==================================================
# PYGAME INITIALIZATION
# ==================================================

pygame.init()

screen = pygame.display.set_mode(
    (
        WINDOW_WIDTH,
        WINDOW_HEIGHT
    )
)

pygame.display.set_caption(
    "3D Sector Coordinated UAV Swarm - Disaster Response"
)

clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 20 if WINDOW_WIDTH < 1000 else 22)
small_font = pygame.font.SysFont(None, 17 if WINDOW_WIDTH < 1000 else 19)
bold_font = pygame.font.SysFont(None, 22 if WINDOW_WIDTH < 1000 else 24, bold=True)


# ==================================================
# CREATE 3D DISASTER ENVIRONMENT
# ==================================================

disaster_map = DisasterMap(
    GRID_WIDTH,
    GRID_HEIGHT,
    GRID_DEPTH
)

disaster_map.generate()


# ==================================================
# CREATE SWARM COORDINATOR
# ==================================================

coordinator = SwarmCoordinator(
    GRID_WIDTH,
    GRID_HEIGHT,
    GRID_DEPTH,
    NUM_UAVS
)


# ==================================================
# CREATE 3D ISOMETRIC VIEWER
# ==================================================

viewer = Viewer3D(
    grid_width=GRID_WIDTH,
    grid_height=GRID_HEIGHT,
    grid_depth=GRID_DEPTH,
    window_width=WINDOW_WIDTH,
    window_height=WINDOW_HEIGHT
)


# ==================================================
# UAV COLORS
# ==================================================

uav_colors = [
    (0, 110, 255),    # Blue
    (235, 45, 45),    # Red
    (15, 175, 45),    # Green
    (170, 30, 200),   # Purple
    (240, 150, 10)    # Orange
]


# ==================================================
# RANDOM UAV SPAWN (GROUND LAYER)
# ==================================================

def get_random_empty_cell_in_sector(
    start_x,
    end_x
):

    attempts = 0
    max_attempts = GRID_WIDTH * GRID_HEIGHT * 10

    while attempts < max_attempts:

        x = random.randint(
            start_x,
            end_x
        )

        y = random.randint(
            0,
            GRID_HEIGHT - 1
        )

        # Check ground layer (z = 0)
        if disaster_map.grid[0][y][x] == EMPTY:

            return (
                x,
                y
            )

        attempts += 1

    return (
        start_x,
        0
    )


# ==================================================
# CREATE 3D UAVS
# ==================================================

uavs = []

for i in range(NUM_UAVS):

    uav_id = i + 1

    sector = coordinator.get_sector(
        uav_id
    )

    start_x, end_x = sector

    spawn_x, spawn_y = get_random_empty_cell_in_sector(
        start_x,
        end_x
    )

    uav = UAV(
        drone_id=uav_id,
        x=spawn_x,
        y=spawn_y,
        z=0,
        color=uav_colors[i],
        search_altitude=2
    )

    uavs.append(uav)

    # Register UAV position (x, y, z)
    coordinator.update_uav_position(
        uav_id,
        uav.get_position()
    )

    # Register UAV base (x, y, z)
    coordinator.set_base(
        uav_id,
        uav.base_position
    )

    # Initial ground footprint coverage
    coordinator.add_coverage(
        uav.get_position()
    )


# ==================================================
# PYGAME EVENTS
# ==================================================

MOVE_EVENT = pygame.USEREVENT + 1
HAZARD_EVENT = pygame.USEREVENT + 2

pygame.time.set_timer(
    MOVE_EVENT,
    MOVE_INTERVAL
)

pygame.time.set_timer(
    HAZARD_EVENT,
    HAZARD_INTERVAL
)


# ==================================================
# HUD PANELS (SIDEBAR DASHBOARD)
# ==================================================

def draw_hud():

    coverage_count = len(
        coordinator.get_coverage()
    )

    coverage_percentage = (
        coordinator.get_coverage_percentage()
    )

    detected = len(
        coordinator.get_survivors()
    )

    rescued = len(
        coordinator.get_rescued_survivors()
    )

    avg_battery = (
        sum(u.battery for u in uavs) / len(uavs)
    )

    panel_w = 230 if WINDOW_WIDTH < 1000 else 255
    panel_x = WINDOW_WIDTH - panel_w - 15
    panel_y = 15
    panel_h = 330 if WINDOW_HEIGHT < 700 else 360

    # Modern dark translucent panel
    hud_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(
        hud_surf,
        (25, 30, 42, 230),
        (0, 0, panel_w, panel_h),
        border_radius=10
    )
    pygame.draw.rect(
        hud_surf,
        (60, 75, 100, 200),
        (0, 0, panel_w, panel_h),
        width=1,
        border_radius=10
    )
    screen.blit(hud_surf, (panel_x, panel_y))

    # Header
    title = bold_font.render("SWARM TELEMETRY 3D", True, (240, 245, 255))
    screen.blit(title, (panel_x + 14, panel_y + 12))

    # Metrics
    metrics = [
        (f"Coverage: {coverage_count} ({coverage_percentage:.1f}%)", (160, 210, 255)),
        (f"Avg Battery: {avg_battery:.1f}%", (100, 230, 150) if avg_battery > 30 else (255, 90, 90)),
        (f"Survivors Detected: {detected}", (255, 215, 60)),
        (f"Survivors Rescued: {rescued}", (80, 240, 120))
    ]

    curr_y = panel_y + 40
    for label, col in metrics:
        txt = font.render(label, True, col)
        screen.blit(txt, (panel_x + 14, curr_y))
        curr_y += 24

    # Separator
    pygame.draw.line(
        screen,
        (50, 60, 80),
        (panel_x + 14, curr_y + 4),
        (panel_x + panel_w - 14, curr_y + 4),
        1
    )
    curr_y += 12

    # UAV Live Telemetry
    uav_header = bold_font.render("UAV STATUS", True, (200, 215, 235))
    screen.blit(uav_header, (panel_x + 14, curr_y))
    curr_y += 26

    for uav in uavs:
        # Status text with altitude
        uav_str = f"UAV {uav.id}: {uav.status[:9]} | z:{uav.z} | {uav.battery}%"
        txt = small_font.render(uav_str, True, uav.color)
        screen.blit(txt, (panel_x + 14, curr_y))
        curr_y += 22


# ==================================================
# MISSION COMPLETE OVERLAY
# ==================================================

def draw_mission_complete():

    overlay = pygame.Surface(
        (
            WINDOW_WIDTH,
            WINDOW_HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            15,
            20,
            30,
            150
        )
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    big_font = pygame.font.SysFont(
        None,
        58,
        bold=True
    )

    text = big_font.render(
        "MISSION COMPLETE",
        True,
        (
            50,
            255,
            120
        )
    )

    text_rect = text.get_rect(
        center=(
            WINDOW_WIDTH // 2 - 80,
            WINDOW_HEIGHT // 2 - 20
        )
    )

    screen.blit(
        text,
        text_rect
    )

    rescued = len(
        coordinator.get_rescued_survivors()
    )

    sub_text = bold_font.render(
        f"All {rescued} survivors safely rescued via 3D airspace coordination!",
        True,
        (
            240,
            245,
            255
        )
    )

    sub_rect = sub_text.get_rect(
        center=(
            WINDOW_WIDTH // 2 - 80,
            WINDOW_HEIGHT // 2 + 25
        )
    )

    screen.blit(
        sub_text,
        sub_rect
    )


# ==================================================
# SIMULATION LOOP
# ==================================================

running = True
paused = False
mission_complete = False


while running:

    # ==================================================
    # EVENT HANDLING
    # ==================================================

    for event in pygame.event.get():

        # Quit
        if event.type == pygame.QUIT:
            running = False

        # Keyboard Controls
        elif event.type == pygame.KEYDOWN:

            if event.key in (pygame.K_LEFT, pygame.K_a):
                viewer.rotate_counter_clockwise()

            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                viewer.rotate_clockwise()

            elif event.key == pygame.K_SPACE:
                paused = not paused

        # UAV Movement
        elif event.type == MOVE_EVENT:

            if not paused:

                for uav in uavs:

                    if uav.status == "DEAD":
                        continue

                    sector = coordinator.get_sector(uav.id)

                    # Move UAV (3D A* and altitude sweep)
                    uav.move(
                        disaster_map,
                        sector,
                        coordinator
                    )

                    # Update position
                    coordinator.update_uav_position(
                        uav.id,
                        uav.get_position()
                    )

                    # Update coverage (ground footprint)
                    coordinator.add_coverage_cells(
                        uav.visited_cells
                    )

                    # 3D sensor scan
                    uav.scan(
                        disaster_map,
                        sector,
                        coordinator
                    )

                    # Attempt rescue if target reached
                    uav.attempt_rescue(
                        disaster_map,
                        coordinator
                    )

        # Hazard Expansion
        elif event.type == HAZARD_EVENT:

            if not paused:
                disaster_map.expand_hazards()
                print("[DISASTER] Hazards expanded in 3D.")

    # ==================================================
    # MISSION COMPLETION CHECK (3D VOXEL SCAN)
    # ==================================================

    if not mission_complete:

        active_survivors = sum(
            1 for z in range(disaster_map.depth)
            for y in range(disaster_map.height)
            for x in range(disaster_map.width)
            if disaster_map.grid[z][y][x] == SURVIVOR
        )

        if (
            active_survivors == 0
            and
            len(coordinator.get_rescued_survivors()) > 0
        ):

            mission_complete = True
            print(
                "[MISSION] All survivors rescued. Mission complete!"
            )

    # ==================================================
    # RENDER 3D SCENE & HUD
    # ==================================================

    viewer.render(
        screen,
        disaster_map,
        coordinator,
        uavs
    )

    draw_hud()

    if mission_complete:
        draw_mission_complete()

    pygame.display.flip()

    clock.tick(60)


# ==================================================
# SHUTDOWN
# ==================================================

pygame.quit()