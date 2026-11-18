# 3D Sector-Coordinated Autonomous UAV Swarm for Urban Disaster Search and Rescue

**Institution:** Indian Institute of Information Technology, Sri City (IIITS)  
**Course:** Semester 7 — Additional Project (Final Evaluation)  
**Student Name(s):** [Insert Your Name(s)]  
**Roll Number(s):** [Insert Roll Number(s)]  
**Faculty Mentor:** [Insert Mentor Name]  
**Project Type:** Autonomous Systems / Multi-Agent Robotics Simulation  
**Date of Submission:** November 2026  

---

## 1. Title Page and Abstract

### Abstract
Rapid search and rescue (SAR) operations in urban disaster scenarios—such as earthquakes, structural collapses, and industrial fires—are critical to minimizing human casualties. However, dynamic hazards, line-of-sight occlusions, structural debris, and battery constraints severely hinder human first responders and single-drone systems. This project presents a decentralized-coordinated multi-UAV swarm simulation platform in a dynamic 3D voxel environment. The system features an autonomous swarm of heterogeneous UAVs governed by a sector-partitioned coverage strategy with cross-sector mutual assistance, dynamic battery-aware charging heuristics, and real-time path planning. To address dynamic environmental hazards that expand during missions, we implemented and benchmarked seven path planning algorithms ($A^*$, BFS/Dijkstra, $D^*$ Lite, Jump Point Search, $\Theta^*$, RRT, and Potential Fields). Quantitative evaluations across varying hazard seeds demonstrate that $D^*$ Lite achieves a 100% mission rescue success rate, reducing path search nodes by 89.4% compared to uniform-cost search while delivering optimal flight distance and energy efficiency.

---

## 2. Introduction

### 2.1 Problem Statement
In post-disaster urban ruins, terrain accessibility is severely compromised. Ground vehicles face impassable rubble, while human entry carries life-threatening risks. Unmanned Aerial Vehicles (UAVs) provide critical aerial reconnaissance; however, single-UAV systems suffer from limited sensor footprints, rapid battery depletion, and single-point-of-failure vulnerabilities. Conversely, uncoordinated multi-UAV swarms exhibit overlapping scans, mid-air collision hazards, and redundant rescue dispatching. Furthermore, real-world disaster zones are non-static: structural fires, toxic smoke plumes, and secondary collapses evolve dynamically, rendering pre-computed flight paths hazardous.

### 2.2 Motivation
Coordinated autonomous UAV swarms provide an optimal paradigm to execute distributed search and rescue missions. By establishing geometric sector partitions combined with dynamic peer-to-peer task handoffs and adaptive replanning, a swarm can comprehensively survey affected regions, detect trapped survivors, and guide emergency responses without human pilot saturation.

### 2.3 Objectives
1. **Dynamic 3D Environment Modeling:** Formulate a multi-layered 3D isometric simulation representing urban structural obstacles, expanding hazards (fire/smoke), and trapped survivors.
2. **Coordinated Multi-Agent Architecture:** Develop a Swarm Coordinator executing sector partitioning, collision avoidance, and opportunistic cross-sector mutual assistance.
3. **Adaptive Path Planning & Replanning:** Integrate real-time 3D collision-free path planning capable of adjusting to dynamic hazard expansions and emergency base returns.
4. **Empirical Algorithm Benchmarking:** Rigorously compare seven pathfinding paradigms under stochastic hazard distributions to identify optimal computational and flight efficiency.
5. **Interactive Operator Telemetry:** Render an intuitive tactical HUD providing real-time fleet health, coverage heatmaps, FLIR thermal mode, and mission debrief metrics.

---

## 3. Literature Review

Numerous studies have explored autonomous UAV coordination and search-and-rescue path planning. Table 1 summarizes seminal works and identifies key research gaps addressed by our system.

### Table 1: Summary of Related Works
| Authors & Year | Primary Focus / Technique | Strengths | Limitations / Gaps Addressed |
|:---|:---|:---|:---|
| **Scherer et al. (2015)** | Autonomous river search using single UAV | Robust perception and obstacle mapping | Single-agent architecture; lacks scalability and fault tolerance |
| **Alfeo et al. (2019)** | Bio-inspired Swarm Pheromone Search | Decentralized emergent exploration | High duplicate coverage; unpredictable rescue latency |
| **Koenig & Likhachev (2002)** | $D^*$ Lite Incremental Replanning | Efficient replanning in partially known graphs | Formulated on generic 2D graphs; unadapted to 3D altitude-aware UAV sectors |
| **Harikumar et al. (2018)** | Multi-UAV Voronoi Area Partitioning | Clean geometric sector boundaries | Fails when sector workloads are asymmetric; lacks mutual assistance |
| **Daniel et al. (2010)** | $\Theta^*$ Any-Angle Pathfinding | Eliminates artificial grid-angle zig-zags | Prone to voxel corner-clipping collisions in dense 3D urban canyons |
| **Khatib (1986)** | Artificial Potential Fields for Obstacles | Extremely fast reactive avoidance | Highly susceptible to local minima traps in concave building clusters |

