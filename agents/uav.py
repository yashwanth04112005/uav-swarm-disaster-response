from environment.map import (
    OBSTACLE,
    HAZARD,
    SURVIVOR,
    RESCUED
)

from planning.a_star import find_path


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

        # --------------------------------------------------
        # UAV STATE
        # --------------------------------------------------

        self.battery = 100

        self.max_battery = 100

        self.sensor_range = 2

        self.visited_cells = set()

        self.visited_cells.add(
            (self.x, self.y)
        )

        # --------------------------------------------------
        # BASE
        # --------------------------------------------------

        self.base_position = (
            self.x,
            self.y
        )

        # --------------------------------------------------
        # MISSION STATE
        # --------------------------------------------------

        self.target = None

        self.path = []

        self.status = "EXPLORING"

        self.rescued_count = 0

    # --------------------------------------------------
    # POSITION
    # --------------------------------------------------

    def get_position(self):

        return (
            self.x,
            self.y
        )

    # --------------------------------------------------
    # MOVE ONE STEP
    # --------------------------------------------------

    def move(
        self,
        disaster_map,
        sector,
        coordinator
    ):

        if self.battery <= 0:

            self.status = "DEAD"

            return

        # --------------------------------------------------
        # RETURN TO BASE WHEN BATTERY IS LOW
        # --------------------------------------------------

        if (
            self.battery <= 20
            and
            self.status != "RETURNING"
            and
            self.status != "CHARGING"
        ):

            self.target = (
                self.base_position
            )

            self.path = find_path(
                disaster_map,
                self.get_position(),
                self.base_position,
                sector
            )

            self.status = "RETURNING"

        # --------------------------------------------------
        # MOVE USING CURRENT A* PATH
        # --------------------------------------------------

        if self.path:

            next_position = (
                self.path[0]
            )

            # Avoid another UAV occupying the cell
            if coordinator.is_position_occupied(
                next_position,
                excluding_uav=self.id
            ):

                self.path = []

                return

            self.path.pop(0)

            self.x, self.y = (
                next_position
            )

            self.visited_cells.add(
                self.get_position()
            )

            self.battery = max(
                0,
                self.battery - 1
            )

            coordinator.update_uav_position(
                self.id,
                self.get_position()
            )

            return

        # --------------------------------------------------
        # RETURNED TO BASE
        # --------------------------------------------------

        if (
            self.status == "RETURNING"
            and
            self.get_position()
            == self.base_position
        ):

            self.status = "CHARGING"

        # --------------------------------------------------
        # CHARGING
        # --------------------------------------------------

        if self.status == "CHARGING":

            self.battery = min(
                self.max_battery,
                self.battery + 5
            )

            if (
                self.battery
                >= self.max_battery
            ):

                self.status = "EXPLORING"

            return

        # --------------------------------------------------
        # TARGETED SURVIVOR
        # --------------------------------------------------

        if self.target:

            self.path = find_path(
                disaster_map,
                self.get_position(),
                self.target,
                sector
            )

            if self.path:

                self.status = "RESCUING"

                return self.move(
                    disaster_map,
                    sector,
                    coordinator
                )

            else:

                # Target cannot currently be reached
                self.target = None
                self.status = "EXPLORING"

        # --------------------------------------------------
        # EXPLORE
        # --------------------------------------------------

        self.explore(
            disaster_map,
            sector,
            coordinator
        )

    # --------------------------------------------------
    # EXPLORATION
    # --------------------------------------------------

    def explore(
        self,
        disaster_map,
        sector,
        coordinator
    ):

        if self.battery <= 0:

            self.status = "DEAD"

            return

        sector_start_x, sector_end_x = (
            sector
        )

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

            # Stay inside assigned sector
            if not (
                sector_start_x
                <= new_x
                <= sector_end_x
            ):

                continue

            # Stay inside map
            if not (
                0 <= new_x
                < disaster_map.width
                and
                0 <= new_y
                < disaster_map.height
            ):

                continue

            cell = (
                disaster_map.grid[
                    new_y
                ][
                    new_x
                ]
            )

            # Avoid obstacles and hazards
            if cell in (
                OBSTACLE,
                HAZARD
            ):

                continue

            # Avoid UAV collision
            if coordinator.is_position_occupied(
                (new_x, new_y),
                excluding_uav=self.id
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

        # Prefer unexplored cells
        if unvisited_moves:

            chosen = unvisited_moves[0]

        elif valid_moves:

            chosen = valid_moves[0]

        else:

            return

        self.x, self.y = chosen

        self.visited_cells.add(
            self.get_position()
        )

        self.battery = max(
            0,
            self.battery - 1
        )

        coordinator.update_uav_position(
            self.id,
            self.get_position()
        )

    # --------------------------------------------------
    # SCAN FOR SURVIVORS
    # --------------------------------------------------

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
                    0 <= scan_x
                    < disaster_map.width
                    and
                    0 <= scan_y
                    < disaster_map.height
                ):

                    continue

                if (
                    disaster_map.grid[
                        scan_y
                    ][
                        scan_x
                    ]
                    == SURVIVOR
                ):

                    location = (
                        scan_x,
                        scan_y
                    )

                    if (
                        location
                        not in coordinator.get_survivors()
                        and
                        location
                        not in coordinator.get_rescued_survivors()
                    ):

                        coordinator.add_survivor(
                            location
                        )

                        print(
                            f"[UAV {self.id}] "
                            f"Survivor detected at "
                            f"{location}"
                        )

        # --------------------------------------------------
        # ASSIGN NEAREST UNASSIGNED SURVIVOR
        # --------------------------------------------------

        if (
            self.target is None
            and
            self.status == "EXPLORING"
        ):

            survivors = (
                coordinator.get_survivors()
            )

            if survivors:

                nearest = min(
                    survivors,
                    key=lambda location:
                    abs(
                        location[0]
                        - self.x
                    )
                    +
                    abs(
                        location[1]
                        - self.y
                    )
                )

                self.target = nearest

                coordinator.assign_target(
                    self.id,
                    nearest
                )

                print(
                    f"[UAV {self.id}] "
                    f"Target assigned: "
                    f"{nearest}"
                )

    # --------------------------------------------------
    # RESCUE SURVIVOR
    # --------------------------------------------------

    def attempt_rescue(
        self,
        disaster_map,
        coordinator
    ):

        if self.target is None:

            return

        if (
            self.get_position()
            != self.target
        ):

            return

        target = self.target

        if disaster_map.rescue_survivor(
            target
        ):

            coordinator.rescue_survivor(
                target
            )

            self.rescued_count += 1

            print(
                f"[UAV {self.id}] "
                f"Survivor rescued at "
                f"{target}"
            )

        coordinator.clear_target(
            self.id
        )

        self.target = None

        self.path = []

        self.status = "EXPLORING"