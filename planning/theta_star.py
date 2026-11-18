"""
Theta* (Any-Angle) pathfinding for 3D grids.

Like A*, but when updating a neighbour n of current node c,
Theta* checks line-of-sight from parent(c) to n.  If clear,
the path goes directly from parent(c) to n — skipping c.
This can reduce nodes explored via better parent assignments.

On a strict 6-connected grid the final step-count is the same
as A* (Manhattan distance is the minimum), but the waypoint
chain may differ, and node exploration can be lower.
"""
import time
import math
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


def _h(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _sign(v):
    return 1 if v > 0 else (-1 if v < 0 else 0)


def _line_of_sight(dmap, s1, s2, sx, ex):
    """3D DDA line-of-sight: True if the straight line is unblocked."""
    x0, y0, z0 = s1
    x1, y1, z1 = s2
    dx = x1 - x0
    dy = y1 - y0
    dz = z1 - z0
    steps = max(abs(dx), abs(dy), abs(dz))
    if steps == 0:
        return True
    xi = dx / steps
    yi = dy / steps
    zi = dz / steps
    x, y, z = float(x0), float(y0), float(z0)
    for _ in range(1, steps):
        x += xi
        y += yi
        z += zi
        ix, iy, iz = round(x), round(y), round(z)
        if not (sx <= ix <= ex):
            return False
        if dmap.is_blocked(ix, iy, iz):
            return False
    return True


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

    if not valid(goal):
        _time_ns += time.perf_counter_ns() - t0
        return []

    frontier = []
    counter = 0
    heapq.heappush(frontier, (0, counter, start))
    parent = {start: start}        # parent of start is itself
    g_cost = {start: 0}

    while frontier:
        _, _, current = heapq.heappop(frontier)
        nodes_this += 1
        if current == goal:
            break
        cg = g_cost.get(current)
        if cg is None:
            continue

        for dx, dy, dz in DIRECTIONS_3D:
            nb = (current[0] + dx, current[1] + dy, current[2] + dz)
            if not valid(nb):
                continue

            p = parent[current]
            # Theta* twist: try shortcutting through parent
            if _line_of_sight(disaster_map, p, nb, sx, ex):
                new_g = g_cost[p] + _h(p, nb)   # Manhattan = grid steps
                if nb not in g_cost or new_g < g_cost[nb]:
                    g_cost[nb] = new_g
                    parent[nb] = p
                    counter += 1
                    heapq.heappush(frontier, (new_g + _h(nb, goal), counter, nb))
            else:
                new_g = cg + 1
                if nb not in g_cost or new_g < g_cost[nb]:
                    g_cost[nb] = new_g
                    parent[nb] = current
                    counter += 1
                    heapq.heappush(frontier, (new_g + _h(nb, goal), counter, nb))

    _nodes += nodes_this

    if goal not in parent:
        _time_ns += time.perf_counter_ns() - t0
        return []

    # Reconstruct waypoints via parent chain
    waypoints = []
    cur = goal
    while cur != start:
        waypoints.append(cur)
        cur = parent[cur]
    waypoints.reverse()

    # Expand waypoints into cell-by-cell 6-connected path
    path = []
    prev = start
    for wp in waypoints:
        # Interleave axes (largest delta first) to stay close to straight line
        cx, cy, cz = prev
        tx, ty, tz = wp
        while (cx, cy, cz) != (tx, ty, tz):
            adx = abs(tx - cx)
            ady = abs(ty - cy)
            adz = abs(tz - cz)
            if adx >= ady and adx >= adz and adx > 0:
                cx += _sign(tx - cx)
            elif ady >= adx and ady >= adz and ady > 0:
                cy += _sign(ty - cy)
            elif adz > 0:
                cz += _sign(tz - cz)
            else:
                break
            path.append((cx, cy, cz))
        prev = wp

    _time_ns += time.perf_counter_ns() - t0
    return path
