import random


EMPTY = 0
OBSTACLE = 1
HAZARD = 2
SURVIVOR = 3
RESCUED = 4

# 6 connected orthogonal directions (dx, dy, dz)
DIRECTIONS_3D = [
    (0, -1, 0),   # North
    (0, 1, 0),    # South
    (-1, 0, 0),   # West
    (1, 0, 0),    # East
    (0, 0, -1),   # Down
    (0, 0, 1)     # Up
]

# 4 horizontal directions on the same altitude layer
DIRECTIONS_HORIZONTAL = [
    (0, -1, 0),
    (0, 1, 0),
    (-1, 0, 0),
    (1, 0, 0)
]


class DisasterMap:

    def __init__(
        self,
        width,
        height,
        depth=6
    ):

        self.width = width
        self.height = height
        self.depth = depth

        # grid[z][y][x] where z=0 is ground level and z=depth-1 is top airspace
        self.grid = [
            [
                [
                    EMPTY
                    for _ in range(width)
                ]
                for _ in range(height)
            ]
            for _ in range(depth)
        ]

    # --------------------------------------------------
    # HELPER CHECKS
    # --------------------------------------------------

    def is_inside(self, x, y, z):
        return (
            0 <= x < self.width
            and
            0 <= y < self.height
            and
            0 <= z < self.depth
        )

    def is_blocked(self, x, y, z):
        if not self.is_inside(x, y, z):
            return True
        return self.grid[z][y][x] in (
            OBSTACLE,
            HAZARD
        )

    # --------------------------------------------------
    # GENERATE DISASTER ENVIRONMENT
    # --------------------------------------------------

    def generate(self):

        # Buildings: vertical columns starting at ground level
        # Max building height is depth - 2, leaving top layer(s) as free air
        max_building_height = max(1, self.depth - 2)

        for y in range(self.height):

            for x in range(self.width):

                r = random.random()

                if r < 0.10:
                    # Place building column
                    building_height = random.randint(1, max_building_height)
                    for z in range(building_height):
                        self.grid[z][y][x] = OBSTACLE

                elif r < 0.15:
                    # Place low hazard on the ground
                    self.grid[0][y][x] = HAZARD
                    if self.depth > 1 and random.random() < 0.3:
                        # Smoke rising to layer 1
                        self.grid[1][y][x] = HAZARD

        self.place_survivors(5)

    # --------------------------------------------------
    # PLACE SURVIVORS
    # --------------------------------------------------

    def place_survivors(
        self,
        count
    ):

        placed = 0

        while placed < count:

            x = random.randint(
                0,
                self.width - 1
            )

            y = random.randint(
                0,
                self.height - 1
            )

            # Survivors are on the ground (z = 0)
            if self.grid[0][y][x] == EMPTY:

                self.grid[0][y][x] = SURVIVOR

                placed += 1

    # --------------------------------------------------
    # RESCUE SURVIVOR
    # --------------------------------------------------

    def rescue_survivor(
        self,
        location
    ):

        if len(location) == 3:
            x, y, z = location
        else:
            x, y = location
            z = 0

        if not self.is_inside(x, y, z):
            return False

        if self.grid[z][y][x] != SURVIVOR:
            return False

        self.grid[z][y][x] = RESCUED

        return True

    # --------------------------------------------------
    # HAZARD EXPANSION
    # --------------------------------------------------

    def expand_hazards(self):

        new_hazards = set()

        for z in range(self.depth):

            for y in range(self.height):

                for x in range(self.width):

                    if self.grid[z][y][x] != HAZARD:
                        continue

                    for dx, dy, dz in DIRECTIONS_3D:

                        new_x = x + dx
                        new_y = y + dy
                        new_z = z + dz

                        if not self.is_inside(new_x, new_y, new_z):
                            continue

                        if self.grid[new_z][new_y][new_x] != EMPTY:
                            continue

                        # Fire and smoke spread upward more easily than downward
                        if dz > 0:
                            spread_chance = 0.35
                        elif dz < 0:
                            spread_chance = 0.10
                        else:
                            spread_chance = 0.25

                        if random.random() < spread_chance:
                            new_hazards.add((new_x, new_y, new_z))

        for x, y, z in new_hazards:
            self.grid[z][y][x] = HAZARD