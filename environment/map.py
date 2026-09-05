import random


EMPTY = 0
OBSTACLE = 1
HAZARD = 2
SURVIVOR = 3
RESCUED = 4


class DisasterMap:

    def __init__(
        self,
        width,
        height
    ):

        self.width = width
        self.height = height

        self.grid = [
            [
                EMPTY
                for _ in range(width)
            ]
            for _ in range(height)
        ]

    # --------------------------------------------------
    # GENERATE DISASTER ENVIRONMENT
    # --------------------------------------------------

    def generate(self):

        for y in range(
            self.height
        ):

            for x in range(
                self.width
            ):

                r = random.random()

                if r < 0.10:

                    self.grid[y][x] = (
                        OBSTACLE
                    )

                elif r < 0.15:

                    self.grid[y][x] = (
                        HAZARD
                    )

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

            if (
                self.grid[y][x]
                == EMPTY
            ):

                self.grid[y][x] = (
                    SURVIVOR
                )

                placed += 1

    # --------------------------------------------------
    # RESCUE SURVIVOR
    # --------------------------------------------------

    def rescue_survivor(
        self,
        location
    ):

        x, y = location

        if not (
            0 <= x < self.width
            and
            0 <= y < self.height
        ):

            return False

        if (
            self.grid[y][x]
            != SURVIVOR
        ):

            return False

        self.grid[y][x] = RESCUED

        return True

    # --------------------------------------------------
    # HAZARD EXPANSION
    # --------------------------------------------------

    def expand_hazards(self):

        new_hazards = []

        directions = [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0)
        ]

        for y in range(
            self.height
        ):

            for x in range(
                self.width
            ):

                if (
                    self.grid[y][x]
                    != HAZARD
                ):

                    continue

                for dx, dy in directions:

                    new_x = x + dx
                    new_y = y + dy

                    if not (
                        0 <= new_x < self.width
                        and
                        0 <= new_y < self.height
                    ):

                        continue

                    if (
                        self.grid[new_y][new_x]
                        != EMPTY
                    ):

                        continue

                    if (
                        random.random()
                        < 0.30
                    ):

                        location = (
                            new_x,
                            new_y
                        )

                        if (
                            location
                            not in new_hazards
                        ):

                            new_hazards.append(
                                location
                            )

        for x, y in new_hazards:

            self.grid[y][x] = (
                HAZARD
            )