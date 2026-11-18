"""
D* Lite pathfinding for 3D grids  (Koenig & Likhachev 2002).

Searches backward from goal → start using g / rhs consistency.
In a single fresh call (no incremental map updates), it behaves
like backward A*. The real advantage of D* Lite appears when the
map changes between calls and only a small incremental replan is
needed — that benefit is not exercised here because each call
starts from scratch.
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

    INF = float('inf')
    g = {}
    rhs = {}
    km = 0
    seq = 0  # tie-breaker

    def G(s):
        return g.get(s, INF)

    def RHS(s):
        return rhs.get(s, INF)

    def calc_key(s):
        m = min(G(s), RHS(s))
        return (m + heuristic(start, s) + km, m)

    rhs[goal] = 0
    frontier = []
    heapq.heappush(frontier, (calc_key(goal), seq, goal))
    in_queue = {goal}

    def update_vertex(u):
        nonlocal seq
        if u != goal:
            best = INF
            for dx, dy, dz in DIRECTIONS_3D:
                s = (u[0] + dx, u[1] + dy, u[2] + dz)
                if valid(s):
                    v = G(s) + 1
                    if v < best:
                        best = v
            rhs[u] = best
        in_queue.discard(u)
        if G(u) != RHS(u):
            seq_val = seq
            seq += 1
            heapq.heappush(frontier, (calc_key(u), seq_val, u))
            in_queue.add(u)

    max_iters = 60000
    iters = 0

    while frontier and iters < max_iters:
        top_key = frontier[0][0]
        sk = calc_key(start)
        if top_key >= sk and RHS(start) == G(start):
            break

        _, _, u = heapq.heappop(frontier)
        if u not in in_queue:
            continue
        in_queue.discard(u)
        nodes_this += 1
        iters += 1

        if G(u) > RHS(u):
            g[u] = rhs[u]
            for dx, dy, dz in DIRECTIONS_3D:
                s = (u[0] + dx, u[1] + dy, u[2] + dz)
                if valid(s):
                    update_vertex(s)
        else:
            g[u] = INF
            update_vertex(u)
            for dx, dy, dz in DIRECTIONS_3D:
                s = (u[0] + dx, u[1] + dy, u[2] + dz)
                if valid(s):
                    update_vertex(s)

    _nodes += nodes_this

    if G(start) == INF:
        _time_ns += time.perf_counter_ns() - t0
        return []

    # Extract path: greedily follow minimum g towards goal
    path = []
    cur = start
    limit = 5000
    while cur != goal and limit > 0:
        best_next = None
        best_g = INF
        for dx, dy, dz in DIRECTIONS_3D:
            s = (cur[0] + dx, cur[1] + dy, cur[2] + dz)
            if valid(s) and G(s) < best_g:
                best_g = G(s)
                best_next = s
        if best_next is None or best_g >= G(cur):
            _time_ns += time.perf_counter_ns() - t0
            return []
        path.append(best_next)
        cur = best_next
        limit -= 1

    _time_ns += time.perf_counter_ns() - t0
    return path
