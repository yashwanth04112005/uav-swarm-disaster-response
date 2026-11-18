"""
Jump Point Search (JPS) adapted for 6-connected 3D grids.

Instead of expanding every neighbour like A*, JPS "jumps" along
straight lines until it finds a forced neighbour (obstacle that
creates a detour), the goal, or a dead end. This dramatically
reduces the number of nodes added to the open list while still
guaranteeing optimality.
"""
import time
import heapq
from environment.map import DIRECTIONS_3D

_calls = 0
_nodes = 0
_time_ns = 0


def reset_stats():
    global _calls, _nodes, _time_ns
    _calls = _nodes = _time_ns = 0


def get_stats():
    return {
        'calls': _calls,
        'nodes_explored': _nodes,
        'time_ms': _time_ns / 1_000_000
    }


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _sign(v):
    return 1 if v > 0 else (-1 if v < 0 else 0)


def find_path(disaster_map, start, goal, sector):
    global _calls, _nodes, _time_ns
    _calls += 1
    t0 = time.perf_counter_ns()
    nodes_this = 0

    if len(start) == 2:
        start = (start[0], start[1], 0)
    if len(goal) == 2:
        goal = (goal[0], goal[1], 0)
    if start == goal:
        _time_ns += time.perf_counter_ns() - t0
        return []

    sx, ex = sector

    def valid(c):
        x, y, z = c
        if not (sx <= x <= ex):
            return False
        return not disaster_map.is_blocked(x, y, z)

    def blocked_or_oob(x, y, z):
        if not disaster_map.is_inside(x, y, z):
            return True
        if not (sx <= x <= ex):
            return True
        return disaster_map.is_blocked(x, y, z)

    if not valid(goal):
        _time_ns += time.perf_counter_ns() - t0
        return []

    # Perpendicular directions for a movement direction
    def perp_dirs(dx, dy, dz):
        return [(ddx, ddy, ddz) for ddx, ddy, ddz in DIRECTIONS_3D
                if (ddx, ddy, ddz) != (dx, dy, dz) and (ddx, ddy, ddz) != (-dx, -dy, -dz)]

    def jump(x, y, z, dx, dy, dz, max_steps=100):
        """Jump from (x,y,z) in direction (dx,dy,dz). Return jump point or None."""
        cx, cy, cz = x, y, z
        for _ in range(max_steps):
            nx, ny, nz = cx + dx, cy + dy, cz + dz
            if not valid((nx, ny, nz)):
                return None
            if (nx, ny, nz) == goal:
                return (nx, ny, nz)

            # Check forced neighbours
            for pdx, pdy, pdz in perp_dirs(dx, dy, dz):
                # Blocked perpendicular at current pos, free at next pos
                if blocked_or_oob(cx + pdx, cy + pdy, cz + pdz):
                    if valid((nx + pdx, ny + pdy, nz + pdz)):
                        return (nx, ny, nz)

            cx, cy, cz = nx, ny, nz
        return None

    # A* over jump points
    frontier = []
    counter = 0
    heapq.heappush(frontier, (heuristic(start, goal), counter, start))
    came_from = {start: None}
    cost = {start: 0}

    while frontier:
        _, _, current = heapq.heappop(frontier)
        nodes_this += 1

        if current == goal:
            break

        # Skip stale entries
        cur_cost = cost.get(current)
        if cur_cost is None:
            continue

        for dx, dy, dz in DIRECTIONS_3D:
            jp = jump(current[0], current[1], current[2], dx, dy, dz)
            if jp is None:
                continue
            dist = heuristic(current, jp)
            g = cur_cost + dist
            if jp not in cost or g < cost[jp]:
                cost[jp] = g
                counter += 1
                heapq.heappush(frontier, (g + heuristic(jp, goal), counter, jp))
                came_from[jp] = current

    _nodes += nodes_this

    if goal not in came_from:
        _time_ns += time.perf_counter_ns() - t0
        return []

    # Reconstruct waypoints
    waypoints = []
    cur = goal
    while cur != start:
        waypoints.append(cur)
        cur = came_from[cur]
    waypoints.reverse()

    # Fill intermediate cells between consecutive jump points
    path = []
    prev = start
    for wp in waypoints:
        dx = _sign(wp[0] - prev[0])
        dy = _sign(wp[1] - prev[1])
        dz = _sign(wp[2] - prev[2])
        c = prev
        while c != wp:
            c = (c[0] + dx, c[1] + dy, c[2] + dz)
            path.append(c)
        prev = wp

    _time_ns += time.perf_counter_ns() - t0
    return path
