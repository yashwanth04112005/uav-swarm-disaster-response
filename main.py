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

SPEED_INTERVALS = [800, 400, 200, 100, 50]
SPEED_LABELS = ["0.5x", "1.0x", "2.0x", "4.0x", "8.0x"]
current_speed_idx = 1

MOVE_INTERVAL = SPEED_INTERVALS[current_speed_idx]
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
big_font = pygame.font.SysFont(None, 30 if WINDOW_WIDTH < 1000 else 36, bold=True)


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
# 3D ISOMETRIC VIEWER
# ==================================================

viewer = Viewer3D(
    grid_width=GRID_WIDTH,
    grid_height=GRID_HEIGHT,
    grid_depth=GRID_DEPTH,
    window_width=WINDOW_WIDTH,
    window_height=WINDOW_HEIGHT
)


# ==================================================
# SIMULATION STATE & RESET FUNCTION
# ==================================================

disaster_map = None
coordinator = None
uavs = []
mission_complete = False
show_scorecard = False
paused = False


def get_random_empty_cell_in_sector(dmap, start_x, end_x):
    attempts = 0
    max_attempts = GRID_WIDTH * GRID_HEIGHT * 10

    while attempts < max_attempts:
        x = random.randint(start_x, end_x)
        y = random.randint(0, GRID_HEIGHT - 1)
        if dmap.grid[0][y][x] == EMPTY:
            return x, y
        attempts += 1

    return start_x, 0


def reset_simulation():
    global disaster_map, coordinator, uavs, mission_complete, show_scorecard

    disaster_map = DisasterMap(
        GRID_WIDTH,
        GRID_HEIGHT,
        GRID_DEPTH
    )
    disaster_map.generate()

    coordinator = SwarmCoordinator(
        GRID_WIDTH,
        GRID_HEIGHT,
        GRID_DEPTH,
        NUM_UAVS
    )

    uavs = []
    viewer.visual_positions.clear()

    for i in range(NUM_UAVS):
        uav_id = i + 1
        sector = coordinator.get_sector(uav_id)
        start_x, end_x = sector

        spawn_x, spawn_y = get_random_empty_cell_in_sector(disaster_map, start_x, end_x)

        uav = UAV(
            drone_id=uav_id,
            x=spawn_x,
            y=spawn_y,
            z=0,
            color=uav_colors[i],
            search_altitude=2
        )
        uavs.append(uav)

        coordinator.update_uav_position(uav_id, uav.get_position())
        coordinator.set_base(uav_id, uav.base_position)
        coordinator.add_coverage(uav.get_position())

    mission_complete = False
    show_scorecard = False
    print("[SIMULATION] Environment & Swarm regenerated.")


# Initialize first run
reset_simulation()


# ==================================================
# PYGAME TIMERS
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


