"""
Grid-based Rapidly-exploring Random Tree (RRT) for 3D grids.

RRT is a sampling-based planner from robotics. It does NOT
guarantee optimal paths — paths are typically longer than A*.
Useful as a contrast baseline showing the cost of non-informed
search.

Uses a separate Random instance so the main simulation's
random state (map generation, hazard expansion) is unaffected.
"""
import time
import random as _random_mod
from environment.map import DIRECTIONS_3D

_calls = 0
_nodes = 0
_time_ns = 0
_rng = _random_mod.Random()          # independent RNG


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
    w = disaster_map.width
    h = disaster_map.height
    d = disaster_map.depth

    def valid(c):
        x, y, z = c
        if not (sx <= x <= ex):
            return False
        return not disaster_map.is_blocked(x, y, z)

    if not valid(goal):
        _time_ns += time.perf_counter_ns() - t0
        return []

    tree = {start: None}          # node → parent
    GOAL_BIAS = 0.20
    MAX_ITER = 8000
    MAX_EXTEND = 5

    for _ in range(MAX_ITER):
        nodes_this += 1

        # --- sample ---
        if _rng.random() < GOAL_BIAS:
            sample = goal
        else:
            sample = (_rng.randint(sx, ex),
                      _rng.randint(0, h - 1),
                      _rng.randint(0, d - 1))

        # --- nearest node (Manhattan) ---
        nearest = min(tree, key=lambda n: _h(n, sample))

        # --- extend along dominant axis ---
        dx = abs(sample[0] - nearest[0])
        dy = abs(sample[1] - nearest[1])
        dz = abs(sample[2] - nearest[2])
        axes = sorted(
            [
                (dx, (_sign(sample[0] - nearest[0]), 0, 0)),
                (dy, (0, _sign(sample[1] - nearest[1]), 0)),
                (dz, (0, 0, _sign(sample[2] - nearest[2]))),
            ],
            reverse=True,
        )

        cur = nearest
        added_any = False
        for _, step in axes:
            if step == (0, 0, 0):
                continue
            for _ in range(MAX_EXTEND):
                nxt = (cur[0] + step[0], cur[1] + step[1], cur[2] + step[2])
                if nxt in tree:
                    break
                if not valid(nxt):
                    break
                tree[nxt] = cur
                cur = nxt
                added_any = True
                if nxt == goal:
                    # --- extract path ---
                    path = []
                    c = goal
                    while c != start:
                        path.append(c)
                        c = tree[c]
                    path.reverse()
                    _nodes += nodes_this
                    _time_ns += time.perf_counter_ns() - t0
                    return path
            if added_any:
                break  # extended along first viable axis

    # Failed to reach goal
    _nodes += nodes_this
    _time_ns += time.perf_counter_ns() - t0
    return []
