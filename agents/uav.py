import random

from environment.map import (
    OBSTACLE,
    SURVIVOR
)


class UAV:

    def __init__(
        self,
        drone_id,
        x,
        y,
        color
    ):

        self.id = drone_id

        self.x = x
        self.y = y

        self.color = color

        self.battery = 100

        self.sensor_range = 2

        self.visited_cells = set()

        self.visited_cells.add(
            (self.x, self.y)
        )

    def move(
        self,
        disaster_map,
        sector
    ):

        if self.battery <= 0:
            return

        sector_start_x, sector_end_x = sector

        directions = [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0)
        ]

        valid_moves = []

        unvisited_moves = []

        for dx, dy in directions:

            new_x = self.x + dx
            new_y = self.y + dy

            if not (
                sector_start_x <= new_x <= sector_end_x
            ):
                continue

            if not (
                0 <= new_x < disaster_map.width
                and
                0 <= new_y < disaster_map.height
            ):
                continue

            if (
                disaster_map.grid[new_y][new_x]
                == OBSTACLE
            ):
                continue

            valid_moves.append(
                (new_x, new_y)
            )

            if (
                new_x,
                new_y
            ) not in self.visited_cells:

                unvisited_moves.append(
                    (new_x, new_y)
                )

        if unvisited_moves:

            chosen_x, chosen_y = random.choice(
                unvisited_moves
            )

        elif valid_moves:

            chosen_x, chosen_y = random.choice(
                valid_moves
            )

        else:
            return

        self.x = chosen_x
        self.y = chosen_y

        self.visited_cells.add(
            (self.x, self.y)
        )

        self.battery = max(
            0,
            self.battery - 1
        )

    def scan(
        self,
        disaster_map,
        coordinator
    ):

        for dy in range(
            -self.sensor_range,
            self.sensor_range + 1
        ):
            for dx in range(
                -self.sensor_range,
                self.sensor_range + 1
            ):

                scan_x = self.x + dx
                scan_y = self.y + dy

                if not (
                    0 <= scan_x < disaster_map.width
                    and
                    0 <= scan_y < disaster_map.height
                ):
                    continue

                if (
                    disaster_map.grid[scan_y][scan_x]
                    == SURVIVOR
                ):

                    location = (
                        scan_x,
                        scan_y
                    )

                    if (
                        location
                        not in coordinator.get_survivors()
                    ):

                        coordinator.add_survivor(
                            location
                        )

                        print(
                            f"[UAV {self.id}] Survivor detected at {location}"
                        )