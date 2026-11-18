"""
Potential Field pathfinding for 3D grids.

Gradient descent on a combined potential:
  P(cell) = P_attractive(cell) + P_repulsive(cell)

  P_attractive  = Manhattan distance to goal
  P_repulsive   = sum of  k / dist²  for every obstacle within radius

This is a reactive / greedy method. It is NOT optimal and can
get trapped in local minima. An oscillation detector triggers
random escape steps when stuck.

Uses a separate Random instance to avoid disturbing the main
simulation random state.
"""
import time
import random as _random_mod
from environment.map import DIRECTIONS_3D

_calls = 0
_nodes = 0
_time_ns = 0
_rng = _random_mod.Random()


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
    REP_K = 4.0
    REP_RAD = 2
    MAX_STEPS = 800

    def valid(c):
        x, y, z = c
        if not (sx <= x <= ex):
            return False
        return not disaster_map.is_blocked(x, y, z)

    if not valid(goal):
        _time_ns += time.perf_counter_ns() - t0
        return []

    def potential(c):
        x, y, z = c
        p_att = abs(x - goal[0]) + abs(y - goal[1]) + abs(z - goal[2])
        p_rep = 0.0
        for dz in range(-REP_RAD, REP_RAD + 1):
            for dy in range(-REP_RAD, REP_RAD + 1):
                for dx in range(-REP_RAD, REP_RAD + 1):
                    ox, oy, oz = x + dx, y + dy, z + dz
                    if disaster_map.is_inside(ox, oy, oz) and disaster_map.is_blocked(ox, oy, oz):
                        d = abs(dx) + abs(dy) + abs(dz)
                        if d > 0:
                            p_rep += REP_K / (d * d)
        return p_att + p_rep

    path = []
    cur = start
    visit_count = {}

    for _ in range(MAX_STEPS):
        nodes_this += 1
        if cur == goal:
            break

        candidates = []
        for dx, dy, dz in DIRECTIONS_3D:
            nb = (cur[0] + dx, cur[1] + dy, cur[2] + dz)
            if valid(nb):
                candidates.append((potential(nb), nb))

        if not candidates:
            break

        candidates.sort()
        best = candidates[0][1]

        # Oscillation escape: if revisiting too often, random walk
        vc = visit_count.get(best, 0)
        if vc > 2 and len(candidates) > 1:
            best = _rng.choice(candidates)[1]

        visit_count[best] = visit_count.get(best, 0) + 1
        path.append(best)
        cur = best

    _nodes += nodes_this

    if cur != goal:
        _time_ns += time.perf_counter_ns() - t0
        return []  # failed

    _time_ns += time.perf_counter_ns() - t0
    return path
