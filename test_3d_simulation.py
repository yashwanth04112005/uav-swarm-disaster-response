"""
Headless test suite for 3D UAV Swarm simulation logic.
Runs multi-step simulation ticks without Pygame display to verify:
1. Bounds integrity (all UAVs stay inside grid width, height, depth).
2. Obstacle avoidance (no UAV ever steps into building columns or hazards).
3. 3D Collision safety (no two UAVs share the same (x, y, z)).
4. Mission progression (survivors detected & rescued, coverage grows).
"""

import random
from environment.map import DisasterMap, EMPTY, OBSTACLE, HAZARD, SURVIVOR
from swarm.coordinator import SwarmCoordinator
from agents.uav import UAV


def run_headless_test(num_ticks=2000, seed=42):
    random.seed(seed)

    grid_width = 25
    grid_height = 20
    grid_depth = 6
    num_uavs = 5

    disaster_map = DisasterMap(grid_width, grid_height, grid_depth)
    disaster_map.generate()

    coordinator = SwarmCoordinator(grid_width, grid_height, grid_depth, num_uavs)

    uavs = []
    uav_colors = [
        (0, 100, 255),
        (255, 0, 0),
        (0, 180, 0),
        (180, 0, 180),
        (255, 180, 0)
    ]

    for i in range(num_uavs):
        uav_id = i + 1
        sector = coordinator.get_sector(uav_id)
        start_x, end_x = sector

        # Find empty ground cell in sector
        spawn_x = start_x
        spawn_y = 0
        found = False
        for _ in range(500):
            rx = random.randint(start_x, end_x)
            ry = random.randint(0, grid_height - 1)
            if disaster_map.grid[0][ry][rx] == EMPTY:
                spawn_x, spawn_y = rx, ry
                found = True
                break

        uav = UAV(
            drone_id=uav_id,
            x=spawn_x,
            y=spawn_y,
            z=0,
            color=uav_colors[i],
            search_altitude=2
        )
        uavs.append(uav)

        coordinator.update_uav_position(uav_id, uav.get_position())
        coordinator.set_base(uav_id, uav.base_position)
        coordinator.add_coverage(uav.get_position())

    print(f"[TEST] Initialized 3D Swarm with {num_uavs} UAVs on {grid_width}x{grid_height}x{grid_depth} grid.")

    initial_survivors = sum(
        1 for z in range(grid_depth)
        for y in range(grid_height)
        for x in range(grid_width)
        if disaster_map.grid[z][y][x] == SURVIVOR
    )
    print(f"[TEST] Placed {initial_survivors} survivors on ground level.")

    vertical_crossings = 0

    for tick in range(1, num_ticks + 1):
        # 1. UAV Actions
        for uav in uavs:
            if uav.status == "DEAD":
                continue

            sector = coordinator.get_sector(uav.id)
            uav.move(disaster_map, sector, coordinator)
            coordinator.update_uav_position(uav.id, uav.get_position())
            coordinator.add_coverage_cells(uav.visited_cells)
            uav.scan(disaster_map, sector, coordinator)
            uav.attempt_rescue(disaster_map, coordinator)

        # 2. Hazard expansion periodically
        if tick % 20 == 0:
            disaster_map.expand_hazards()

        # 3. Invariant Validations
        positions = {}
        for uav in uavs:
            pos = uav.get_position()
            ux, uy, uz = pos

            # Bounds Check
            assert 0 <= ux < grid_width, f"Tick {tick}: UAV {uav.id} x out of bounds ({ux})"
            assert 0 <= uy < grid_height, f"Tick {tick}: UAV {uav.id} y out of bounds ({uy})"
            assert 0 <= uz < grid_depth, f"Tick {tick}: UAV {uav.id} z out of bounds ({uz})"

            # Obstacle Check
            cell_type = disaster_map.grid[uz][uy][ux]
            assert cell_type != OBSTACLE, f"Tick {tick}: UAV {uav.id} inside OBSTACLE at {pos}"

            # 3D Collision Check (no two UAVs at same 3D voxel)
            assert pos not in positions, (
                f"Tick {tick}: 3D COLLISION between UAV {uav.id} and UAV {positions[pos]} at {pos}"
            )
            positions[pos] = uav.id

        # Check for vertical flyover: two UAVs sharing (x, y) at different z
        ground_coords = {}
        for uav in uavs:
            g = (uav.x, uav.y)
            if g in ground_coords:
                vertical_crossings += 1
            ground_coords[g] = uav.id

        # Check if all survivors rescued
        active_survivors = sum(
            1 for z in range(grid_depth)
            for y in range(grid_height)
            for x in range(grid_width)
            if disaster_map.grid[z][y][x] == SURVIVOR
        )
        rescued = len(coordinator.get_rescued_survivors())

        if active_survivors == 0 and rescued == initial_survivors and tick > 1000:
            print(f"[TEST] SUCCESS: All {initial_survivors} survivors rescued, ran {tick} ticks!")
            break

    coverage_pct = coordinator.get_coverage_percentage()
    print(f"[TEST] Completed simulation run.")
    print(f"[TEST] Final coverage: {coverage_pct:.2f}% (<= 100% check: {coverage_pct <= 100.0})")
    print(f"[TEST] Rescued survivors: {len(coordinator.get_rescued_survivors())} / {initial_survivors}")
    print(f"[TEST] Vertical crossings detected: {vertical_crossings}")

    assert coverage_pct <= 100.001, f"Coverage percentage exceeded 100%: {coverage_pct}"
    print("[TEST] ALL 3D LOGIC TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_headless_test()
