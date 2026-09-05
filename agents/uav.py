from collections import deque

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

            self.target = None

            self.path = find_path(
                disaster_map,
                self.get_position(),
                self.base_position,
                sector
            )

            self.status = "RETURNING"

        # --------------------------------------------------
        # FOLLOW EXISTING PATH
        # --------------------------------------------------

        if self.path:

            next_position = self.path[0]

            # Avoid another UAV
            if coordinator.is_position_occupied(
                next_position,
                excluding_uav=self.id
            ):

                self.path = []

                return

            self.path.pop(0)

            self.x, self.y = next_position

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

                self.target = None

                self.status = "EXPLORING"

        # --------------------------------------------------
        # EXPLORATION
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

        start = self.get_position()

        sector_start_x, sector_end_x = sector

        directions = [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0)
        ]

        # --------------------------------------------------
        # STEP 1:
        # LOOK FOR IMMEDIATELY UNVISITED CELLS
        # --------------------------------------------------

        unvisited_moves = []

        for dx, dy in directions:

            new_x = self.x + dx
            new_y = self.y + dy

            if not (
                sector_start_x
                <= new_x
                <= sector_end_x
            ):

                continue

            if not (
                0 <= new_x < disaster_map.width
                and
                0 <= new_y < disaster_map.height
            ):

                continue

            cell = disaster_map.grid[
                new_y
            ][
                new_x
            ]

            if cell in (
                OBSTACLE,
                HAZARD
            ):

                continue

            position = (
                new_x,
                new_y
            )

            if coordinator.is_position_occupied(
                position,
                excluding_uav=self.id
            ):

                continue

            if position not in self.visited_cells:

                unvisited_moves.append(
                    position
                )

        # --------------------------------------------------
        # ALWAYS PREFER DIRECT UNVISITED CELLS
        # --------------------------------------------------

        if unvisited_moves:

            # Choose the first available unexplored cell.
            # This keeps the algorithm simple and predictable.
            chosen = unvisited_moves[0]

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

            return

        # --------------------------------------------------
        # STEP 2:
        # NO UNVISITED NEIGHBOUR
        #
        # SEARCH FOR THE NEAREST REACHABLE UNVISITED CELL
        # --------------------------------------------------

        target = self.find_nearest_unvisited_cell(
            disaster_map,
            sector,
            coordinator
        )

        # --------------------------------------------------
        # NO REACHABLE UNVISITED CELL
        # --------------------------------------------------

        if target is None:

            # Do NOT randomly wander through visited cells.
            self.status = "EXPLORATION_COMPLETE"

            return

        # --------------------------------------------------
        # STEP 3:
        # BUILD A PATH TO THE UNVISITED REGION
        # --------------------------------------------------

        path = self.find_exploration_path(
            disaster_map,
            start,
            target,
            sector,
            coordinator
        )

        if not path:

            self.status = "EXPLORATION_COMPLETE"

            return

        # --------------------------------------------------
        # MOVE ONLY ONE STEP
        # --------------------------------------------------

        next_position = path[0]

        if coordinator.is_position_occupied(
            next_position,
            excluding_uav=self.id
        ):

            return

        self.x, self.y = next_position

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
    # FIND NEAREST UNVISITED CELL
    # --------------------------------------------------

    def find_nearest_unvisited_cell(
        self,
        disaster_map,
        sector,
        coordinator
    ):

        start = self.get_position()

        sector_start_x, sector_end_x = sector

        directions = [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0)
        ]

        queue = deque()

        queue.append(start)

        visited_search = set()

        visited_search.add(start)

        while queue:

            current = queue.popleft()

            # --------------------------------------------------
            # If this cell is unexplored, use it
            # --------------------------------------------------

            if (
                current not in self.visited_cells
                and
                current != start
            ):

                return current

            for dx, dy in directions:

                next_x = current[0] + dx
                next_y = current[1] + dy

                next_position = (
                    next_x,
                    next_y
                )

                if next_position in visited_search:

                    continue

                if not (
                    sector_start_x
                    <= next_x
                    <= sector_end_x
                ):

                    continue

                if not (
                    0 <= next_x < disaster_map.width
                    and
                    0 <= next_y < disaster_map.height
                ):

                    continue

                cell = disaster_map.grid[
                    next_y
                ][
                    next_x
                ]

                if cell in (
                    OBSTACLE,
                    HAZARD
                ):

                    continue

                # Avoid another UAV during exploration search
                if coordinator.is_position_occupied(
                    next_position,
                    excluding_uav=self.id
                ):

                    continue

                visited_search.add(
                    next_position
                )

                queue.append(
                    next_position
                )

        return None

    # --------------------------------------------------
    # FIND PATH TO EXPLORATION TARGET
    # --------------------------------------------------

    def find_exploration_path(
        self,
        disaster_map,
        start,
        goal,
        sector,
        coordinator
    ):

        directions = [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0)
        ]

        sector_start_x, sector_end_x = sector

        queue = deque()

        queue.append(start)

        came_from = {
            start: None
        }

        while queue:

            current = queue.popleft()

            if current == goal:

                break

            for dx, dy in directions:

                next_x = current[0] + dx
                next_y = current[1] + dy

                next_position = (
                    next_x,
                    next_y
                )

                if next_position in came_from:

                    continue

                if not (
                    sector_start_x
                    <= next_x
                    <= sector_end_x
                ):

                    continue

                if not (
                    0 <= next_x < disaster_map.width
                    and
                    0 <= next_y < disaster_map.height
                ):

                    continue

                cell = disaster_map.grid[
                    next_y
                ][
                    next_x
                ]

                if cell in (
                    OBSTACLE,
                    HAZARD
                ):

                    continue

                if (
                    next_position != goal
                    and
                    coordinator.is_position_occupied(
                        next_position,
                        excluding_uav=self.id
                    )
                ):

                    continue

                came_from[
                    next_position
                ] = current

                queue.append(
                    next_position
                )

        # --------------------------------------------------
        # NO PATH
        # --------------------------------------------------

        if goal not in came_from:

            return []

        # --------------------------------------------------
        # RECONSTRUCT PATH
        # --------------------------------------------------

        path = []

        current = goal

        while current != start:

            path.append(current)

            current = came_from[current]

        path.reverse()

        return path

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