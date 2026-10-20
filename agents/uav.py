from collections import deque

from environment.map import (
    OBSTACLE,
    HAZARD,
    SURVIVOR,
    RESCUED,
    DIRECTIONS_3D,
    DIRECTIONS_HORIZONTAL
)

from planning.a_star import find_path


class UAV:

    def __init__(
        self,
        drone_id,
        x,
        y,
        z=0,
        color=(0, 100, 255),
        search_altitude=2
    ):

        self.id = drone_id

        self.x = x
        self.y = y
        self.z = z

        self.color = color
        self.search_altitude = search_altitude

        # --------------------------------------------------
        # UAV STATE
        # --------------------------------------------------

        self.battery = 100
        self.max_battery = 100

        self.sensor_range = 2

        self.visited_cells = set()
        self.visited_cells.add(
            (self.x, self.y, self.z)
        )

        # --------------------------------------------------
        # BASE
        # --------------------------------------------------

        self.base_position = (
            self.x,
            self.y,
            self.z
        )

        # --------------------------------------------------
        # MISSION STATE
        # --------------------------------------------------

        self.target = None
        self.path = []
        self.status = "EXPLORING"
        self.rescued_count = 0

        # Performance & Flight Telemetry
        self.total_distance = 0
        self.total_energy_consumed = 0
        self.recharge_count = 0

    # --------------------------------------------------
    # POSITION
    # --------------------------------------------------

    def get_position(self):

        return (
            self.x,
            self.y,
            self.z
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
            if self.target is not None:
                coordinator.clear_target(self.id)
                self.target = None
            self.status = "DEAD"
            return

        # --------------------------------------------------
        # RETURN TO BASE WHEN BATTERY IS LOW (DYNAMIC THRESHOLD)
        # --------------------------------------------------

        dist_to_base = (
            abs(self.x - self.base_position[0]) +
            abs(self.y - self.base_position[1]) +
            abs(self.z - self.base_position[2])
        )

        if (
            self.battery <= (dist_to_base + 8)
            and
            self.status != "RETURNING"
            and
            self.status != "CHARGING"
        ):

            if self.target is not None:
                coordinator.clear_target(self.id)
                self.target = None

            sector_start_x, sector_end_x = sector
            ret_sector = (0, disaster_map.width - 1) if (self.x < sector_start_x or self.x > sector_end_x) else sector
            self.path = find_path(
                disaster_map,
                self.get_position(),
                self.base_position,
                ret_sector
            )

            self.status = "RETURNING"

        # --------------------------------------------------
        # FOLLOW EXISTING PATH
        # --------------------------------------------------

        if self.path:

            next_position = self.path[0]

            # Check if path is still safe
            # (hazards may have expanded or building ahead)
            nx, ny, nz = next_position

            if disaster_map.is_blocked(nx, ny, nz):

                self.path = []
                return

            # Avoid another UAV (3D collision)
            if coordinator.is_position_occupied(
                next_position,
                excluding_uav=self.id
            ):

                self.path = []
                return

            self.path.pop(0)

            self.x, self.y, self.z = next_position

            self.visited_cells.add(
                self.get_position()
            )

            self.battery = max(
                0,
                self.battery - 1
            )
            self.total_distance += 1
            self.total_energy_consumed += 1

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
            self.get_position() == self.base_position
        ):

            self.recharge_count += 1
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
        # RETURNING BUT PATH WAS CLEARED
        # --------------------------------------------------

        if (
            self.status == "RETURNING"
            and
            self.get_position() != self.base_position
        ):

            sector_start_x, sector_end_x = sector
            ret_sector = (0, disaster_map.width - 1) if (self.x < sector_start_x or self.x > sector_end_x) else sector
            self.path = find_path(
                disaster_map,
                self.get_position(),
                self.base_position,
                ret_sector
            )

            # If still no path, stay put
            return

        # --------------------------------------------------
        # TARGETED SURVIVOR
        # --------------------------------------------------

        if self.target:

            sector_start_x, sector_end_x = sector
            target_x = self.target[0]
            if not (sector_start_x <= target_x <= sector_end_x) or not (sector_start_x <= self.x <= sector_end_x):
                effective_sector = (0, disaster_map.width - 1)
            else:
                effective_sector = sector

            self.path = find_path(
                disaster_map,
                self.get_position(),
                self.target,
                effective_sector
            )

            if self.path:

                self.status = "RESCUING"

                return self.move(
                    disaster_map,
                    sector,
                    coordinator
                )

            else:

                coordinator.clear_target(
                    self.id
                )

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
    # EXPLORATION (STRATEGY E1: ALTITUDE SWEEP)
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

        # Climb to search altitude first if below it
        if self.z < self.search_altitude:

            climb_target = (
                self.x,
                self.y,
                self.search_altitude
            )

            climb_path = find_path(
                disaster_map,
                self.get_position(),
                climb_target,
                sector
            )

            if climb_path:

                self.path = climb_path
                return self.move(
                    disaster_map,
                    sector,
                    coordinator
                )

        start = self.get_position()
        sector_start_x, sector_end_x = sector

        # --------------------------------------------------
        # STEP 1: LOOK FOR DIRECT UNVISITED HORIZONTAL NEIGHBOURS
        # --------------------------------------------------

        unvisited_moves = []

        for dx, dy, dz in DIRECTIONS_HORIZONTAL:

            new_x = self.x + dx
            new_y = self.y + dy
            new_z = self.z

            if not (
                sector_start_x
                <= new_x
                <= sector_end_x
            ):

                continue

            if not disaster_map.is_inside(new_x, new_y, new_z):

                continue

            if disaster_map.is_blocked(new_x, new_y, new_z):

                continue

            position = (
                new_x,
                new_y,
                new_z
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

        if unvisited_moves:

            chosen = unvisited_moves[0]

            self.x, self.y, self.z = chosen

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
        # STEP 2: SEARCH FOR NEAREST REACHABLE UNVISITED CELL
        # --------------------------------------------------

        target = self.find_nearest_unvisited_cell(
            disaster_map,
            sector,
            coordinator
        )

        if target is None:

            self.status = "EXPLORATION_COMPLETE"
            return

        # --------------------------------------------------
        # STEP 3: BUILD PATH TO UNVISITED CELL
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

        next_position = path[0]

        if coordinator.is_position_occupied(
            next_position,
            excluding_uav=self.id
        ):

            return

        self.x, self.y, self.z = next_position

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
    # FIND NEAREST UNVISITED CELL (BFS ON LAYER)
    # --------------------------------------------------

    def find_nearest_unvisited_cell(
        self,
        disaster_map,
        sector,
        coordinator
    ):

        start = self.get_position()
        sector_start_x, sector_end_x = sector

        queue = deque()
        queue.append(start)

        visited_search = set()
        visited_search.add(start)

        while queue:

            current = queue.popleft()

            if (
                current not in self.visited_cells
                and
                current != start
            ):

                return current

            for dx, dy, dz in DIRECTIONS_HORIZONTAL:

                next_x = current[0] + dx
                next_y = current[1] + dy
                next_z = current[2]

                next_position = (
                    next_x,
                    next_y,
                    next_z
                )

                if next_position in visited_search:

                    continue

                if not (
                    sector_start_x
                    <= next_x
                    <= sector_end_x
                ):

                    continue

                if not disaster_map.is_inside(next_x, next_y, next_z):

                    continue

                if disaster_map.is_blocked(next_x, next_y, next_z):

                    continue

                visited_search.add(
                    next_position
                )

                queue.append(
                    next_position
                )

        return None

    # --------------------------------------------------
    # FIND PATH TO EXPLORATION TARGET (BFS ON LAYER)
    # --------------------------------------------------

    def find_exploration_path(
        self,
        disaster_map,
        start,
        goal,
        sector,
        coordinator
    ):

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

            for dx, dy, dz in DIRECTIONS_HORIZONTAL:

                next_x = current[0] + dx
                next_y = current[1] + dy
                next_z = current[2]

                next_position = (
                    next_x,
                    next_y,
                    next_z
                )

                if next_position in came_from:

                    continue

                if not (
                    sector_start_x
                    <= next_x
                    <= sector_end_x
                ):

                    continue

                if not disaster_map.is_inside(next_x, next_y, next_z):

                    continue

                if disaster_map.is_blocked(next_x, next_y, next_z):

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

                came_from[next_position] = current

                queue.append(
                    next_position
                )

        if goal not in came_from:

            return []

        path = []
        current = goal

        while current != start:

            path.append(current)
            current = came_from[current]

        path.reverse()

        return path

    # --------------------------------------------------
    # SCAN FOR SURVIVORS (3D CUBE)
    # --------------------------------------------------

    def scan(
        self,
        disaster_map,
        sector,
        coordinator
    ):

        for dz in range(
            -self.sensor_range,
            self.sensor_range + 1
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
                    scan_z = self.z + dz

                    if not disaster_map.is_inside(scan_x, scan_y, scan_z):

                        continue

                    if (
                        disaster_map.grid[scan_z][scan_y][scan_x]
                        == SURVIVOR
                    ):

                        location = (
                            scan_x,
                            scan_y,
                            scan_z
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

            survivors = coordinator.get_survivors()

            sector_start_x, sector_end_x = sector

            available = [
                s for s in survivors
                if not
                coordinator.is_target_assigned(s)
                and
                sector_start_x
                <= s[0]
                <= sector_end_x
            ]

            if available:

                nearest = min(
                    available,
                    key=lambda location:
                    abs(location[0] - self.x)
                    +
                    abs(location[1] - self.y)
                    +
                    abs(location[2] - self.z)
                )

                assigned = coordinator.assign_target(
                    self.id,
                    nearest
                )

                if assigned:

                    self.target = nearest

                    print(
                        f"[UAV {self.id}] "
                        f"Target assigned: "
                        f"{nearest}"
                    )

            elif self.status in ("EXPLORING", "EXPLORATION_COMPLETE"):

                # Mutual Assistance: Request unassigned survivor across any sector
                cross_target = coordinator.request_cross_sector_target(
                    self.id,
                    self.get_position()
                )

                if cross_target:

                    self.target = cross_target
                    self.status = "EXPLORING"

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

        if self.get_position() != self.target:

            return

        target = self.target

        if disaster_map.rescue_survivor(target):

            coordinator.rescue_survivor(
                target,
                getattr(coordinator, "current_tick", 0)
            )

            self.rescued_count += 1

            print(
                f"[UAV {self.id}] "
                f"Survivor rescued at "
                f"{target}"
            )

        coordinator.clear_target(self.id)

        self.target = None
        self.path = []
        self.status = "EXPLORING"