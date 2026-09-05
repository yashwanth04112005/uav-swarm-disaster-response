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
    SURVIVOR,
    RESCUED
)


# ==================================================
# CONFIGURATION
# ==================================================

CELL_SIZE = 30

GRID_WIDTH = 25
GRID_HEIGHT = 20

WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE

NUM_UAVS = 5

MOVE_INTERVAL = 500
HAZARD_INTERVAL = 10000


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
    "Sector Coordinated UAV Swarm"
)

clock = pygame.time.Clock()

font = pygame.font.SysFont(
    None,
    24
)

small_font = pygame.font.SysFont(
    None,
    20
)


# ==================================================
# CREATE DISASTER ENVIRONMENT
# ==================================================

disaster_map = DisasterMap(
    GRID_WIDTH,
    GRID_HEIGHT
)

disaster_map.generate()


# ==================================================
# CREATE SWARM COORDINATOR
# ==================================================

coordinator = SwarmCoordinator(
    GRID_WIDTH,
    GRID_HEIGHT,
    NUM_UAVS
)


# ==================================================
# UAV COLORS
# ==================================================

uav_colors = [
    (0, 100, 255),
    (255, 0, 0),
    (0, 180, 0),
    (180, 0, 180),
    (255, 180, 0)
]


# ==================================================
# RANDOM UAV SPAWN
# ==================================================

def get_random_empty_cell_in_sector(
    start_x,
    end_x
):

    attempts = 0

    max_attempts = (
        GRID_WIDTH *
        GRID_HEIGHT *
        10
    )

    while attempts < max_attempts:

        x = random.randint(
            start_x,
            end_x
        )

        y = random.randint(
            0,
            GRID_HEIGHT - 1
        )

        if (
            disaster_map.grid[y][x]
            == EMPTY
        ):

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
# CREATE UAVS
# ==================================================

uavs = []


for i in range(NUM_UAVS):

    uav_id = i + 1

    sector = coordinator.get_sector(
        uav_id
    )

    start_x, end_x = sector

    spawn_x, spawn_y = (
        get_random_empty_cell_in_sector(
            start_x,
            end_x
        )
    )

    uav = UAV(
        uav_id,
        spawn_x,
        spawn_y,
        uav_colors[i]
    )

    uavs.append(
        uav
    )

    # Register UAV position
    coordinator.update_uav_position(
        uav_id,
        uav.get_position()
    )

    # Register UAV base
    coordinator.set_base(
        uav_id,
        uav.base_position
    )

    # Initial coverage
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
# DRAW DISASTER MAP
# ==================================================

def draw_map():

    colors = {

        EMPTY: (
            240,
            240,
            240
        ),

        OBSTACLE: (
            60,
            60,
            60
        ),

        HAZARD: (
            255,
            140,
            0
        ),

        SURVIVOR: (
            0,
            200,
            0
        ),

        RESCUED: (
            0,
            120,
            0
        )
    }

    for y in range(
        GRID_HEIGHT
    ):

        for x in range(
            GRID_WIDTH
        ):

            rect = pygame.Rect(

                x * CELL_SIZE,

                y * CELL_SIZE,

                CELL_SIZE,

                CELL_SIZE
            )

            cell_type = (
                disaster_map.grid[y][x]
            )

            pygame.draw.rect(

                screen,

                colors.get(
                    cell_type,
                    (255, 255, 255)
                ),

                rect
            )

            pygame.draw.rect(

                screen,

                (180, 180, 180),

                rect,

                1
            )


# ==================================================
# DRAW COVERAGE
# ==================================================

def draw_coverage():

    coverage = (
        coordinator.get_coverage()
    )

    for x, y in coverage:

        if not (
            0 <= x < GRID_WIDTH
            and
            0 <= y < GRID_HEIGHT
        ):

            continue

        cell_type = (
            disaster_map.grid[y][x]
        )

        # Do not cover important map objects
        if cell_type != EMPTY:

            continue

        rect = pygame.Rect(

            x * CELL_SIZE,

            y * CELL_SIZE,

            CELL_SIZE,

            CELL_SIZE
        )

        coverage_surface = pygame.Surface(

            (
                CELL_SIZE,
                CELL_SIZE
            ),

            pygame.SRCALPHA
        )

        coverage_surface.fill(
            (
                100,
                180,
                255,
                80
            )
        )

        screen.blit(
            coverage_surface,
            rect
        )