def apply_speed(idx):
    global current_speed_idx, MOVE_INTERVAL
    current_speed_idx = max(0, min(len(SPEED_INTERVALS) - 1, idx))
    MOVE_INTERVAL = SPEED_INTERVALS[current_speed_idx]
    pygame.time.set_timer(MOVE_EVENT, MOVE_INTERVAL)
    print(f"[SPEED] Swarm speed set to {SPEED_LABELS[current_speed_idx]} ({MOVE_INTERVAL}ms)")


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
    panel_h = 360 if WINDOW_HEIGHT < 700 else 390

    # Modern dark translucent panel
    hud_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    bg_hud_col = (10, 16, 26, 235) if viewer.thermal_mode else (25, 30, 42, 230)
    border_hud_col = (40, 95, 140, 210) if viewer.thermal_mode else (60, 75, 100, 200)

    pygame.draw.rect(
        hud_surf,
        bg_hud_col,
        (0, 0, panel_w, panel_h),
        border_radius=10
    )
    pygame.draw.rect(
        hud_surf,
        border_hud_col,
        (0, 0, panel_w, panel_h),
        width=1,
        border_radius=10
    )
    screen.blit(hud_surf, (panel_x, panel_y))

    # Header
    title_str = "FLIR THERMAL HUD" if viewer.thermal_mode else "SWARM TELEMETRY 3D"
    title_col = (110, 240, 255) if viewer.thermal_mode else (240, 245, 255)
    title = bold_font.render(title_str, True, title_col)
    screen.blit(title, (panel_x + 14, panel_y + 12))

    # Mode / Pause indicator
    status_indicator = f"Speed: {SPEED_LABELS[current_speed_idx]}"
    if paused:
        status_indicator += " [PAUSED]"
    stat_txt = small_font.render(status_indicator, True, (255, 200, 60) if paused else (160, 190, 220))
    screen.blit(stat_txt, (panel_x + 14, panel_y + 36))

    # Metrics
    metrics = [
        (f"Coverage: {coverage_count} ({coverage_percentage:.1f}%)", (160, 210, 255)),
        (f"Avg Battery: {avg_battery:.1f}%", (100, 230, 150) if avg_battery > 30 else (255, 90, 90)),
        (f"Survivors Detected: {detected}", (255, 215, 60)),
        (f"Survivors Rescued: {rescued}", (80, 240, 120))
    ]

    curr_y = panel_y + 60
    for label, col in metrics:
        txt = font.render(label, True, col)
        screen.blit(txt, (panel_x + 14, curr_y))
        curr_y += 23

    # Separator
    pygame.draw.line(
        screen,
        (45, 60, 80),
        (panel_x + 14, curr_y + 4),
        (panel_x + panel_w - 14, curr_y + 4),
        1
    )
    curr_y += 12

    # UAV Live Telemetry
    uav_header = bold_font.render("UAV STATUS", True, (200, 215, 235))
    screen.blit(uav_header, (panel_x + 14, curr_y))
    curr_y += 24

    for uav in uavs:
        uav_str = f"UAV {uav.id}: {uav.status[:9]} | z:{uav.z} | {uav.battery}%"
        txt = small_font.render(uav_str, True, uav.color)
        screen.blit(txt, (panel_x + 14, curr_y))
        curr_y += 20

    if mission_complete:
        curr_y += 4
        m_txt = small_font.render("[Tab] Toggle Debrief Card", True, (50, 255, 130))
        screen.blit(m_txt, (panel_x + 14, curr_y))


# ==================================================
# MISSION DEBRIEF & EFFICIENCY SCORECARD
# ==================================================

