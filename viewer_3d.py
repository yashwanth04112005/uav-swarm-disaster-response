"""
Isometric 3D Viewer module for UAV Swarm Disaster Response.
Features:
- Procedural 3D Quadcopter Drones (carbon X-frame, 4 motor pods, animated spinning rotors, LED navigation lights, camera gimbal).
- Architectural Buildings (window lattices, rooftop helipads, HVAC units, radio antenna spires with blinking warning lights).
- Dynamic Volumetric Hazards (pulsing fire voxels and rising smoke puffs).
- High-Tech Base Stations & Pulsing Survivor Distress Beacons.
- Strict Painter's Algorithm Depth Sorting across 4 camera angles (0, 90, 180, 270 deg).
"""

import math
import pygame
from environment.map import EMPTY, OBSTACLE, HAZARD, SURVIVOR, RESCUED


class Viewer3D:

    def __init__(
        self,
        grid_width=25,
        grid_height=20,
        grid_depth=6,
        tile_width=None,
        tile_height=None,
        layer_height=None,
        window_width=880,
        window_height=640
    ):

        self.grid_width = grid_width
        self.grid_height = grid_height
        self.grid_depth = grid_depth

        self.window_width = window_width
        self.window_height = window_height

        # Auto-compute tile sizes to fit window if not explicitly given
        if tile_width is None:
            available_w = max(400, window_width - 240)
            max_grid_span = grid_width + grid_height
            calc_tw = int((available_w * 2) / (max_grid_span + 2))
            self.tile_width = max(22, min(36, (calc_tw // 2) * 2))
        else:
            self.tile_width = tile_width

        self.tile_height = self.tile_width // 2 if tile_height is None else tile_height
        self.layer_height = max(11, int(self.tile_width * 0.52)) if layer_height is None else layer_height

        # Current camera rotation: 0 = 0 deg, 1 = 90 deg, 2 = 180 deg, 3 = 270 deg
        self.view_angle = 0
        self.view_names = ["0° (North)", "90° (East)", "180° (South)", "270° (West)"]

        # Calculate origin offset so the map is nicely centered with HUD clearance
        available_w = window_width - 230
        self.origin_x = available_w // 2 - 10
        self.origin_y = max(110, int(window_height * 0.27))

        # Color Palette
        self.COLOR_BG = (238, 242, 248)
        self.COLOR_GRID = (210, 216, 226)
        self.COLOR_COVERAGE = (180, 220, 255)

        # Base building concrete colors
        self.BUILDING_FACES = (
            (165, 172, 185),  # Top (sunlit)
            (125, 132, 145),  # Left (ambient)
            (95, 102, 115)    # Right (shadow)
        )
        self.BUILDING_OUTLINE = (65, 70, 80)

        # Window colors
        self.COLOR_WINDOW_LIT = (245, 235, 170)
        self.COLOR_WINDOW_CYAN = (195, 230, 255)
        self.COLOR_WINDOW_DARK = (55, 62, 75)

        # Sector colors (soft pastels)
        self.SECTOR_COLORS = [
            (225, 238, 255),
            (255, 230, 230),
            (230, 255, 230),
            (248, 230, 255),
            (255, 246, 225)
        ]

        self.font = pygame.font.SysFont(None, 20)
        self.bold_font = pygame.font.SysFont(None, 22, bold=True)
        self.small_font = pygame.font.SysFont(None, 16)
        self.tiny_font = pygame.font.SysFont(None, 14, bold=True)

    # --------------------------------------------------
    # ROTATION CONTROLS
    # --------------------------------------------------

    def rotate_clockwise(self):
        self.view_angle = (self.view_angle + 1) % 4

    def rotate_counter_clockwise(self):
        self.view_angle = (self.view_angle - 1) % 4

    # --------------------------------------------------
    # COORDINATE TRANSFORMATION
    # --------------------------------------------------

    def rotate_coords(self, x, y):
        """Map grid (x, y) to rotated coordinates (rx, ry) based on current view."""
        w, h = self.grid_width, self.grid_height
        if self.view_angle == 0:
            return x, y
        elif self.view_angle == 1:
            return y, (w - 1 - x)
        elif self.view_angle == 2:
            return (w - 1 - x), (h - 1 - y)
        elif self.view_angle == 3:
            return (h - 1 - y), x
        return x, y

    def project(self, x, y, z):
        """Project 3D grid coordinate (x, y, z) into 2D isometric screen space."""
        rx, ry = self.rotate_coords(x, y)
        half_tw = self.tile_width / 2.0
        half_th = self.tile_height / 2.0

        screen_x = self.origin_x + (rx - ry) * half_tw
        screen_y = self.origin_y + (rx + ry) * half_th - z * self.layer_height

        return int(screen_x), int(screen_y)

    # --------------------------------------------------
    # DRAWING: GROUND FLOOR
    # --------------------------------------------------

    def draw_diamond(self, surface, cx, cy, fill_color, outline_color=None):
        """Draw an isometric horizontal diamond centered at (cx, cy)."""
        htw = self.tile_width // 2
        hth = self.tile_height // 2
        points = [
            (cx, cy - hth),
            (cx + htw, cy),
            (cx, cy + hth),
            (cx - htw, cy)
        ]
        pygame.draw.polygon(surface, fill_color, points)
        if outline_color:
            pygame.draw.polygon(surface, outline_color, points, 1)

    # --------------------------------------------------
    # DRAWING: ARCHITECTURAL BUILDING CUBES
    # --------------------------------------------------

    def draw_architectural_building(self, surface, x, y, z, disaster_map):
        """Draws realistic building voxel with office windows and rooftop details."""
        top_cx, top_cy = self.project(x, y, z)
        htw = self.tile_width // 2
        hth = self.tile_height // 2
        lh = self.layer_height

        # 1. Base Concrete Faces
        top_pts = [
            (top_cx, top_cy - hth),
            (top_cx + htw, top_cy),
            (top_cx, top_cy + hth),
            (top_cx - htw, top_cy)
        ]
        left_pts = [
            (top_cx - htw, top_cy),
            (top_cx, top_cy + hth),
            (top_cx, top_cy + hth + lh),
            (top_cx - htw, top_cy + lh)
        ]
        right_pts = [
            (top_cx, top_cy + hth),
            (top_cx + htw, top_cy),
            (top_cx + htw, top_cy + lh),
            (top_cx, top_cy + hth + lh)
        ]

        pygame.draw.polygon(surface, self.BUILDING_FACES[0], top_pts)
        pygame.draw.polygon(surface, self.BUILDING_FACES[1], left_pts)
        pygame.draw.polygon(surface, self.BUILDING_FACES[2], right_pts)

        # 2. Window Lattices on Left and Right Facades
        # 2 windows across each face
        win_w = max(2, htw // 4)
        win_h = max(2, lh // 3)

        # Left facade windows
        for row in range(2):
            for col in range(2):
                h_seed = (x * 17 + y * 31 + z * 7 + row * 3 + col) % 5
                win_col = self.COLOR_WINDOW_CYAN if h_seed in (0, 1) else (
                    self.COLOR_WINDOW_LIT if h_seed == 2 else self.COLOR_WINDOW_DARK
                )
                # Interpolate on left parallelogram
                u = 0.25 + col * 0.45
                v = 0.25 + row * 0.45
                wx = int((top_cx - htw) * (1 - u) + top_cx * u)
                wy = int(top_cy * (1 - u) + (top_cy + hth) * u + lh * v)
                pygame.draw.rect(surface, win_col, (wx - 1, wy - 1, win_w, win_h))

        # Right facade windows
        for row in range(2):
            for col in range(2):
                h_seed = (x * 19 + y * 23 + z * 11 + row * 5 + col) % 5
                win_col = self.COLOR_WINDOW_CYAN if h_seed in (0, 2) else (
                    self.COLOR_WINDOW_LIT if h_seed == 1 else self.COLOR_WINDOW_DARK
                )
                u = 0.25 + col * 0.45
                v = 0.25 + row * 0.45
                wx = int(top_cx * (1 - u) + (top_cx + htw) * u)
                wy = int((top_cy + hth) * (1 - u) + top_cy * u + lh * v)
                pygame.draw.rect(surface, win_col, (wx - 1, wy - 1, win_w, win_h))

        # 3. Solid Edges Outline
        pygame.draw.polygon(surface, self.BUILDING_OUTLINE, top_pts, 1)
        pygame.draw.polygon(surface, self.BUILDING_OUTLINE, left_pts, 1)
        pygame.draw.polygon(surface, self.BUILDING_OUTLINE, right_pts, 1)

        # 4. Rooftop Features (if this is the top of the building column)
        is_rooftop = (z == self.grid_depth - 1) or (disaster_map.grid[z + 1][y][x] != OBSTACLE)
        if is_rooftop:
            # Parapet inset ledge
            p_pts = [
                (top_cx, top_cy - hth + 2),
                (top_cx + htw - 3, top_cy),
                (top_cx, top_cy + hth - 2),
                (top_cx - htw + 3, top_cy)
            ]
            pygame.draw.polygon(surface, (135, 142, 155), p_pts)
            pygame.draw.polygon(surface, (85, 92, 105), p_pts, 1)

            feature_type = (x * 7 + y * 13) % 4
            if feature_type == 0:
                # Radio/Communication Antenna with blinking obstacle warning beacon
                antenna_top_y = top_cy - 14
                pygame.draw.line(surface, (80, 85, 95), (top_cx, top_cy), (top_cx, antenna_top_y), 2)
                # Blinking red beacon
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    pygame.draw.circle(surface, (255, 30, 30), (top_cx, antenna_top_y), 2)
                else:
                    pygame.draw.circle(surface, (120, 20, 20), (top_cx, antenna_top_y), 2)

            elif feature_type == 1:
                # Rooftop HVAC Unit (raised metallic box)
                hvac_pts = [
                    (top_cx - 4, top_cy - 3),
                    (top_cx + 4, top_cy - 3),
                    (top_cx + 4, top_cy + 2),
                    (top_cx - 4, top_cy + 2)
                ]
                pygame.draw.polygon(surface, (100, 110, 120), hvac_pts)
                pygame.draw.polygon(surface, (60, 65, 75), hvac_pts, 1)

            elif feature_type == 2:
                # Rooftop Helipad ('H' inside circle)
                pygame.draw.circle(surface, (240, 200, 40), (top_cx, top_cy), 5, 1)
                h_txt = self.tiny_font.render("H", True, (240, 200, 40))
                surface.blit(h_txt, (top_cx - h_txt.get_width() // 2, top_cy - h_txt.get_height() // 2))

    # --------------------------------------------------
    # DRAWING: VOLUMETRIC HAZARDS (PULSING FIRE & SMOKE)
    # --------------------------------------------------

    def draw_volumetric_hazard(self, surface, x, y, z):
        """Renders animated pulsing fire block and rising smoke particles."""
        top_cx, top_cy = self.project(x, y, z)
        htw = self.tile_width // 2
        hth = self.tile_height // 2
        lh = self.layer_height

        # Pulsing flame colors
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.008 + x * 2.0 + y * 1.5)
        top_r = int(230 + pulse * 25)
        top_g = int(90 + pulse * 50)
        top_col = (top_r, top_g, 20)
        left_col = (int(190 + pulse * 30), int(60 + pulse * 20), 10)
        right_col = (int(150 + pulse * 30), 30, 5)

        top_pts = [
            (top_cx, top_cy - hth),
            (top_cx + htw, top_cy),
            (top_cx, top_cy + hth),
            (top_cx - htw, top_cy)
        ]
        left_pts = [
            (top_cx - htw, top_cy),
            (top_cx, top_cy + hth),
            (top_cx, top_cy + hth + lh),
            (top_cx - htw, top_cy + lh)
        ]
        right_pts = [
            (top_cx, top_cy + hth),
            (top_cx + htw, top_cy),
            (top_cx + htw, top_cy + lh),
            (top_cx, top_cy + hth + lh)
        ]

        pygame.draw.polygon(surface, top_col, top_pts)
        pygame.draw.polygon(surface, left_col, left_pts)
        pygame.draw.polygon(surface, right_col, right_pts)
        pygame.draw.polygon(surface, (140, 30, 0), top_pts, 1)

        # Rising smoke puff
        smoke_phase = ((pygame.time.get_ticks() + x * 250 + y * 400) % 1200) / 1200.0
        smoke_y = top_cy - int(smoke_phase * 16)
        smoke_rad = int(3 + smoke_phase * 4)
        smoke_surf = pygame.Surface((smoke_rad * 2, smoke_rad * 2), pygame.SRCALPHA)
        smoke_alpha = int((1.0 - smoke_phase) * 110)
        pygame.draw.circle(smoke_surf, (80, 80, 90, smoke_alpha), (smoke_rad, smoke_rad), smoke_rad)
        surface.blit(smoke_surf, (top_cx - smoke_rad, smoke_y - smoke_rad))

    # --------------------------------------------------
    # DRAWING: PROCEDURAL 3D QUADCOPTER
    # --------------------------------------------------

    def draw_quadcopter(self, surface, uav, ux, uy):
        """
        Renders an authentic 3D X-frame Quadcopter:
        - Aerodynamic carbon central hub in team color.
        - 4 diagonal carbon motor arms.
        - 4 motor hubs with spinning rotor blades (motion blur).
        - Twin front LEDs (status colored) & twin rear red LEDs.
        - Underbody optical sensor / camera gimbal.
        """
        arm_len_x = max(7, self.tile_width // 3)
        arm_len_y = max(4, self.tile_height // 2)

        # 4 Motor Positions (X configuration)
        motor_offsets = [
            (+arm_len_x, -arm_len_y),  # Front-Right
            (-arm_len_x, -arm_len_y),  # Front-Left
            (+arm_len_x, +arm_len_y),  # Rear-Right
            (-arm_len_x, +arm_len_y)   # Rear-Left
        ]

        # 1. Carbon Fiber Arms (cross struts)
        for dx, dy in motor_offsets:
            pygame.draw.line(surface, (40, 44, 52), (ux, uy), (ux + dx, uy + dy), 2)

        # 2. Motor Pods & Spinning Propellers
        rotor_t = pygame.time.get_ticks() * 0.04
        blade_r = max(5, self.tile_width // 5)

        for i, (dx, dy) in enumerate(motor_offsets):
            mx = ux + dx
            my = uy + dy

            # Motor cylinder
            pygame.draw.circle(surface, (55, 60, 70), (mx, my), 3)
            pygame.draw.circle(surface, (25, 28, 35), (mx, my), 1)

            # Spinning Rotor Blade (Motion Blur Disk)
            disk_surf = pygame.Surface((blade_r * 2 + 2, blade_r + 2), pygame.SRCALPHA)
            pygame.draw.ellipse(
                disk_surf,
                (210, 230, 255, 95),
                (1, 1, blade_r * 2, blade_r)
            )
            # Propeller tip streak
            blade_angle = rotor_t + i * (math.pi / 2)
            bx = blade_r + int((blade_r - 1) * math.cos(blade_angle))
            by = (blade_r // 2) + int((blade_r // 2 - 1) * math.sin(blade_angle))
            pygame.draw.circle(disk_surf, (240, 248, 255, 180), (bx, by), 1)

            surface.blit(disk_surf, (mx - blade_r - 1, my - blade_r // 2 - 1))

        # 3. Navigation Status LEDs
        # Front arms (index 0, 1): status color (Green/Cyan/Blue)
        # Rear arms (index 2, 3): Red
        led_blink = (pygame.time.get_ticks() // 200) % 2 == 0
        if uav.status == "RESCUING":
            front_led_col = (0, 180, 255) if led_blink else (0, 80, 150)
        elif uav.status == "RETURNING":
            front_led_col = (255, 170, 0) if led_blink else (140, 80, 0)
        elif uav.status == "CHARGING":
            front_led_col = (255, 220, 0)
        else:
            front_led_col = (40, 255, 120) if led_blink else (20, 120, 50)

        # Front LEDs
        pygame.draw.circle(surface, front_led_col, (ux + motor_offsets[0][0], uy + motor_offsets[0][1]), 2)
        pygame.draw.circle(surface, front_led_col, (ux + motor_offsets[1][0], uy + motor_offsets[1][1]), 2)
        # Rear LEDs
        pygame.draw.circle(surface, (240, 40, 40), (ux + motor_offsets[2][0], uy + motor_offsets[2][1]), 2)
        pygame.draw.circle(surface, (240, 40, 40), (ux + motor_offsets[3][0], uy + motor_offsets[3][1]), 2)

        # 4. Central Drone Chassis / Fuselage
        hub_w = max(10, self.tile_width // 3)
        hub_h = max(6, self.tile_height // 3)

        hub_pts = [
            (ux, uy - hub_h // 2),
            (ux + hub_w // 2, uy),
            (ux, uy + hub_h // 2),
            (ux - hub_w // 2, uy)
        ]
        # Carbon rim
        pygame.draw.polygon(surface, (25, 30, 38), hub_pts)
        pygame.draw.polygon(surface, (60, 68, 80), hub_pts, 1)

        # Team Color Canopy Dome
        canopy_pts = [
            (ux, uy - hub_h // 2 + 1),
            (ux + hub_w // 2 - 2, uy),
            (ux, uy + hub_h // 2 - 1),
            (ux - hub_w // 2 + 2, uy)
        ]
        pygame.draw.polygon(surface, uav.color, canopy_pts)

        # 5. Front Camera Gimbal Sensor Eye
        pygame.draw.circle(surface, (20, 25, 30), (ux, uy - hub_h // 2 - 1), 2)
        pygame.draw.circle(surface, (120, 200, 255), (ux, uy - hub_h // 2 - 1), 1)

        # 6. Drone ID Pill Badge
        badge_txt = self.tiny_font.render(f"{uav.id}", True, (255, 255, 255))
        bw = badge_txt.get_width() + 6
        bh = badge_txt.get_height() + 2
        bx = ux - bw // 2
        by = uy - hub_h // 2 - 10

        pill_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(pill_surf, (20, 25, 35, 210), (0, 0, bw, bh), border_radius=3)
        surface.blit(pill_surf, (bx, by))
        surface.blit(badge_txt, (bx + 3, by + 1))

        # Altitude Tag
        alt_txt = self.tiny_font.render(f"z:{uav.z}", True, (50, 60, 75))
        surface.blit(alt_txt, (ux + arm_len_x + 4, uy - 4))

    # --------------------------------------------------
    # DRAWING: SURVIVORS & BASES
    # --------------------------------------------------

    def draw_survivor_beacon(self, surface, cx, cy, is_rescued):
        """Distress beacon with expanding sonar pulse ring or green rescue shield."""
        if not is_rescued:
            # Active Distress Beacon
            pulse_val = (pygame.time.get_ticks() % 1000) / 1000.0
            pulse_r = int(5 + pulse_val * 9)
            pulse_alpha = int((1.0 - pulse_val) * 180)

            # Pulsing Sonar Ring
            pulse_surf = pygame.Surface((pulse_r * 2 + 2, pulse_r + 2), pygame.SRCALPHA)
            pygame.draw.ellipse(
                pulse_surf,
                (255, 210, 0, pulse_alpha),
                (1, 1, pulse_r * 2, pulse_r),
                1
            )
            surface.blit(pulse_surf, (cx - pulse_r - 1, cy - pulse_r // 2 - 1))

            # Core Beacon
            pygame.draw.circle(surface, (255, 200, 0), (cx, cy), 5)
            pygame.draw.circle(surface, (230, 40, 20), (cx, cy), 3)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 1)

        else:
            # Rescued Medical Cross
            pygame.draw.circle(surface, (34, 160, 60), (cx, cy), 6)
            # White Cross
            pygame.draw.line(surface, (255, 255, 255), (cx - 3, cy), (cx + 3, cy), 2)
            pygame.draw.line(surface, (255, 255, 255), (cx, cy - 3), (cx, cy + 3), 2)

    def draw_base_station(self, surface, bx, by, bz, color):
        """High-tech drone charging launchpad on the ground."""
        cx, cy = self.project(bx, by, bz)
        pad_w = max(12, self.tile_width // 2)
        pad_h = max(6, self.tile_height // 2)

        # Pad Diamond Plate
        pts = [
            (cx, cy - pad_h // 2),
            (cx + pad_w // 2, cy),
            (cx, cy + pad_h // 2),
            (cx - pad_w // 2, cy)
        ]
        pygame.draw.polygon(surface, (45, 50, 62), pts)
        pygame.draw.polygon(surface, color, pts, 1)

        # Charging Target Circle
        pygame.draw.ellipse(surface, (90, 100, 120), (cx - 4, cy - 2, 8, 4), 1)

    # --------------------------------------------------
    # FULL SCENE RENDER (DEPTH SORTED)
    # --------------------------------------------------

    def render(self, screen, disaster_map, coordinator, uavs):
        """Renders the entire 3D simulation with architectural models and quadcopters."""
        screen.fill(self.COLOR_BG)

        # 1. Ground Floor Diamonds
        coverage_set = coordinator.get_coverage()
        sectors = coordinator.sectors

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                cx, cy = self.project(x, y, 0)

                # Sector pastel tint
                sector_idx = 0
                for s_i, (s_start, s_end) in enumerate(sectors):
                    if s_start <= x <= s_end:
                        sector_idx = s_i % len(self.SECTOR_COLORS)
                        break

                floor_color = self.SECTOR_COLORS[sector_idx]

                # Explored ground coverage
                if (x, y) in coverage_set:
                    floor_color = self.COLOR_COVERAGE

                self.draw_diamond(screen, cx, cy, floor_color, self.COLOR_GRID)

        # 2. Gather Entities for Depth Sorting
        # Sorting key: (rx + ry, z, priority)
        # Priority: 0: Solid Cubes, 1: Ground Items, 2: UAVs
        render_queue = []

        for z in range(self.grid_depth):
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    cell = disaster_map.grid[z][y][x]
                    if cell == OBSTACLE:
                        rx, ry = self.rotate_coords(x, y)
                        render_queue.append((rx + ry, z, 0, "BUILDING", (x, y, z)))
                    elif cell == HAZARD:
                        rx, ry = self.rotate_coords(x, y)
                        render_queue.append((rx + ry, z, 0, "HAZARD", (x, y, z)))
                    elif cell == SURVIVOR:
                        rx, ry = self.rotate_coords(x, y)
                        render_queue.append((rx + ry, z, 1, "SURVIVOR", (x, y, z)))
                    elif cell == RESCUED:
                        rx, ry = self.rotate_coords(x, y)
                        render_queue.append((rx + ry, z, 1, "RESCUED", (x, y, z)))

        for uav in uavs:
            bx, by, bz = uav.base_position
            rx, ry = self.rotate_coords(bx, by)
            render_queue.append((rx + ry, bz, 1, "BASE", (bx, by, bz, uav.color)))

        for uav in uavs:
            if uav.status == "DEAD":
                continue
            rx, ry = self.rotate_coords(uav.x, uav.y)
            render_queue.append((rx + ry, uav.z, 2, "UAV", uav))

        # Painter's Algorithm Depth Sort
        render_queue.sort(key=lambda item: (item[0], item[1], item[2]))

        # 3. Draw Target Lines
        for uav in uavs:
            if uav.target and uav.status != "DEAD":
                ux, uy = self.project(uav.x, uav.y, uav.z)
                tx, ty = self.project(uav.target[0], uav.target[1], uav.target[2] if len(uav.target) > 2 else 0)
                # Dotted/dashed target line
                pygame.draw.line(screen, uav.color, (ux, uy), (tx, ty), 2)

        # 4. Render All Sorted Entities
        for _, _, _, item_type, data in render_queue:

            if item_type == "BUILDING":
                x, y, z = data
                self.draw_architectural_building(screen, x, y, z, disaster_map)

            elif item_type == "HAZARD":
                x, y, z = data
                self.draw_volumetric_hazard(screen, x, y, z)

            elif item_type == "SURVIVOR":
                x, y, z = data
                cx, cy = self.project(x, y, z)
                self.draw_survivor_beacon(screen, cx, cy, is_rescued=False)

            elif item_type == "RESCUED":
                x, y, z = data
                cx, cy = self.project(x, y, z)
                self.draw_survivor_beacon(screen, cx, cy, is_rescued=True)

            elif item_type == "BASE":
                bx, by, bz, color = data
                self.draw_base_station(screen, bx, by, bz, color)

            elif item_type == "UAV":
                uav = data

                # Ground Shadow
                gx, gy = self.project(uav.x, uav.y, 0)
                shadow_w = max(14, self.tile_width // 2)
                shadow_h = max(7, self.tile_height // 2)
                shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (40, 45, 55, 115), (0, 0, shadow_w, shadow_h))
                screen.blit(shadow_surf, (gx - shadow_w // 2, gy - shadow_h // 2))

                # Vertical Altitude Drop-Line
                ux, uy = self.project(uav.x, uav.y, uav.z)
                if uav.z > 0:
                    pygame.draw.line(screen, (100, 115, 135), (gx, gy), (ux, uy), 1)

                # Procedural 3D Quadcopter
                self.draw_quadcopter(screen, uav, ux, uy)

        # 5. Top Controls & Camera Banner
        cam_text = self.bold_font.render(f"Camera View: {self.view_names[self.view_angle]}", True, (30, 40, 60))
        screen.blit(cam_text, (20, 15))

        help_text = self.small_font.render("Rotate: [<-] [->] or [A] [D]  |  Space: Pause/Resume", True, (90, 105, 125))
        screen.blit(help_text, (20, 38))
