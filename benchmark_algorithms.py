#!/usr/bin/env python3
"""
Headless benchmark: runs the full UAV Swarm Disaster Response simulation
with each of 7 pathfinding algorithms across 5 random seeds, then
prints a comparison table and writes results to JSON.
"""
import sys, os, io, json, time, random, contextlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from environment.map import DisasterMap, EMPTY, SURVIVOR
from swarm.coordinator import SwarmCoordinator
from agents.uav import UAV

# ── algorithm modules ──────────────────────────────────────────
from planning import a_star_stats, bfs, d_star_lite, jps, theta_star, rrt, potential_field

ALGORITHMS = [
    ("A*",              a_star_stats),
    ("BFS/Dijkstra",    bfs),
    ("D* Lite",         d_star_lite),
    ("JPS",             jps),
    ("Theta*",          theta_star),
    ("RRT",             rrt),
    ("Potential Field",  potential_field),
]

# ── simulation parameters (must match main.py) ────────────────
SEEDS        = [42, 123, 456, 789, 1024]
MAX_TICKS    = 1500
HAZARD_EVERY = 20       # ticks  (8000 ms / 400 ms per tick at 1×)
GRID_W, GRID_H, GRID_D = 25, 20, 6
NUM_UAVS     = 5
UAV_COLORS   = [
    (0, 110, 255), (235, 45, 45), (15, 175, 45),
    (170, 30, 200), (240, 150, 10),
]


def _spawn(dmap, sx, ex):
    for _ in range(GRID_W * GRID_H * 10):
        x = random.randint(sx, ex)
        y = random.randint(0, GRID_H - 1)
        if dmap.grid[0][y][x] == EMPTY:
            return x, y
    return sx, 0


def run_sim(algo_mod, seed):
    """Run one headless simulation; return metrics dict."""
    random.seed(seed)

    dmap  = DisasterMap(GRID_W, GRID_H, GRID_D)
    dmap.generate()

    coord = SwarmCoordinator(GRID_W, GRID_H, GRID_D, NUM_UAVS)

    uavs = []
    for i in range(NUM_UAVS):
        uid   = i + 1
        s, e  = coord.get_sector(uid)
        sx, sy = _spawn(dmap, s, e)
        u = UAV(drone_id=uid, x=sx, y=sy, z=0,
                color=UAV_COLORS[i], search_altitude=2)
        uavs.append(u)
        coord.update_uav_position(uid, u.get_position())
        coord.set_base(uid, u.base_position)
        coord.add_coverage(u.get_position())

    # ── monkey-patch find_path in agents.uav ───────────────
    import agents.uav as _uav_mod
    _orig = _uav_mod.find_path
    _uav_mod.find_path = algo_mod.find_path

    if hasattr(algo_mod, "reset_stats"):
        algo_mod.reset_stats()

    completed  = False
    final_tick = MAX_TICKS

    # Suppress console spam from UAV / coordinator
    _stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        for tick in range(MAX_TICKS):
            coord.current_tick = tick

            for u in uavs:
                if u.status == "DEAD":
                    continue
                sec = coord.get_sector(u.id)
                u.move(dmap, sec, coord)
                coord.update_uav_position(u.id, u.get_position())
                coord.add_coverage_cells(u.visited_cells)
                u.scan(dmap, sec, coord)
                u.attempt_rescue(dmap, coord)

            if tick > 0 and tick % HAZARD_EVERY == 0:
                dmap.expand_hazards()

            active = sum(
                1 for z in range(GRID_D)
                for y in range(GRID_H)
                for x in range(GRID_W)
                if dmap.grid[z][y][x] == SURVIVOR
            )
            if active == 0 and len(coord.get_rescued_survivors()) > 0:
                completed  = True
                final_tick = tick + 1
                break
    finally:
        sys.stdout = _stdout
        _uav_mod.find_path = _orig

    stats = algo_mod.get_stats() if hasattr(algo_mod, "get_stats") else {}

    return {
        "ticks":          final_tick,
        "completed":      completed,
        "rescued":        len(coord.get_rescued_survivors()),
        "coverage_pct":   round(coord.get_coverage_percentage(), 1),
        "mttr":           round(coord.get_mean_time_to_rescue(), 1),
        "total_distance": sum(u.total_distance for u in uavs),
        "total_energy":   sum(u.total_energy_consumed for u in uavs),
        "total_recharges":sum(u.recharge_count   for u in uavs),
        "path_calls":     stats.get("calls", 0),
        "nodes_explored": stats.get("nodes_explored", 0),
        "pf_time_ms":     round(stats.get("time_ms", 0), 2),
    }