def draw_mission_debrief():

    overlay = pygame.Surface(
        (
            WINDOW_WIDTH,
            WINDOW_HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            8,
            12,
            20,
            205
        )
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    card_w = min(560, WINDOW_WIDTH - 60)
    card_h = min(470, WINDOW_HEIGHT - 60)
    card_x = (WINDOW_WIDTH - card_w) // 2
    card_y = (WINDOW_HEIGHT - card_h) // 2

    # Tactical Debrief Card Surface
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (16, 22, 34, 250), (0, 0, card_w, card_h), border_radius=12)
    pygame.draw.rect(card_surf, (50, 215, 130, 230), (0, 0, card_w, card_h), width=2, border_radius=12)
    screen.blit(card_surf, (card_x, card_y))

    # Header Title
    title = big_font.render("MISSION DEBRIEF & SCORECARD", True, (50, 255, 130))
    screen.blit(title, (card_x + (card_w - title.get_width()) // 2, card_y + 16))

    rescued = len(coordinator.get_rescued_survivors())
    cov_pct = coordinator.get_coverage_percentage()
    mttr = coordinator.get_mean_time_to_rescue()
    total_dist = sum(u.total_distance for u in uavs)
    total_energy = sum(u.total_energy_consumed for u in uavs)
    total_recharges = sum(u.recharge_count for u in uavs)

    # Performance Evaluation Grade
    if cov_pct >= 60:
        grade = "GRADE S (OPTIMAL COORDINATION)"
        grade_col = (50, 255, 130)
    elif cov_pct >= 40:
        grade = "GRADE A (EXCELLENT PERFORMANCE)"
        grade_col = (100, 220, 255)
    else:
        grade = "GRADE B (SUCCESSFUL RESCUE)"
        grade_col = (255, 200, 60)

    sub_txt = font.render(f"Fleet Evaluation: {grade}", True, grade_col)
    screen.blit(sub_txt, (card_x + (card_w - sub_txt.get_width()) // 2, card_y + 54))

    # 4 Key Summary Metric Badges (2x2 Grid)
    metrics_data = [
        ("Survivors Rescued", f"{rescued} / {rescued} (100%)", (80, 240, 120)),
        ("Mean Time to Rescue (MTTR)", f"{mttr:.1f} ticks", (255, 215, 60)),
        ("Total 3D Flight Distance", f"{total_dist} voxels", (160, 210, 255)),
        ("Energy & Recharge Cycles", f"{total_energy} steps | {total_recharges} charges", (255, 140, 200))
    ]

    grid_w = (card_w - 50) // 2
    grid_h = 50
    for idx, (label, val, col) in enumerate(metrics_data):
        gx = card_x + 20 + (idx % 2) * (grid_w + 10)
        gy = card_y + 86 + (idx // 2) * (grid_h + 8)

        m_surf = pygame.Surface((grid_w, grid_h), pygame.SRCALPHA)
        pygame.draw.rect(m_surf, (26, 34, 48, 220), (0, 0, grid_w, grid_h), border_radius=6)
        screen.blit(m_surf, (gx, gy))

        lbl = small_font.render(label, True, (160, 175, 195))
        val_txt = bold_font.render(val, True, col)
        screen.blit(lbl, (gx + 10, gy + 5))
        screen.blit(val_txt, (gx + 10, gy + 24))

    # Fleet Telemetry Table
    tbl_y = card_y + 215
    tbl_header = bold_font.render("FLEET TELEMETRY BREAKDOWN", True, (210, 225, 245))
    screen.blit(tbl_header, (card_x + 20, tbl_y))

    col_hdr = small_font.render("Drone ID         Distance         Rescues         Charges         Battery", True, (130, 150, 175))
    screen.blit(col_hdr, (card_x + 20, tbl_y + 24))

    pygame.draw.line(screen, (45, 60, 80), (card_x + 20, tbl_y + 42), (card_x + card_w - 20, tbl_y + 42), 1)

    row_y = tbl_y + 48
    for uav in uavs:
        row_str = f"UAV {uav.id}               {uav.total_distance:4d}              {uav.rescued_count:2d}               {uav.recharge_count:2d}              {uav.battery:3d}%"
        row_txt = small_font.render(row_str, True, uav.color)
        screen.blit(row_txt, (card_x + 20, row_y))
        row_y += 19

    # Footer Action Prompt
    footer_str = "Press [R] New Mission  |  [Tab] Toggle Scorecard  |  [T] Thermal View"
    footer_txt = small_font.render(footer_str, True, (140, 190, 240))
    screen.blit(footer_txt, (card_x + (card_w - footer_txt.get_width()) // 2, card_y + card_h - 24))


# ==================================================
# MAIN SIMULATION LOOP
# ==================================================

def run_simulation():
    global running, paused, mission_complete, show_scorecard

    running = True

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

                # Camera 90-degree rotations
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    viewer.rotate_counter_clockwise()

                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    viewer.rotate_clockwise()

                # Pause / Resume
                elif event.key == pygame.K_SPACE:
                    paused = not paused

                # Thermal / Night Vision Mode
                elif event.key == pygame.K_t:
                    viewer.toggle_thermal_mode()

                # Regenerate & Restart Simulation
                elif event.key == pygame.K_r:
                    reset_simulation()

                # Toggle Debrief Scorecard
                elif event.key == pygame.K_TAB:
                    show_scorecard = not show_scorecard

                # Speed Adjustments (+ / - or UP / DOWN)
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_UP):
                    apply_speed(current_speed_idx + 1)

                elif event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE, pygame.K_DOWN):
                    apply_speed(current_speed_idx - 1)

            # UAV Movement
            elif event.type == MOVE_EVENT:

                if not paused:

                    coordinator.current_tick += 1

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
                show_scorecard = True
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

        if mission_complete and show_scorecard:
            draw_mission_debrief()

        pygame.display.flip()

        clock.tick(60)

    # Shutdown
    pygame.quit()


if __name__ == "__main__":
    run_simulation()