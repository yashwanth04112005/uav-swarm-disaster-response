"""
BFS / Dijkstra pathfinding for 3D uniform-cost grids.
All edge costs = 1  ⇒  BFS guarantees optimal shortest paths
and is equivalent to Dijkstra with zero priority-queue overhead.
"""
import time
from collections import deque
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

    queue = deque([start])
    came_from = {start: None}

    while queue:
        current = queue.popleft()
        nodes_this += 1
        if current == goal:
            break
        for dx, dy, dz in DIRECTIONS_3D:
            nc = (current[0] + dx, current[1] + dy, current[2] + dz)
            if nc in came_from:
                continue
            if not valid(nc):
                continue
            came_from[nc] = current
            queue.append(nc)

    _nodes += nodes_this
    if goal not in came_from:
        _time_ns += time.perf_counter_ns() - t0
        return []

    path = []
    cur = goal
    while cur != start:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    _time_ns += time.perf_counter_ns() - t0
    return path