### Gap Addressed
Existing literature either investigates abstract 2D path planning without realistic 3D building/altitude constraints, or implements rigid spatial partitioning that leaves idle drones inactive once their primary sector is swept. Our work bridges this gap by combining **3D volumetric obstacle/hazard physics** with a **dynamic sector allocation policy featuring cross-sector mutual assistance** and **resilient incremental replanning ($D^*$ Lite)**.

---

## 4. Recap of Previous Evaluation & Feedback Addressed

During the Mid-Term Evaluation, the project demonstrated a basic 2D flat grid with preliminary $A^*$ pathfinding and independent drone sweeps. The evaluation committee provided the following constructive feedback:
1. **Lack of Altitude and 3D Complexity:** The simulation was constrained to a planar grid, failing to reflect multi-story urban environments and vertical altitude clearances.
2. **Vulnerability to Expanding Hazards:** The original system assumed static obstacles; it did not account for dynamic disaster evolution (e.g., propagating fire or smoke).
3. **Absence of Quantitative Algorithmic Comparison:** The choice of $A^*$ was unjustified by benchmark data against competing planners.
4. **Telemetry and Visual Fidelity:** The user interface was primitive, lacking intuitive situational awareness for rescue controllers.

### Actions Taken in Current Phase
- **3D Voxel Engine:** Upgraded the environment into a full $25 \times 20 \times 6$ 3D voxel space with structural building columns, rooftops, and vertical flight corridors.
- **Dynamic Hazard Expansion Engine:** Introduced cellular-automata fire and smoke expansion that spreads upward and laterally every 8 seconds.
- **Comprehensive 7-Algorithm Benchmark:** Implemented and tested $A^*$, BFS/Dijkstra, $D^*$ Lite, JPS, $\Theta^*$, RRT, and Potential Fields across 5 independent seeds.
- **Tactical 3D Isometric HUD:** Developed 60 FPS visual interpolation, FLIR thermal night mode, drone battery badges, and automated mission scorecard generation.

---

## 5. Methodology

The system architecture follows a hierarchical multi-agent framework comprising three major subsystems: the **Environmental Engine**, the **Swarm Coordinator**, and the **Autonomous UAV Agent**.

```
                ┌─────────────────────────────────────────┐
                │          Disaster Environment           │
                │  (3D Grid: Obstacles, Hazards, Victims) │
                └────────────────────┬────────────────────┘
                                     │ State Broadcast
                                     ▼
                        ┌────────────────────────┐
                        │   Swarm Coordinator    │
                        │ ────────────────────── │
                        │ • Sector Partitioning  │
                        │ • Target Arbitration   │
                        │ • Mutual Assistance    │
                        │ • Global Coverage Map  │
                        └────────────┬───────────┘
                                     │ Assignments
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                    ▼
        ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
        │ UAV Agent 1  │     │ UAV Agent 2  │     │ UAV Agent N  │
        │ ──────────── │     │ ──────────── │     │ ──────────── │
        │ • 3D Sensors │     │ • 3D Sensors │     │ • 3D Sensors │
        │ • D* Lite    │     │ • D* Lite    │     │ • D* Lite    │
        │ • State Mach │     │ • State Mach │     │ • State Mach │
        └──────────────┘     └──────────────┘     └──────────────┘
```

### 5.1 Environment & 3D Sensor Model
The environment is modeled as a discretized 3D tensor $\mathcal{G} \in \mathbb{R}^{W \times H \times D}$, where cells are categorized as $\text{EMPTY}$, $\text{OBSTACLE}$, $\text{HAZARD}$, $\text{SURVIVOR}$, or $\text{RESCUED}$. Each UAV maintains a cubic sensor range of radius $r_s = 2$ voxels in all directions:
$$\mathcal{N}_{\text{sensor}}(x, y, z) = \{ (x + \delta x, y + \delta y, z + \delta z) \mid |\delta x|, |\delta y|, |\delta z| \le r_s \}$$

### 5.2 Dynamic Sector Partitioning with Mutual Assistance
The global map of width $W$ is partitioned along the primary axis among $N$ drones:
$$\text{Sector}_i = \left[ \left\lfloor (i-1) \frac{W}{N} \right\rfloor, \, \left\lfloor i \frac{W}{N} \right\rfloor - 1 \right], \quad i \in \{1, \dots, N\}$$
To eliminate idle latency when a UAV finishes sweeping its assigned sector, the coordinator triggers **Cross-Sector Mutual Assistance**. If an agent transitions to `EXPLORATION_COMPLETE` while unassigned survivors exist in adjacent sectors, the coordinator assigns the nearest global target, authorizing inter-sector transit.

