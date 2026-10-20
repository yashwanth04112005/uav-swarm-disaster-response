"""
Isometric 3D Viewer module for UAV Swarm Disaster Response.
Features:
- Smooth 60 FPS Visual Interpolation (drones glide seamlessly instead of jumping).
- Procedural 3D Quadcopter Drones (carbon X-frame, 4 motor pods, animated spinning rotors, LED navigation lights, camera gimbal).
- FLIR / Thermal Night Vision Mode (tactical dark environment, glowing heat signatures, drone searchlight cones).
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

        # Smooth flight visual interpolation: uav_id -> [vx, vy, vz]
        self.visual_positions = {}

        # FLIR / Thermal Night Vision Mode
        self.thermal_mode = False

        # Color Palettes (Day Ops)
        self.COLOR_BG = (140, 185, 240)
        self.COLOR_GRID = (195, 210, 225)
        self.COLOR_COVERAGE = (160, 215, 255)

        self.BUILDING_FACES = (
            (175, 183, 198),  # Top
            (118, 128, 142),  # Left
            (85, 94, 110)     # Right
        )
        self.BUILDING_OUTLINE = (55, 62, 76)

        self.COLOR_WINDOW_LIT = (245, 235, 170)
        self.COLOR_WINDOW_CYAN = (195, 230, 255)
        self.COLOR_WINDOW_DARK = (55, 62, 75)

        self.SECTOR_COLORS = [
            (212, 228, 252),
            (252, 220, 220),
            (220, 248, 220),
            (240, 220, 252),
            (252, 238, 210)
        ]

        # Thermal Ops Palette
        self.THERMAL_BG = (8, 12, 20)
        self.THERMAL_GRID = (22, 36, 52)
        self.THERMAL_FLOOR = (14, 20, 30)
        self.THERMAL_COVERAGE = (25, 65, 100)
        self.THERMAL_BUILDING_FACES = (
            (44, 58, 80),
            (28, 38, 56),
            (18, 26, 40)
        )
        self.THERMAL_BUILDING_OUTLINE = (50, 70, 100)

        # Pre-baked sky gradient surface (drawn once, cached)
        self._sky_surface = None
        self._sky_thermal_surface = None
        self._sky_size = (window_width, window_height)

        # Ember particle system: list of [x, y, vx, vy, life, max_life, r, g, b]
        self._embers = []

        self.font = pygame.font.SysFont(None, 20)
        self.bold_font = pygame.font.SysFont(None, 22, bold=True)
        self.small_font = pygame.font.SysFont(None, 16)
        self.tiny_font = pygame.font.SysFont(None, 14, bold=True)

    # --------------------------------------------------
    # CAMERA & MODE CONTROLS
    # --------------------------------------------------

    def rotate_clockwise(self):
        self.view_angle = (self.view_angle + 1) % 4

    def rotate_counter_clockwise(self):
        self.view_angle = (self.view_angle - 1) % 4

    def toggle_thermal_mode(self):
        self.thermal_mode = not self.thermal_mode

    # --------------------------------------------------
    # SKY GRADIENT BACKGROUND
    # --------------------------------------------------

    def _build_sky_surface(self, w, h, thermal=False):
        """Pre-bake a vertical sky gradient surface."""
        surf = pygame.Surface((w, h))
        for row in range(h):
            t = row / max(1, h - 1)
            if thermal:
                # Deep FLIR blue-black at top -> dark teal at horizon
                r = int(6 + t * 14)
                g = int(10 + t * 20)
                b = int(18 + t * 26)
            else:
                # Cerulean sky at top -> warm hazy horizon
                r = int(80 + t * 105)
                g = int(140 + t * 62)
                b = int(215 + t * 28)
            surf.fill((r, g, b), (0, row, w, 1))
        return surf

    def draw_sky(self, surface):
        """Draw cached sky gradient; rebuilds if thermal mode changed."""
        w, h = self._sky_size
        if self.thermal_mode:
            if self._sky_thermal_surface is None:
                self._sky_thermal_surface = self._build_sky_surface(w, h, thermal=True)
            surface.blit(self._sky_thermal_surface, (0, 0))
        else:
            if self._sky_surface is None:
                self._sky_surface = self._build_sky_surface(w, h, thermal=False)
            surface.blit(self._sky_surface, (0, 0))

    # --------------------------------------------------
    # DEPTH FOG HELPER
    # --------------------------------------------------

    def _fog_blend(self, color, dist_t, thermal=False):
        """Blend a tile colour toward the sky/horizon colour with distance."""
        fog_t = min(1.0, dist_t * 0.55)   # max 55% fog at map edge
        if thermal:
            fog_r, fog_g, fog_b = 14, 26, 38
        else:
            fog_r, fog_g, fog_b = 185, 210, 240  # hazy horizon colour
        r = int(color[0] * (1 - fog_t) + fog_r * fog_t)
        g = int(color[1] * (1 - fog_t) + fog_g * fog_t)
        b = int(color[2] * (1 - fog_t) + fog_b * fog_t)
        return (r, g, b)

    # --------------------------------------------------
    # EMBER PARTICLE SYSTEM
    # --------------------------------------------------

    def _spawn_embers(self, screen_x, screen_y):
        """Probabilistically spawn fire embers at a hazard cell."""
        import random
        if random.random() < 0.25:   # 25% chance each render frame
            life = random.randint(28, 55)
            vx = random.uniform(-0.6, 0.6)
            vy = random.uniform(-1.5, -0.6)
            # Ember colour: bright orange/yellow to red
            r = random.randint(220, 255)
            g = random.randint(60, 160)
            b = random.randint(0, 20)
            self._embers.append([screen_x, screen_y, vx, vy, life, life, r, g, b])

    def _update_and_draw_embers(self, surface):
        """Advance ember physics and draw surviving particles."""
        alive = []
        for em in self._embers:
            em[0] += em[2]           # x drift
            em[1] += em[3]           # y rise
            em[3] *= 0.97            # slow rise over time
            em[2] += 0.02 * (0.5 - (hash(id(em)) % 100) / 100.0)  # wobble
            em[4] -= 1               # age
            if em[4] > 0:
                t = em[4] / em[5]
                alpha = int(t * 230)
                radius = max(1, int(t * 2.5))
                em_surf = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(em_surf, (em[6], em[7], em[8], alpha),
                                   (radius + 1, radius + 1), radius)
                surface.blit(em_surf, (int(em[0]) - radius - 1, int(em[1]) - radius - 1))
                alive.append(em)
        # Cap particle count to avoid slowdown
        self._embers = alive[-300:]

    # --------------------------------------------------
    # SOS VERTICAL LIGHT BEAM
    # --------------------------------------------------

    def draw_sos_beam(self, surface, cx, cy):
        """Draw a vertical SOS light column rising from a survivor."""
        beam_h = 80
        num_layers = 6
        t_ms = pygame.time.get_ticks()
        # Pulse the beam intensity slowly
        pulse = 0.55 + 0.45 * math.sin(t_ms * 0.004)
        beam_surf = pygame.Surface((18, beam_h), pygame.SRCALPHA)
        for i in range(num_layers):
            layer_t = i / num_layers          # 0=top, 1=bottom
            alpha = int(pulse * (1.0 - layer_t) * 80)
            stripe_h = beam_h // num_layers
            color = (255, 240, 80, alpha) if not self.thermal_mode else (140, 255, 210, alpha)
            pygame.draw.rect(beam_surf, color, (0, i * stripe_h, 18, stripe_h + 1))
        surface.blit(beam_surf, (cx - 9, cy - beam_h))

    # --------------------------------------------------
    # ROTOR DOWNWASH GROUND EFFECT
    # --------------------------------------------------

    def draw_rotor_downwash(self, surface, gx, gy, altitude_z):
        """Faint expanding ring on ground below a flying drone."""
        if altitude_z < 0.3:
            return
        t_ms = pygame.time.get_ticks()
        # Two counter-phase rings so it looks like air pulses
        for phase_offset in (0, 500):
            ring_t = ((t_ms + phase_offset) % 700) / 700.0
            ring_r_x = int(self.tile_width * 0.55 * (0.4 + ring_t * 0.6))
            ring_r_y = max(3, ring_r_x // 2)
            alpha = int((1.0 - ring_t) * 55)
            dw_surf = pygame.Surface((ring_r_x * 2 + 2, ring_r_y * 2 + 2), pygame.SRCALPHA)
            col = (120, 200, 255, alpha) if self.thermal_mode else (180, 200, 220, alpha)
            pygame.draw.ellipse(dw_surf, col, (1, 1, ring_r_x * 2, ring_r_y * 2), 1)
            surface.blit(dw_surf, (gx - ring_r_x - 1, gy - ring_r_y - 1))

    # --------------------------------------------------
    # COORDINATE TRANSFORMATION
    # --------------------------------------------------

    def rotate_coords(self, x, y):
        """Map grid (x, y) to rotated coordinates (rx, ry) based on current view."""
        w, h = self.grid_width, self.grid_height
        if self.view_angle == 0:
            return x, y
        elif self.view_angle == 1:
            return y, (w - 1.0 - x)
        elif self.view_angle == 2:
            return (w - 1.0 - x), (h - 1.0 - y)
        elif self.view_angle == 3:
            return (h - 1.0 - y), x
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
        """Draws realistic building voxel with office windows, AO edges, and rooftop details."""
        top_cx, top_cy = self.project(x, y, z)
        htw = self.tile_width // 2
        hth = self.tile_height // 2
        lh = self.layer_height

        faces = self.THERMAL_BUILDING_FACES if self.thermal_mode else self.BUILDING_FACES
        outline = self.THERMAL_BUILDING_OUTLINE if self.thermal_mode else self.BUILDING_OUTLINE

        # Depth fog factor: further from camera = more fog
        rx, ry = self.rotate_coords(x, y)
        max_dist = self.grid_width + self.grid_height
        dist_t = (rx + ry) / max(1, max_dist)

        def fog(c):
            return self._fog_blend(c, dist_t, self.thermal_mode)

        # 1. Base Concrete Faces with fog
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

        pygame.draw.polygon(surface, fog(faces[0]), top_pts)
        pygame.draw.polygon(surface, fog(faces[1]), left_pts)
        pygame.draw.polygon(surface, fog(faces[2]), right_pts)

        # 1b. Ambient Occlusion: dark strip at base of left & right faces (fast solid-colour)
        ao_dark = (18, 20, 28) if self.thermal_mode else (38, 42, 54)
        ao_pts_left = [
            (top_cx - htw, top_cy + lh - 4),
            (top_cx, top_cy + hth + lh - 4),
            (top_cx, top_cy + hth + lh),
            (top_cx - htw, top_cy + lh)
        ]
        ao_pts_right = [
            (top_cx, top_cy + hth + lh - 4),
            (top_cx + htw, top_cy + lh - 4),
            (top_cx + htw, top_cy + lh),
            (top_cx, top_cy + hth + lh)
        ]
        pygame.draw.polygon(surface, ao_dark, ao_pts_left)
        pygame.draw.polygon(surface, ao_dark, ao_pts_right)

        # 1c. AO inner crease line at corner edge
        crease_col = (35, 38, 48) if self.thermal_mode else (55, 60, 72)
        pygame.draw.line(surface, crease_col, (top_cx, top_cy + hth), (top_cx, top_cy + hth + lh), 1)

        # 2. Window Lattices on Left and Right Facades
        win_w = max(2, htw // 4)
        win_h = max(2, lh // 3)

        for row in range(2):
            for col in range(2):
                h_seed = (x * 17 + y * 31 + z * 7 + row * 3 + col) % 5
                if self.thermal_mode:
                    win_col = (110, 230, 255) if h_seed in (0, 1) else (30, 42, 60)
                else:
                    win_col = self.COLOR_WINDOW_CYAN if h_seed in (0, 1) else (
                        self.COLOR_WINDOW_LIT if h_seed == 2 else self.COLOR_WINDOW_DARK
                    )
                u = 0.25 + col * 0.45
                v = 0.25 + row * 0.45
                wx = int((top_cx - htw) * (1 - u) + top_cx * u)
                wy = int(top_cy * (1 - u) + (top_cy + hth) * u + lh * v)
                pygame.draw.rect(surface, win_col, (wx - 1, wy - 1, win_w, win_h))

        for row in range(2):
            for col in range(2):
                h_seed = (x * 19 + y * 23 + z * 11 + row * 5 + col) % 5
                if self.thermal_mode:
                    win_col = (110, 230, 255) if h_seed in (0, 2) else (30, 42, 60)
                else:
                    win_col = self.COLOR_WINDOW_CYAN if h_seed in (0, 2) else (
                        self.COLOR_WINDOW_LIT if h_seed == 1 else self.COLOR_WINDOW_DARK
                    )
                u = 0.25 + col * 0.45
                v = 0.25 + row * 0.45
                wx = int(top_cx * (1 - u) + (top_cx + htw) * u)
                wy = int((top_cy + hth) * (1 - u) + top_cy * u + lh * v)
                pygame.draw.rect(surface, win_col, (wx - 1, wy - 1, win_w, win_h))

        # 3. Solid Edges Outline
        pygame.draw.polygon(surface, outline, top_pts, 1)
        pygame.draw.polygon(surface, outline, left_pts, 1)
        pygame.draw.polygon(surface, outline, right_pts, 1)

        # 4. Rooftop Features
        is_rooftop = (z == self.grid_depth - 1) or (disaster_map.grid[z + 1][y][x] != OBSTACLE)
        if is_rooftop:
            p_pts = [
                (top_cx, top_cy - hth + 2),
                (top_cx + htw - 3, top_cy),
                (top_cx, top_cy + hth - 2),
                (top_cx - htw + 3, top_cy)
            ]
            roof_p_col = (40, 52, 72) if self.thermal_mode else (135, 142, 155)
            pygame.draw.polygon(surface, roof_p_col, p_pts)
            pygame.draw.polygon(surface, outline, p_pts, 1)

            feature_type = (x * 7 + y * 13) % 4
            if feature_type == 0:
                antenna_top_y = top_cy - 14
                pygame.draw.line(surface, outline, (top_cx, top_cy), (top_cx, antenna_top_y), 2)
                beacon_col = (255, 60, 60) if ((pygame.time.get_ticks() // 500) % 2 == 0) else (140, 20, 20)
                pygame.draw.circle(surface, beacon_col, (top_cx, antenna_top_y), 2)

            elif feature_type == 1:
                hvac_pts = [
                    (top_cx - 4, top_cy - 3),
                    (top_cx + 4, top_cy - 3),
                    (top_cx + 4, top_cy + 2),
                    (top_cx - 4, top_cy + 2)
                ]
                hvac_col = (60, 75, 100) if self.thermal_mode else (100, 110, 120)
                pygame.draw.polygon(surface, hvac_col, hvac_pts)
                pygame.draw.polygon(surface, outline, hvac_pts, 1)

            elif feature_type == 2:
                helipad_col = (100, 220, 255) if self.thermal_mode else (240, 200, 40)
                pygame.draw.circle(surface, helipad_col, (top_cx, top_cy), 5, 1)
                h_txt = self.tiny_font.render("H", True, helipad_col)
                surface.blit(h_txt, (top_cx - h_txt.get_width() // 2, top_cy - h_txt.get_height() // 2))

    # --------------------------------------------------
    # DRAWING: VOLUMETRIC HAZARDS
    # --------------------------------------------------

    def draw_volumetric_hazard(self, surface, x, y, z):
        """Renders animated pulsing fire block and rising smoke particles."""
        top_cx, top_cy = self.project(x, y, z)
        htw = self.tile_width // 2
        hth = self.tile_height // 2
        lh = self.layer_height

        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.008 + x * 2.0 + y * 1.5)

        if self.thermal_mode:
            # White-hot infrared thermal signature
            top_col = (255, int(230 + pulse * 25), int(160 + pulse * 50))
            left_col = (240, int(150 + pulse * 50), 30)
            right_col = (200, int(80 + pulse * 40), 10)
        else:
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
        pygame.draw.polygon(surface, (150, 30, 0), top_pts, 1)

        # Rising smoke puff
        smoke_phase = ((pygame.time.get_ticks() + x * 250 + y * 400) % 1200) / 1200.0
        smoke_y = top_cy - int(smoke_phase * 16)
        smoke_rad = int(3 + smoke_phase * 4)
        smoke_surf = pygame.Surface((smoke_rad * 2, smoke_rad * 2), pygame.SRCALPHA)
        smoke_alpha = int((1.0 - smoke_phase) * 110)
        smoke_col = (140, 160, 180, smoke_alpha) if self.thermal_mode else (80, 80, 90, smoke_alpha)
        pygame.draw.circle(smoke_surf, smoke_col, (smoke_rad, smoke_rad), smoke_rad)
        surface.blit(smoke_surf, (top_cx - smoke_rad, smoke_y - smoke_rad))

    # --------------------------------------------------
    # DRAWING: PROCEDURAL 3D QUADCOPTER
    # --------------------------------------------------

    def draw_quadcopter(self, surface, uav, ux, uy, gx, gy):
        """
        Renders an authentic 3D X-frame Quadcopter:
        - Downward searchlight cone (Thermal mode).
        - Aerodynamic carbon central hub in team color.
        - 4 diagonal carbon motor arms.
        - 4 motor hubs with spinning rotor blades (motion blur).
        - Twin front LEDs (status colored) & twin rear red LEDs.
        - Underbody optical sensor / camera gimbal.
        """
        # Thermal Searchlight Cone onto ground
        if self.thermal_mode and uav.status != "DEAD":
            spot_w = max(24, self.tile_width)
            spot_h = max(12, self.tile_height)
            spot_surf = pygame.Surface((spot_w, spot_h), pygame.SRCALPHA)
            pygame.draw.ellipse(spot_surf, (140, 255, 210, 40), (0, 0, spot_w, spot_h))
            surface.blit(spot_surf, (gx - spot_w // 2, gy - spot_h // 2))

            # Light rays from drone to spot
            beam_surf = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
            beam_pts = [
                (ux - 3, uy + 2),
                (ux + 3, uy + 2),
                (gx + spot_w // 2 - 2, gy),
                (gx - spot_w // 2 + 2, gy)
            ]
            pygame.draw.polygon(beam_surf, (140, 255, 210, 18), beam_pts)
            surface.blit(beam_surf, (0, 0))

        arm_len_x = max(7, self.tile_width // 3)
        arm_len_y = max(4, self.tile_height // 2)

        motor_offsets = [
            (+arm_len_x, -arm_len_y),  # Front-Right
            (-arm_len_x, -arm_len_y),  # Front-Left
            (+arm_len_x, +arm_len_y),  # Rear-Right
            (-arm_len_x, +arm_len_y)   # Rear-Left
        ]

        # 1. Carbon Fiber Arms
        arm_col = (20, 24, 30) if self.thermal_mode else (40, 44, 52)
        for dx, dy in motor_offsets:
            pygame.draw.line(surface, arm_col, (ux, uy), (ux + dx, uy + dy), 2)

        # 2. Motor Pods & Spinning Propellers
        rotor_t = pygame.time.get_ticks() * 0.04
        blade_r = max(5, self.tile_width // 5)

        for i, (dx, dy) in enumerate(motor_offsets):
            mx = ux + dx
            my = uy + dy

            pygame.draw.circle(surface, (55, 60, 70), (mx, my), 3)
            pygame.draw.circle(surface, (25, 28, 35), (mx, my), 1)

            # Spinning Rotor Blade (Motion Blur Disk)
            disk_surf = pygame.Surface((blade_r * 2 + 2, blade_r + 2), pygame.SRCALPHA)
            disk_col = (140, 240, 255, 110) if self.thermal_mode else (210, 230, 255, 95)
            pygame.draw.ellipse(
                disk_surf,
                disk_col,
                (1, 1, blade_r * 2, blade_r)
            )
            blade_angle = rotor_t + i * (math.pi / 2)
            bx = blade_r + int((blade_r - 1) * math.cos(blade_angle))
            by = (blade_r // 2) + int((blade_r // 2 - 1) * math.sin(blade_angle))
            pygame.draw.circle(disk_surf, (240, 248, 255, 180), (bx, by), 1)

            surface.blit(disk_surf, (mx - blade_r - 1, my - blade_r // 2 - 1))

        # 3. Navigation Status LEDs
        led_blink = (pygame.time.get_ticks() // 200) % 2 == 0
        if uav.status == "RESCUING":
            front_led_col = (0, 210, 255) if led_blink else (0, 90, 160)
        elif uav.status == "RETURNING":
            front_led_col = (255, 170, 0) if led_blink else (140, 80, 0)
        elif uav.status == "CHARGING":
            front_led_col = (255, 220, 0)
        else:
            front_led_col = (40, 255, 120) if led_blink else (20, 120, 50)

        pygame.draw.circle(surface, front_led_col, (ux + motor_offsets[0][0], uy + motor_offsets[0][1]), 2)
        pygame.draw.circle(surface, front_led_col, (ux + motor_offsets[1][0], uy + motor_offsets[1][1]), 2)
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
        pygame.draw.polygon(surface, (20, 25, 32), hub_pts)
        pygame.draw.polygon(surface, (60, 68, 80), hub_pts, 1)

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
        pill_col = (10, 15, 25, 230) if self.thermal_mode else (20, 25, 35, 210)
        pygame.draw.rect(pill_surf, pill_col, (0, 0, bw, bh), border_radius=3)
        surface.blit(pill_surf, (bx, by))
        surface.blit(badge_txt, (bx + 3, by + 1))

        # Altitude Tag
        alt_col = (100, 220, 255) if self.thermal_mode else (50, 60, 75)
        alt_txt = self.tiny_font.render(f"z:{uav.z}", True, alt_col)
        surface.blit(alt_txt, (ux + arm_len_x + 4, uy - 4))

    # --------------------------------------------------
    # DRAWING: SURVIVORS & BASES
    # --------------------------------------------------

    def draw_survivor_beacon(self, surface, cx, cy, is_rescued):
        """Distress beacon with expanding sonar pulse ring or green rescue shield."""
        if not is_rescued:
            pulse_val = (pygame.time.get_ticks() % 1000) / 1000.0
            pulse_r = int(5 + pulse_val * 9)
            pulse_alpha = int((1.0 - pulse_val) * 190)

            # Pulsing Sonar Ring
            pulse_surf = pygame.Surface((pulse_r * 2 + 2, pulse_r + 2), pygame.SRCALPHA)
            ring_col = (255, 240, 100, pulse_alpha) if self.thermal_mode else (255, 210, 0, pulse_alpha)
            pygame.draw.ellipse(
                pulse_surf,
                ring_col,
                (1, 1, pulse_r * 2, pulse_r),
                1
            )
            surface.blit(pulse_surf, (cx - pulse_r - 1, cy - pulse_r // 2 - 1))

            # Thermal glowing hot signature or daytime beacon
            if self.thermal_mode:
                pygame.draw.circle(surface, (255, 255, 230), (cx, cy), 6)
                pygame.draw.circle(surface, (255, 180, 50), (cx, cy), 4)
                pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 2)
            else:
                pygame.draw.circle(surface, (255, 200, 0), (cx, cy), 5)
                pygame.draw.circle(surface, (230, 40, 20), (cx, cy), 3)
                pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 1)

        else:
            pygame.draw.circle(surface, (34, 160, 60), (cx, cy), 6)
            pygame.draw.line(surface, (255, 255, 255), (cx - 3, cy), (cx + 3, cy), 2)
            pygame.draw.line(surface, (255, 255, 255), (cx, cy - 3), (cx, cy + 3), 2)

    def draw_base_station(self, surface, bx, by, bz, color):
        """High-tech drone charging launchpad on the ground."""
        cx, cy = self.project(bx, by, bz)
        pad_w = max(12, self.tile_width // 2)
        pad_h = max(6, self.tile_height // 2)

        pts = [
            (cx, cy - pad_h // 2),
            (cx + pad_w // 2, cy),
            (cx, cy + pad_h // 2),
            (cx - pad_w // 2, cy)
        ]
        pad_col = (25, 32, 45) if self.thermal_mode else (45, 50, 62)
        pygame.draw.polygon(surface, pad_col, pts)
        pygame.draw.polygon(surface, color, pts, 1)

        ring_col = (100, 180, 255) if self.thermal_mode else (90, 100, 120)
        pygame.draw.ellipse(surface, ring_col, (cx - 4, cy - 2, 8, 4), 1)

    # --------------------------------------------------
    # FULL SCENE RENDER (SMOOTH FLIGHT & DEPTH SORTED)
    # --------------------------------------------------

    def render(self, screen, disaster_map, coordinator, uavs):
        """Renders the entire 3D simulation with visual interpolation and depth sorting."""

        # 0. Sky gradient background (replaces flat fill)
        self.draw_sky(screen)

        # 1. Ground Floor Diamonds with depth fog
        coverage_set = coordinator.get_coverage()
        sectors = coordinator.sectors

        grid_col = self.THERMAL_GRID if self.thermal_mode else self.COLOR_GRID
        cov_col = self.THERMAL_COVERAGE if self.thermal_mode else self.COLOR_COVERAGE

        max_dist = self.grid_width + self.grid_height

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                cx, cy = self.project(x, y, 0)

                sector_idx = 0
                for s_i, (s_start, s_end) in enumerate(sectors):
                    if s_start <= x <= s_end:
                        sector_idx = s_i % len(self.SECTOR_COLORS)
                        break

                if self.thermal_mode:
                    floor_color = self.THERMAL_FLOOR
                else:
                    floor_color = self.SECTOR_COLORS[sector_idx]

                if (x, y) in coverage_set:
                    floor_color = cov_col

                # Apply depth fog to ground tiles
                rx, ry = self.rotate_coords(x, y)
                dist_t = (rx + ry) / max(1, max_dist)
                floor_color = self._fog_blend(floor_color, dist_t, self.thermal_mode)
                grid_fogged = self._fog_blend(grid_col, dist_t, self.thermal_mode)

                self.draw_diamond(screen, cx, cy, floor_color, grid_fogged)

        # 2. Update Smooth Visual Flight Positions (60 FPS Interpolation)
        lerp_speed = 0.22
        for uav in uavs:
            if uav.id not in self.visual_positions:
                self.visual_positions[uav.id] = [float(uav.x), float(uav.y), float(uav.z)]
            else:
                vx, vy, vz = self.visual_positions[uav.id]
                vx += (uav.x - vx) * lerp_speed
                vy += (uav.y - vy) * lerp_speed
                vz += (uav.z - vz) * lerp_speed
                self.visual_positions[uav.id] = [vx, vy, vz]

        # 3. Gather Entities for Depth Sorting
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
            vx, vy, vz = self.visual_positions[uav.id]
            rx, ry = self.rotate_coords(vx, vy)
            render_queue.append((rx + ry, vz, 2, "UAV", (uav, vx, vy, vz)))

        # Painter's Algorithm Depth Sort
        render_queue.sort(key=lambda item: (item[0], item[1], item[2]))

        # 4. Draw Target Lines
        for uav in uavs:
            if uav.target and uav.status != "DEAD":
                vx, vy, vz = self.visual_positions[uav.id]
                ux, uy = self.project(vx, vy, vz)
                tx, ty = self.project(uav.target[0], uav.target[1], uav.target[2] if len(uav.target) > 2 else 0)
                pygame.draw.line(screen, uav.color, (ux, uy), (tx, ty), 2)

        # 5. Render All Sorted Entities
        for _, _, _, item_type, data in render_queue:

            if item_type == "BUILDING":
                x, y, z = data
                self.draw_architectural_building(screen, x, y, z, disaster_map)

            elif item_type == "HAZARD":
                x, y, z = data
                cx_h, cy_h = self.project(x, y, z)
                self.draw_volumetric_hazard(screen, x, y, z)
                # Spawn embers from this fire cell
                self._spawn_embers(cx_h, cy_h)

            elif item_type == "SURVIVOR":
                x, y, z = data
                cx, cy = self.project(x, y, z)
                # Draw SOS vertical light beam
                self.draw_sos_beam(screen, cx, cy)
                self.draw_survivor_beacon(screen, cx, cy, is_rescued=False)

            elif item_type == "RESCUED":
                x, y, z = data
                cx, cy = self.project(x, y, z)
                self.draw_survivor_beacon(screen, cx, cy, is_rescued=True)

            elif item_type == "BASE":
                bx, by, bz, color = data
                self.draw_base_station(screen, bx, by, bz, color)

            elif item_type == "UAV":
                uav, vx, vy, vz = data

                # Ground Shadow
                gx, gy = self.project(vx, vy, 0)
                shadow_w = max(14, self.tile_width // 2)
                shadow_h = max(7, self.tile_height // 2)
                shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
                shadow_col = (10, 15, 25, 140) if self.thermal_mode else (40, 45, 55, 115)
                pygame.draw.ellipse(shadow_surf, shadow_col, (0, 0, shadow_w, shadow_h))
                screen.blit(shadow_surf, (gx - shadow_w // 2, gy - shadow_h // 2))

                # Rotor downwash ground effect ring
                self.draw_rotor_downwash(screen, gx, gy, vz)

                # Vertical Altitude Drop-Line
                ux, uy = self.project(vx, vy, vz)
                if vz > 0.05:
                    line_col = (80, 130, 170) if self.thermal_mode else (100, 115, 135)
                    pygame.draw.line(screen, line_col, (gx, gy), (ux, uy), 1)

                # Procedural 3D Quadcopter at smooth visual coordinates
                self.draw_quadcopter(screen, uav, ux, uy, gx, gy)

        # 6. Ember Particle Layer (on top of buildings/hazards, under HUD)
        self._update_and_draw_embers(screen)

        # 7. Top Controls & Camera Banner
        view_str = f"Camera: {self.view_names[self.view_angle]}"
        if self.thermal_mode:
            view_str += "  |  [MODE: FLIR THERMAL NIGHT]"

        title_col = (100, 240, 255) if self.thermal_mode else (30, 40, 60)
        cam_text = self.bold_font.render(view_str, True, title_col)
        screen.blit(cam_text, (20, 14))

        sub_col = (130, 170, 200) if self.thermal_mode else (90, 105, 125)
        help_text = self.small_font.render(
            "Controls: [<-] [->] Rotate | [T] Thermal FLIR | [+/-] Speed | [R] Restart | [Space] Pause",
            True,
            sub_col
        )
        screen.blit(help_text, (20, 36))
