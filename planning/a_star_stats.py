"""
Instrumented A* pathfinding — identical to a_star.py but tracks
calls, nodes explored, and cumulative time for benchmarking.
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
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost = {start: 0}

    while frontier:
        _, current = heapq.heappop(frontier)
        nodes_this += 1
        if current == goal:
            break
        for dx, dy, dz in DIRECTIONS_3D:
            nc = (current[0] + dx, current[1] + dy, current[2] + dz)
            if not valid(nc):
                continue
            g = cost[current] + 1
            if nc not in cost or g < cost[nc]:
                cost[nc] = g
                heapq.heappush(frontier, (g + heuristic(nc, goal), nc))
                came_from[nc] = current

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
