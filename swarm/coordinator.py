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
    # SURVIVOR MANAGEMENT
    # ==================================================

    def add_survivor(self, location):

        if location in self.rescued_survivors:
            return

        self.shared_survivors.add(
            location
        )

    def get_survivors(self):

        return self.shared_survivors

    def rescue_survivor(self, location):

        self.rescued_survivors.add(
            location
        )

        self.shared_survivors.discard(
            location
        )

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

    # ==================================================
    # TARGET ASSIGNMENT
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