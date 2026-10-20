import heapq
from environment.map import DIRECTIONS_3D


def heuristic(a, b):
    az = a[2] if len(a) > 2 else 0
    bz = b[2] if len(b) > 2 else 0
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(az - bz)


def find_path(disaster_map, start, goal, sector):
    """
    Find a shortest 6-connected 3D path from start to goal
    while keeping the UAV inside its assigned sector (x-range).
    """

    if len(start) == 2:
        start = (start[0], start[1], 0)
    if len(goal) == 2:
        goal = (goal[0], goal[1], 0)

    if start == goal:
        return []

    sector_start_x, sector_end_x = sector

    def is_valid(cell):

        x, y, z = cell

        # Stay inside assigned sector
        if not (
            sector_start_x
            <= x
            <= sector_end_x
        ):
            return False

        # Stay inside map and avoid obstacles and hazards
        return not disaster_map.is_blocked(x, y, z)

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

    while frontier:

        _, current = heapq.heappop(
            frontier
        )

        if current == goal:
            break

        for dx, dy, dz in DIRECTIONS_3D:

            next_cell = (
                current[0] + dx,
                current[1] + dy,
                current[2] + dz
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