import heapq


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def find_path(disaster_map, start, goal, sector):
    """
    Find a shortest 4-connected path from start to goal
    while keeping the UAV inside its assigned sector.
    """

    if start == goal:
        return []

    sector_start_x, sector_end_x = sector

    def is_valid(cell):

        x, y = cell

        # Stay inside assigned sector
        if not (
            sector_start_x
            <= x
            <= sector_end_x
        ):
            return False

        # Stay inside map
        if not (
            0 <= x < disaster_map.width
            and
            0 <= y < disaster_map.height
        ):
            return False

        # Avoid obstacles and hazards
        return disaster_map.grid[y][x] not in (
            1,  # OBSTACLE
            2   # HAZARD
        )

    # Goal cannot be reached
    if not is_valid(goal):
        return []

    frontier = []

    heapq.heappush(
        frontier,
        (0, start)
    )

    came_from = {
        start: None
    }

    cost_so_far = {
        start: 0
    }

    directions = [
        (0, -1),
        (0, 1),
        (-1, 0),
        (1, 0)
    ]

    while frontier:

        _, current = heapq.heappop(
            frontier
        )

        if current == goal:
            break

        for dx, dy in directions:

            next_cell = (
                current[0] + dx,
                current[1] + dy
            )

            if not is_valid(next_cell):
                continue

            new_cost = (
                cost_so_far[current] + 1
            )

            if (
                next_cell not in cost_so_far
                or
                new_cost
                < cost_so_far[next_cell]
            ):

                cost_so_far[next_cell] = (
                    new_cost
                )

                priority = (
                    new_cost
                    + heuristic(
                        next_cell,
                        goal
                    )
                )

                heapq.heappush(
                    frontier,
                    (
                        priority,
                        next_cell
                    )
                )

                came_from[next_cell] = (
                    current
                )

    # No path exists
    if goal not in came_from:
        return []

    # Reconstruct path
    path = []

    current = goal

    while current != start:

        path.append(current)

        current = came_from[current]

    path.reverse()

    return path