class SwarmCoordinator:

    def __init__(
        self,
        map_width,
        map_height,
        map_depth=6,
        num_uavs=None
    ):

        self.map_width = map_width
        self.map_height = map_height

        if num_uavs is None:
            # Backwards compatibility: called as (map_width, map_height, num_uavs)
            self.num_uavs = map_depth
            self.map_depth = 6
        else:
            self.map_depth = map_depth
            self.num_uavs = num_uavs

        # ==================================================
        # TIME & PERFORMANCE ANALYTICS
        # ==================================================

        self.current_tick = 0
        self.survivor_detection_ticks = {}
        self.survivor_rescue_ticks = {}

        # ==================================================
        # SHARED INFORMATION
        # ==================================================

        self.shared_survivors = set()

        # Ground footprint coverage: (x, y) coordinates
        self.shared_coverage = set()

        self.rescued_survivors = set()

        # ==================================================
        # UAV INFORMATION
        # ==================================================

        self.uav_positions = {}

        self.uav_bases = {}

        # UAV ID -> survivor location (x, y, z)
        self.assigned_targets = {}

        # ==================================================
        # SECTOR ASSIGNMENTS
        # ==================================================

        self.sectors = []

        sector_width = (
            map_width // self.num_uavs
        )

        for i in range(self.num_uavs):

            start_x = (
                i * sector_width
            )

            if i == self.num_uavs - 1:

                end_x = (
                    map_width - 1
                )

            else:

                end_x = (
                    (i + 1)
                    * sector_width
                    - 1
                )

            self.sectors.append(
                (
                    start_x,
                    end_x
                )
            )

    # ==================================================
    # SECTOR MANAGEMENT
    # ==================================================

    def get_sector(self, uav_id):

        return self.sectors[
            uav_id - 1
        ]

    # ==================================================
    # SURVIVOR MANAGEMENT & ANALYTICS
    # ==================================================

    def add_survivor(self, location, tick=None):

        if location in self.rescued_survivors:
            return

        self.shared_survivors.add(
            location
        )

        if location not in self.survivor_detection_ticks:
            t = self.current_tick if tick is None else tick
            self.survivor_detection_ticks[location] = t

    def get_survivors(self):

        return self.shared_survivors

    def rescue_survivor(self, location, tick=None):

        self.rescued_survivors.add(
            location
        )

        self.shared_survivors.discard(
            location
        )

        t = self.current_tick if tick is None else tick
        self.survivor_rescue_ticks[location] = t

        # Remove any assignment for this survivor
        for uav_id, target in list(
            self.assigned_targets.items()
        ):

            if target == location:

                del self.assigned_targets[
                    uav_id
                ]

    def get_rescued_survivors(self):

        return self.rescued_survivors

    def get_mean_time_to_rescue(self):
        """Returns average ticks from detection to rescue."""
        if not self.survivor_rescue_ticks:
            return 0.0

        durations = []
        for loc, r_tick in self.survivor_rescue_ticks.items():
            d_tick = self.survivor_detection_ticks.get(loc, 0)
            durations.append(max(0, r_tick - d_tick))

        return sum(durations) / len(durations) if durations else 0.0

    # ==================================================
    # TARGET ASSIGNMENT & CROSS-SECTOR ASSISTANCE
    # ==================================================

    def assign_target(
        self,
        uav_id,
        target
    ):

        # Survivor already rescued
        if target in self.rescued_survivors:

            return False

        # Survivor already assigned to another UAV
        for assigned_uav, assigned_target in (
            self.assigned_targets.items()
        ):

            if (
                assigned_target == target
                and
                assigned_uav != uav_id
            ):

                return False

        self.assigned_targets[
            uav_id
        ] = target

        return True

    def request_cross_sector_target(self, uav_id, uav_pos):
        """
        Cross-Sector Mutual Assistance:
        If a UAV has no targets in its own sector, find the nearest
        unassigned survivor in any sector across the map.
        """
        available = [
            s for s in self.shared_survivors
            if not self.is_target_assigned(s)
            and s not in self.rescued_survivors
        ]

        if not available:
            return None

        # Find closest survivor across all sectors
        nearest = min(
            available,
            key=lambda loc: (
                abs(loc[0] - uav_pos[0]) +
                abs(loc[1] - uav_pos[1]) +
                abs(loc[2] - uav_pos[2])
            )
        )

        if self.assign_target(uav_id, nearest):
            print(f"[MUTUAL ASSISTANCE] UAV {uav_id} dispatched across sectors to target {nearest}!")
            return nearest

        return None

    def get_assigned_target(
        self,
        uav_id
    ):

        return self.assigned_targets.get(
            uav_id
        )

    def clear_target(
        self,
        uav_id
    ):

        self.assigned_targets.pop(
            uav_id,
            None
        )

    def is_target_assigned(
        self,
        target
    ):

        return target in (
            self.assigned_targets.values()
        )

    # ==================================================
    # COVERAGE MANAGEMENT (PROJECTED GROUND FOOTPRINT)
    # ==================================================

    def add_coverage(
        self,
        location
    ):

        self.shared_coverage.add(
            (location[0], location[1])
        )

    def add_coverage_cells(
        self,
        cells
    ):

        for cell in cells:
            self.shared_coverage.add(
                (cell[0], cell[1])
            )

    def get_coverage(self):

        return self.shared_coverage

    def get_coverage_percentage(self):

        total_cells = (
            self.map_width
            * self.map_height
        )

        if total_cells == 0:

            return 0.0

        return (
            len(self.shared_coverage)
            / total_cells
        ) * 100

    # ==================================================
    # UAV POSITION MANAGEMENT
    # ==================================================

    def update_uav_position(
        self,
        uav_id,
        position
    ):

        self.uav_positions[
            uav_id
        ] = position

    def get_uav_positions(self):

        return self.uav_positions

    # ==================================================
    # UAV BASE MANAGEMENT
    # ==================================================

    def set_base(
        self,
        uav_id,
        position
    ):

        self.uav_bases[
            uav_id
        ] = position

    def get_base(
        self,
        uav_id
    ):

        return self.uav_bases.get(
            uav_id
        )

    # ==================================================
    # COLLISION DETECTION (3D VOXEL OCCUPANCY)
    # ==================================================

    def is_position_occupied(
        self,
        position,
        excluding_uav=None
    ):

        for uav_id, uav_position in (
            self.uav_positions.items()
        ):

            if (
                excluding_uav is not None
                and
                uav_id == excluding_uav
            ):

                continue

            if uav_position == position:

                return True

        return False