# ==================================================
# DRAW SENSOR RANGES
# ==================================================

def draw_sensor_ranges():

    for uav in uavs:

        center_x = (
            uav.x * CELL_SIZE
            + CELL_SIZE // 2
        )

        center_y = (
            uav.y * CELL_SIZE
            + CELL_SIZE // 2
        )

        radius = (
            uav.sensor_range
            * CELL_SIZE
        )

        sensor_surface = pygame.Surface(

            (
                WINDOW_WIDTH,
                WINDOW_HEIGHT
            ),

            pygame.SRCALPHA
        )

        pygame.draw.circle(

            sensor_surface,

            (
                100,
                150,
                255,
                25
            ),

            (
                center_x,
                center_y
            ),

            radius
        )

        screen.blit(
            sensor_surface,
            (0, 0)
        )


# ==================================================
# DRAW SECTORS
# ==================================================

def draw_sectors():

    for index, sector in enumerate(
        coordinator.sectors
    ):

        start_x, end_x = sector

        # Draw boundary at start
        line_x = (
            start_x *
            CELL_SIZE
        )

        pygame.draw.line(

            screen,

            (
                80,
                80,
                255
            ),

            (
                line_x,
                0
            ),

            (
                line_x,
                WINDOW_HEIGHT
            ),

            2
        )

        # Sector label
        label = small_font.render(

            f"S{index + 1}",

            True,

            (
                70,
                70,
                180
            )
        )

        screen.blit(

            label,

            (
                start_x * CELL_SIZE + 5,
                WINDOW_HEIGHT - 22
            )
        )


# ==================================================
# DRAW BASES
# ==================================================

def draw_bases():

    for uav in uavs:

        base_x, base_y = (
            uav.base_position
        )

        center_x = (
            base_x * CELL_SIZE
            + CELL_SIZE // 2
        )

        center_y = (
            base_y * CELL_SIZE
            + CELL_SIZE // 2
        )

        pygame.draw.rect(

            screen,

            (
                0,
                0,
                0
            ),

            pygame.Rect(

                center_x - 6,
                center_y - 6,
                12,
                12
            )
        )


# ==================================================
# DRAW TARGET PATHS
# ==================================================

def draw_target_paths():

    for uav in uavs:

        if not uav.target:

            continue

        target_x, target_y = (
            uav.target
        )

        start_x = (
            uav.x * CELL_SIZE
            + CELL_SIZE // 2
        )

        start_y = (
            uav.y * CELL_SIZE
            + CELL_SIZE // 2
        )

        end_x = (
            target_x * CELL_SIZE
            + CELL_SIZE // 2
        )

        end_y = (
            target_y * CELL_SIZE
            + CELL_SIZE // 2
        )

        pygame.draw.line(

            screen,

            uav.color,

            (
                start_x,
                start_y
            ),

            (
                end_x,
                end_y
            ),

            2
        )


# ==================================================
# DRAW UAVS
# ==================================================

