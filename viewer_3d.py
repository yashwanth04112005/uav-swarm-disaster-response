"""
Isometric 3D Viewer module for UAV Swarm Disaster Response.
Renders 3D voxel city, terrain, survivors, altitude drop-lines, and UAVs
using pure Pygame (no 3D engine required).
Supports 4 camera rotations (0, 90, 180, 270 degrees).
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

        # Colors
        self.COLOR_BG = (242, 245, 249)
        self.COLOR_FLOOR = (230, 234, 240)
        self.COLOR_GRID = (212, 218, 226)
        self.COLOR_COVERAGE = (185, 222, 255)

        # Building cube face colors (light, mid, dark)
        self.BUILDING_FACES = (
            (160, 168, 180),  # Top
            (125, 132, 144),  # Left
            (100, 106, 118)   # Right
        )
        self.BUILDING_OUTLINE = (75, 80, 90)

        # Hazard cube face colors (light, mid, dark)
        self.HAZARD_FACES = (
            (255, 125, 40),   # Top
            (225, 85, 20),    # Left
            (185, 50, 10)     # Right
        )
        self.HAZARD_OUTLINE = (140, 30, 0)

        # Sector colors (subtle pastels)
        self.SECTOR_COLORS = [
            (220, 235, 255),
            (255, 225, 225),
            (225, 255, 225),
            (245, 225, 255),
            (255, 245, 220)
        ]

        self.font = pygame.font.SysFont(None, 22)
        self.bold_font = pygame.font.SysFont(None, 24, bold=True)
        self.small_font = pygame.font.SysFont(None, 18)

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
    # DRAWING PRIMITIVES
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

    def draw_voxel_cube(self, surface, x, y, z, faces, outline_color):
        """Draw a solid isometric 3D voxel cube at (x, y, z)."""
        top_cx, top_cy = self.project(x, y, z)
        htw = self.tile_width // 2
        hth = self.tile_height // 2
        lh = self.layer_height

        # Top Face
        top_pts = [
            (top_cx, top_cy - hth),
            (top_cx + htw, top_cy),
            (top_cx, top_cy + hth),
            (top_cx - htw, top_cy)
        ]
        pygame.draw.polygon(surface, faces[0], top_pts)

        # Left Face
        left_pts = [
            (top_cx - htw, top_cy),
            (top_cx, top_cy + hth),
            (top_cx, top_cy + hth + lh),
            (top_cx - htw, top_cy + lh)
        ]
        pygame.draw.polygon(surface, faces[1], left_pts)

        # Right Face
        right_pts = [
            (top_cx, top_cy + hth),
            (top_cx + htw, top_cy),
            (top_cx + htw, top_cy + lh),
            (top_cx, top_cy + hth + lh)
        ]
        pygame.draw.polygon(surface, faces[2], right_pts)

        # Outlines
        if outline_color:
            pygame.draw.polygon(surface, outline_color, top_pts, 1)
            pygame.draw.polygon(surface, outline_color, left_pts, 1)
            pygame.draw.polygon(surface, outline_color, right_pts, 1)

    # --------------------------------------------------
    # FULL SCENE RENDER
    # --------------------------------------------------

    def render(self, screen, disaster_map, coordinator, uavs):
        """Renders the entire 3D isometric simulation."""
        screen.fill(self.COLOR_BG)

        # 1. Draw Ground Floor Diamonds
        coverage_set = coordinator.get_coverage()
        sectors = coordinator.sectors

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                cx, cy = self.project(x, y, 0)

                # Determine base floor color (sector tint)
                sector_idx = 0
                for s_i, (s_start, s_end) in enumerate(sectors):
                    if s_start <= x <= s_end:
                        sector_idx = s_i % len(self.SECTOR_COLORS)
                        break

                floor_color = self.SECTOR_COLORS[sector_idx]

                # Coverage overlay
                if (x, y) in coverage_set:
                    floor_color = self.COLOR_COVERAGE

                self.draw_diamond(screen, cx, cy, floor_color, self.COLOR_GRID)

        # 2. Gather All Entities for Depth Sorting
        # Depth key: (rx + ry, z, priority)
        # Priority:
        # 0: Solid Voxel (Building/Hazard)
        # 1: Ground Markers (Base, Survivors)
        # 2: UAV Shadows & Drop-lines
        # 3: UAV Body
        render_queue = []

        # A. Voxel Cubes (Buildings and Hazards)
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

        # B. UAV Bases
        for uav in uavs:
            bx, by, bz = uav.base_position
            rx, ry = self.rotate_coords(bx, by)
            render_queue.append((rx + ry, bz, 1, "BASE", (bx, by, bz, uav.color)))

        # C. UAVs (Shadows and Drones)
        for uav in uavs:
            if uav.status == "DEAD":
                continue
            rx, ry = self.rotate_coords(uav.x, uav.y)
            render_queue.append((rx + ry, uav.z, 2, "UAV", uav))

        # Sort strictly from far to near, bottom to top
        render_queue.sort(key=lambda item: (item[0], item[1], item[2]))

        # 3. Draw Target Lines
        for uav in uavs:
            if uav.target and uav.status != "DEAD":
                ux, uy = self.project(uav.x, uav.y, uav.z)
                tx, ty = self.project(uav.target[0], uav.target[1], uav.target[2] if len(uav.target) > 2 else 0)
                pygame.draw.line(screen, uav.color, (ux, uy), (tx, ty), 2)

        # 4. Render Sorted Entities
        for _, _, _, item_type, data in render_queue:

            if item_type == "BUILDING":
                x, y, z = data
                self.draw_voxel_cube(screen, x, y, z, self.BUILDING_FACES, self.BUILDING_OUTLINE)

            elif item_type == "HAZARD":
                x, y, z = data
                self.draw_voxel_cube(screen, x, y, z, self.HAZARD_FACES, self.HAZARD_OUTLINE)

            elif item_type == "SURVIVOR":
                x, y, z = data
                cx, cy = self.project(x, y, z)
                # Survivor target ring
                pygame.draw.circle(screen, (255, 215, 0), (cx, cy), 7)
                pygame.draw.circle(screen, (200, 0, 0), (cx, cy), 4)

            elif item_type == "RESCUED":
                x, y, z = data
                cx, cy = self.project(x, y, z)
                pygame.draw.circle(screen, (34, 139, 34), (cx, cy), 6)
                pygame.draw.circle(screen, (150, 255, 150), (cx, cy), 3)

            elif item_type == "BASE":
                bx, by, bz, color = data
                cx, cy = self.project(bx, by, bz)
                pygame.draw.rect(screen, (40, 40, 40), (cx - 5, cy - 4, 10, 8))
                pygame.draw.rect(screen, color, (cx - 3, cy - 2, 6, 4))

            elif item_type == "UAV":
                uav = data
                # 1. Ground Shadow
                gx, gy = self.project(uav.x, uav.y, 0)
                shadow_rect = pygame.Rect(gx - 8, gy - 4, 16, 8)
                shadow_surf = pygame.Surface((16, 8), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (50, 50, 60, 110), (0, 0, 16, 8))
                screen.blit(shadow_surf, shadow_rect)

                # 2. Vertical Altitude Drop-Line
                ux, uy = self.project(uav.x, uav.y, uav.z)
                if uav.z > 0:
                    pygame.draw.line(screen, (120, 130, 150), (gx, gy), (ux, uy), 1)

                # 3. UAV Body Sphere
                radius = 10
                pygame.draw.circle(screen, (20, 20, 25), (ux, uy), radius + 1)
                pygame.draw.circle(screen, uav.color, (ux, uy), radius)

                # 4. UAV ID and Altitude Tag
                id_txt = self.small_font.render(str(uav.id), True, (255, 255, 255))
                screen.blit(id_txt, (ux - id_txt.get_width() // 2, uy - id_txt.get_height() // 2))

                alt_txt = self.small_font.render(f"z:{uav.z}", True, (40, 40, 50))
                screen.blit(alt_txt, (ux + radius + 2, uy - 6))

        # 5. Top Controls & Camera Banner
        cam_text = self.bold_font.render(f"Camera View: {self.view_names[self.view_angle]}", True, (30, 40, 60))
        screen.blit(cam_text, (20, 15))

        help_text = self.small_font.render("Rotate: [<-] [->] or [A] [D]  |  Space: Pause/Resume", True, (100, 110, 130))
        screen.blit(help_text, (20, 38))