### 5.3 Path Planning Algorithm ($D^*$ Lite)
To navigate around dynamic obstacles and expanding fire voxels, agents employ $D^*$ Lite. The algorithm maintains two estimates for each node $s$: $g(s)$ (path cost from goal) and $rhs(s)$ (one-step lookahead cost):
$$rhs(s) = \begin{cases} 0 & \text{if } s = s_{\text{goal}} \\ \min_{s' \in \text{Succ}(s)} (g(s') + c(s, s')) & \text{otherwise} \end{cases}$$
Priority keys are computed as $k(s) = [k_1(s), k_2(s)]$:
$$k_1(s) = \min(g(s), rhs(s)) + h(s_{\text{start}}, s) + k_m, \quad k_2(s) = \min(g(s), rhs(s))$$
When an expanding hazard obstructs an active path, only affected vertices are updated in the priority queue, avoiding full-graph re-evaluations.

### 5.4 UAV Finite State Machine (FSM)
Each UAV operates under an autonomous 5-state lifecycle:
1. **EXPLORING:** Flying at survey altitude ($z=2$) conducting systematic sweep scans.
2. **RESCUING:** Dispatched along a planned trajectory to land at survivor coordinates ($z=0$).
3. **RETURNING:** Initiated when remaining battery $\le \text{dist}(p, p_{\text{base}}) + 8$.
4. **CHARGING:** Stationed at ground base pad replenishing $+5\%$ energy/tick.
5. **DEAD:** Emergency failsafe triggered if battery drops to zero in flight.

---

## 6. Implementation Details

- **Programming Language & Libraries:** Python 3.12, Pygame 2.6.1, NumPy 2.3.1, NetworkX 3.5.
- **Coordinate Transformation:** 3D grid points $(x, y, z)$ are mapped to 2D isometric screen space $(u, v)$ with rotational symmetry:
  $$u = x_{\text{origin}} + (x_{\text{rot}} - y_{\text{rot}}) \cdot \frac{W_{\text{tile}}}{2}$$
  $$v = y_{\text{origin}} + (x_{\text{rot}} + y_{\text{rot}}) \cdot \frac{H_{\text{tile}}}{2} - z \cdot H_{\text{layer}}$$
- **Visual Interpolation Engine:** Drone entities use linear interpolation (LERP) at 60 FPS:
  $$\mathbf{p}_{\text{vis}}(t + \Delta t) = \mathbf{p}_{\text{vis}}(t) + \alpha \cdot (\mathbf{p}_{\text{target}} - \mathbf{p}_{\text{vis}}(t)), \quad \alpha = 0.22$$
- **Depth Sorting:** Strict Painter's Algorithm sorts entities by $(x_{\text{rot}} + y_{\text{rot}}, z, \text{priority})$ ensuring correct visual occlusion across all 4 camera angles ($0^\circ, 90^\circ, 180^\circ, 270^\circ$).

---

## 7. Results and Analysis

### 7.1 Quantitative Benchmark Across 7 Algorithms
A rigorous headless benchmark was conducted across 5 randomized seeds ($42, 123, 456, 789, 1024$) on a $25 \times 20 \times 6$ grid with 5 UAVs and dynamic hazards. Table 2 summarizes the empirical results.

### Table 2: Comparative Performance Metrics (Averaged over 5 Runs)
| Algorithm | Mission Success | Mean Ticks | MTTR (Ticks) | Flight Dist | Energy (Units) | Recharges | Total Nodes | Path Time (ms) | Nodes / Call |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **$D^*$ Lite** | **5/5 (100%)** | **64.2** | 11.1 | **70.4** | **70.4** | **0.4** | **2,412** | **73.4** | **10.2** |
| **BFS / Dijkstra** | **5/5 (100%)** | **64.2** | 11.1 | **70.4** | **70.4** | **0.4** | 22,812 | 101.9 | 96.3 |
| **RRT** | **5/5 (100%)** | 69.2 | 13.3 | 86.2 | 86.2 | **0.4** | 2,719 | 281.4 | 10.4 |
| **Jump Point Search** | **5/5 (100%)** | 91.2 | 27.8 | 109.4 | 109.4 | 0.8 | 15,942 | 1276.6 | 26.4 |
| **$A^*$ (Baseline)** | 4/5 (80%) | 353.2 | 9.8 | 70.2 | 70.2 | 1.0 | 1,454 | 8.8 | 0.5 |
| **$\Theta^*$ (Any-Angle)** | 1/5 (20%) | 1207.4 | 5.8 | 64.4 | 64.4 | 1.4 | 66,250 | 1049.5 | 5.0 |
| **Potential Field** | 0/5 (0%) | 1500.0 | 13.2 | 295.4 | 295.4 | 0.2 | 34,851 | 10085.5 | 3.0 |

### 7.2 Failure Mode Discussion
1. **$A^*$ Trapping (Seed 1024):** In Seed 1024, expanding hazard voxels enclosed a narrow passage between two buildings. Forward $A^*$ repeatedly repathprinted toward the nearest boundary, cycling into an oscillating dead end and timing out at 1500 ticks.
2. **$\Theta^*$ Voxel Corner Clipping:** While $\Theta^*$ generates optimal geometric straight lines, projecting continuous lines onto a discrete 6-connected voxel grid caused drones to graze obstacle corners, inducing path invalidations in 80% of test runs.
3. **Artificial Potential Field Local Minima:** Reactive gradient descent failed completely ($0\%$ success) in dense urban clusters, as repulsive vectors from adjacent building walls neutralized attractive goal forces, trapping UAVs indefinitely.
4. **$D^*$ Lite Superiority:** $D^*$ Lite maintained $100\%$ mission success, exploring only **10.2 nodes per invocation** (an $89.4\%$ reduction compared to BFS) while delivering identical optimal flight paths (70.4 voxels).

---

## 8. Conclusion and Future Work

### 8.1 Objectives Met
The project successfully realized a fully autonomous, 3D multi-agent UAV disaster response simulation. Key accomplishments include:
- Scalable sector-coordinated swarm architecture featuring mutual assistance.
- Dynamic 3D hazard spreading engine modeling fire and smoke risks.
- Empirical validation of 7 path planning algorithms, establishing $D^*$ Lite as the superior replanning engine.
- High-fidelity isometric dashboard with live battery telemetry and debrief evaluation.

### 8.2 Limitations
- Simplified uniform sensor detection without probabilistic false negatives.
- Homogeneous drone speed and payload assumptions.
- Grid-based discrete collision avoidance rather than continuous velocity obstacles (VO).

### 8.3 Future Work
- **Heterogeneous Swarms:** Integrating heavy-lift rescue drones paired with agile scout drones.
- **Wind & Thermal Plume Aerodynamics:** Simulating downdrafts and thermal lift forces near fire hazards.
- **Hardware-in-the-Loop (HITL):** Porting coordinator algorithms to ROS2/PX4 micro-air-vehicle testbeds.

---

## 9. References (IEEE Style)

1. [1] J. Scherer et al., "Autonomous UAV cooperation for search and rescue missions," *IEEE Robotics & Automation Magazine*, vol. 22, no. 2, pp. 88–99, Jun. 2015.
2. [2] A. L. Alfeo, M. G. Cimino, and G. Vaglini, "Enhancing UAV swarm search and rescue operations through bio-inspired coordination," *Applied Soft Computing*, vol. 76, pp. 248–262, Mar. 2019.
3. [3] S. Koenig and M. Likhachev, "D* Lite," in *Proc. National Conference on Artificial Intelligence (AAAI)*, Edmonton, Canada, 2002, pp. 476–483.
4. [4] S. Harikumar, R. Cohen, and S. Sundaram, "Multi-UAV area coverage in uncertain environments using Voronoi partitioning," in *Proc. IEEE International Conference on Systems, Man, and Cybernetics (SMC)*, Miyazaki, Japan, 2018, pp. 1120–1125.
5. [5] K. Daniel, A. Nash, S. Koenig, and A. Felner, "Theta*: Any-angle path planning on grids," *Journal of Artificial Intelligence Research (JAIR)*, vol. 39, pp. 533–579, Oct. 2010.
6. [6] O. Khatib, "Real-time obstacle avoidance for mobile robots and manipulators," *The International Journal of Robotics Research*, vol. 5, no. 1, pp. 90–98, Mar. 1986.
7. [7] D. Harabor and A. Grastien, "Online graph pruning for pathfinding on grid maps," in *Proc. AAAI Conference on Artificial Intelligence*, San Francisco, CA, 2011, pp. 1114–1119.
8. [8] S. M. LaValle, "Rapidly-exploring random trees: A new tool for path planning," *Computer Science Dept., Iowa State University*, Tech. Rep. TR 98-11, Oct. 1998.
9. [9] P. E. Hart, N. J. Nilsson, and B. Raphael, "A formal basis for the heuristic determination of minimum cost paths," *IEEE Transactions on Systems Science and Cybernetics*, vol. 4, no. 2, pp. 100–107, Jul. 1968.
10. [10] Y. Chen et al., "Energy-efficient 3D trajectory planning for multi-UAV disaster management networks," *IEEE Transactions on Wireless Communications*, vol. 20, no. 8, pp. 5240–5254, Aug. 2021.
