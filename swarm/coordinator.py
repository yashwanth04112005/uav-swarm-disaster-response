class SwarmCoordinator:

    def __init__(self, map_width, map_height, num_uavs):

        self.map_width = map_width
        self.map_height = map_height

        # Shared survivor information
        self.shared_survivors = set()

        # Shared coverage information
        self.shared_coverage = set()

        # Sector assignments
        self.sectors = []

        sector_width = map_width // num_uavs

        for i in range(num_uavs):

            start_x = i * sector_width

            if i == num_uavs - 1:
                end_x = map_width - 1
            else:
                end_x = (i + 1) * sector_width - 1

            self.sectors.append(
                (start_x, end_x)
            )

    def get_sector(self, uav_id):

        return self.sectors[uav_id - 1]

    def add_survivor(self, location):

        self.shared_survivors.add(location)

    def get_survivors(self):

        return self.shared_survivors

    def add_coverage(self, location):

        self.shared_coverage.add(location)

    def add_coverage_cells(self, cells):

        self.shared_coverage.update(cells)

    def get_coverage(self):

        return self.shared_coverage

    def get_coverage_percentage(self):

        total_cells = (
            self.map_width *
            self.map_height
        )

        if total_cells == 0:
            return 0.0

        return (
            len(self.shared_coverage) /
            total_cells
        ) * 100