def draw_uavs():

    for uav in uavs:

        center_x = (
            uav.x * CELL_SIZE
            + CELL_SIZE // 2
        )

        center_y = (
            uav.y * CELL_SIZE
            + CELL_SIZE // 2
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

        # UAV ID
        text = small_font.render(

            str(uav.id),

            True,

            (255, 255, 255)
        )

        text_rect = (
            text.get_rect(
                center=(
                    center_x,
                    center_y
                )
            )
        )

        screen.blit(
            text,
            text_rect
        )


# ==================================================
# DRAW STATUS
# ==================================================

def draw_status():

    coverage_count = len(
        coordinator.get_coverage()
    )

    coverage_percentage = (
        coordinator
        .get_coverage_percentage()
    )

    detected = len(
        coordinator.get_survivors()
    )

    rescued = len(
        coordinator
        .get_rescued_survivors()
    )

    battery_sum = sum(
        uav.battery
        for uav in uavs
    )

    avg_battery = (
        battery_sum /
        len(uavs)
    )

    # ----------------------------------------------
    # Background panel
    # ----------------------------------------------

    panel = pygame.Surface(

        (
            330,
            135
        ),

        pygame.SRCALPHA
    )

    panel.fill(
        (
            255,
            255,
            255,
            210
        )
    )

    screen.blit(
        panel,
        (5, 5)
    )

    # ----------------------------------------------
    # General statistics
    # ----------------------------------------------

    text1 = font.render(

        f"Coverage: {coverage_count} "
        f"({coverage_percentage:.1f}%)",

        True,

        (0, 0, 0)
    )

    text2 = font.render(

        f"Avg Battery: "
        f"{avg_battery:.1f}%",

        True,

        (0, 0, 0)
    )

    text3 = font.render(

        f"Detected: {detected}",

        True,

        (0, 0, 0)
    )

    text4 = font.render(

        f"Rescued: {rescued}",

        True,

        (0, 0, 0)
    )

    screen.blit(
        text1,
        (10, 8)
    )

    screen.blit(
        text2,
        (10, 34)
    )

    screen.blit(
        text3,
        (10, 60)
    )

    screen.blit(
        text4,
        (10, 86)
    )


# ==================================================
# DRAW UAV STATUS
# ==================================================

def draw_uav_status():

    start_y = 145

    for index, uav in enumerate(
        uavs
    ):

        status_text = (

            f"UAV {uav.id}: "
            f"{uav.status} "
            f"{uav.battery}%"
        )

        text = small_font.render(

            status_text,

            True,

            uav.color
        )

        screen.blit(

            text,

            (
                10,
                start_y +
                index * 22
            )
        )


# ==================================================
# DRAW SURVIVOR MARKERS
# ==================================================

def draw_survivor_markers():

    survivors = (
        coordinator.get_survivors()
    )

    for x, y in survivors:

        center_x = (
            x * CELL_SIZE
            + CELL_SIZE // 2
        )

        center_y = (
            y * CELL_SIZE
            + CELL_SIZE // 2
        )

        # Yellow target ring
        pygame.draw.circle(

            screen,

            (
                255,
                255,
                0
            ),

            (
                center_x,
                center_y
            ),

            CELL_SIZE // 2 - 3,

            2
        )


# ==================================================
# MAIN SIMULATION LOOP
# ==================================================

running = True


while running:

    # ==================================================
    # EVENT HANDLING
    # ==================================================

    for event in pygame.event.get():

        # ----------------------------------------------
        # QUIT
        # ----------------------------------------------

        if event.type == pygame.QUIT:

            running = False

        # ----------------------------------------------
        # UAV MOVEMENT
        # ----------------------------------------------

        elif event.type == MOVE_EVENT:

            for uav in uavs:

                if uav.status == "DEAD":

                    continue

                sector = (
                    coordinator.get_sector(
                        uav.id
                    )
                )

                # Move UAV
                uav.move(

                    disaster_map,

                    sector,

                    coordinator
                )

                # Register position
                coordinator.update_uav_position(

                    uav.id,

                    uav.get_position()
                )

                # Add visited cells
                coordinator.add_coverage_cells(

                    uav.visited_cells
                )

                # Scan environment
                uav.scan(

                    disaster_map,

                    coordinator
                )

                # Attempt rescue if target reached
                uav.attempt_rescue(

                    disaster_map,

                    coordinator
                )

        # ----------------------------------------------
        # HAZARD EXPANSION
        # ----------------------------------------------

        elif event.type == HAZARD_EVENT:

            disaster_map.expand_hazards()

            print(
                "[DISASTER] "
                "Hazards expanded."
            )


    # ==================================================
    # RENDER
    # ==================================================

    screen.fill(
        (
            255,
            255,
            255
        )
    )

    # Base map
    draw_map()

    # Coverage
    draw_coverage()

    # Sensor visualization
    draw_sensor_ranges()

    # Sector boundaries
    draw_sectors()

    # UAV bases
    draw_bases()

    # Survivor target markers
    draw_survivor_markers()

    # Target communication lines
    draw_target_paths()

    # UAVs
    draw_uavs()

    # Main statistics
    draw_status()

    # UAV-specific status
    draw_uav_status()

    pygame.display.flip()

    clock.tick(60)


# ==================================================
# SHUTDOWN
# ==================================================

pygame.quit()