# ── main ───────────────────────────────────────────────────────
def main():
    all_results = {}

    for algo_name, algo_mod in ALGORITHMS:
        print(f"\n{'=' * 70}")
        print(f"  Benchmarking: {algo_name}")
        print(f"{'=' * 70}")

        runs = []
        for seed in SEEDS:
            print(f"  Seed {seed:>5} ...", end=" ", flush=True)
            t0 = time.perf_counter()
            try:
                r = run_sim(algo_mod, seed)
                runs.append(r)
                wall = time.perf_counter() - t0
                tag = "COMPLETE" if r["completed"] else f"INCOMPLETE ({r['rescued']} rescued)"
                print(f"{tag:>22s}  ticks={r['ticks']:>5}  "
                      f"MTTR={r['mttr']:>6.1f}  dist={r['total_distance']:>5}  "
                      f"pathCalls={r['path_calls']:>5}  "
                      f"pfTime={r['pf_time_ms']:>8.1f}ms  "
                      f"wall={wall:.1f}s")
            except Exception as e:
                print(f"ERROR: {e}")
                runs.append({
                    "ticks": MAX_TICKS, "completed": False, "rescued": 0,
                    "coverage_pct": 0, "mttr": 0, "total_distance": 0,
                    "total_energy": 0, "total_recharges": 0,
                    "path_calls": 0, "nodes_explored": 0, "pf_time_ms": 0,
                })

        all_results[algo_name] = runs

    # ── summary table ──────────────────────────────────────────
    n = len(SEEDS)
    print(f"\n\n{'=' * 130}")
    print(f"{'PATHFINDING ALGORITHM COMPARISON — SUMMARY (averaged over ' + str(n) + ' seeds)':^130}")
    print(f"{'=' * 130}")

    hdr = (f"{'Algorithm':<18} {'Success':>7} {'Avg Ticks':>10} {'Avg MTTR':>9} "
           f"{'Avg Dist':>9} {'Avg Energy':>10} {'Recharges':>9} "
           f"{'PathCalls':>10} {'Nodes':>12} {'PF ms':>10} {'Nodes/Call':>11} {'us/Call':>9}")
    print(hdr)
    print("-" * 130)

    summary_rows = []

    for algo_name, runs in all_results.items():
        succ      = sum(1 for r in runs if r["completed"])
        avg_tick  = sum(r["ticks"]          for r in runs) / n
        avg_mttr  = sum(r["mttr"]           for r in runs) / n
        avg_dist  = sum(r["total_distance"] for r in runs) / n
        avg_en    = sum(r["total_energy"]   for r in runs) / n
        avg_rch   = sum(r["total_recharges"]for r in runs) / n
        tot_calls = sum(r["path_calls"]     for r in runs)
        tot_nodes = sum(r["nodes_explored"] for r in runs)
        tot_pf_ms = sum(r["pf_time_ms"]    for r in runs)
        npc       = tot_nodes / tot_calls if tot_calls else 0
        uspc      = (tot_pf_ms * 1000) / tot_calls if tot_calls else 0

        row = (f"{algo_name:<18} {succ:>3}/{n:<3} {avg_tick:>10.1f} {avg_mttr:>9.1f} "
               f"{avg_dist:>9.1f} {avg_en:>10.1f} {avg_rch:>9.1f} "
               f"{tot_calls:>10} {tot_nodes:>12} {tot_pf_ms:>10.1f} "
               f"{npc:>11.1f} {uspc:>9.1f}")
        print(row)

        summary_rows.append({
            "algorithm":    algo_name,
            "success":      f"{succ}/{n}",
            "avg_ticks":    round(avg_tick, 1),
            "avg_mttr":     round(avg_mttr, 1),
            "avg_distance": round(avg_dist, 1),
            "avg_energy":   round(avg_en, 1),
            "avg_recharges":round(avg_rch, 1),
            "total_path_calls":  tot_calls,
            "total_nodes":       tot_nodes,
            "total_pf_time_ms":  round(tot_pf_ms, 2),
            "nodes_per_call":    round(npc, 1),
            "us_per_call":       round(uspc, 1),
        })

    print(f"{'=' * 130}\n")

    # ── write JSON ─────────────────────────────────────────────
    out = {"seeds": SEEDS, "max_ticks": MAX_TICKS, "grid": [GRID_W, GRID_H, GRID_D],
           "num_uavs": NUM_UAVS, "summary": summary_rows, "raw": all_results}
    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_results.json")
    with open(outpath, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Full results written to {outpath}")


if __name__ == "__main__":
    main()
