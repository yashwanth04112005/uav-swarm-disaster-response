# 🎬 Project Presentation Script & Slide Outline (8–10 Minutes)

**Project Title:** 3D Sector-Coordinated Autonomous UAV Swarm for Urban Disaster Search and Rescue  
**Duration:** 8:30 to 9:30 minutes (Targeting the 8–10 minute requirement)  
**Video Setup:** Screen recording with web camera feed active in top-right or bottom-right corner throughout.

---

## Slide Breakdown & Timing Guide

| Slide # | Slide Title | Duration | Cumulative Time | Key Visual Content |
|:---:|:---|:---:|:---:|:---|
| **1** | Title & Project Overview | 0:45 | 0:45 | Title, Student Names, Roll Nos, Mentor, IIITS logo |
| **2** | Problem Statement & Motivation | 1:00 | 1:45 | Urban disaster imagery, single-UAV bottlenecks vs swarm benefits |
| **3** | Recap of Mid-Term Evaluation & Feedback | 0:45 | 2:30 | Feedback items vs actions taken (2D $\to$ 3D, Dynamic Hazards) |
| **4** | System Architecture & Swarm Coordination | 1:15 | 3:45 | Block diagram, sector partitioning, mutual assistance flow |
| **5** | Dynamic 3D Environment & Hazard Expansion | 1:00 | 4:45 | Isometric map render, building voxels, fire/smoke expansion |
| **6** | Pathfinding Algorithms Evaluated | 1:00 | 5:45 | Comparison list (A*, BFS, D* Lite, JPS, Theta*, RRT, Potential Field) |
| **7** | Live Simulation Demonstration | 1:45 | 7:30 | Video / screen capture of simulation running, FLIR mode, rescues |
| **8** | Results, Analysis & Algorithm Benchmark | 1:15 | 8:45 | Benchmark table, why D* Lite won, failure mode analysis |
| **9** | Conclusion, Limitations & Future Scope | 0:45 | 9:30 | Objectives achieved, ROS2/hardware next steps, Q&A / Thank you |

---

## Detailed Spoken Script (Word-for-Word Guide)

### ⏱️ 0:00 – 0:45 | Slide 1: Title & Overview
> *"Good morning/afternoon, respected mentors and evaluators. I am [Your Name], along with [Partner Name, if group project], presenting our Semester 7 Additional Project titled: **3D Sector-Coordinated Autonomous UAV Swarm for Urban Disaster Search and Rescue**, carried out under the guidance of [Mentor Name] at IIIT Sri City.*  
> *In today's 9-minute presentation, we will walk you through the problem motivation, our multi-agent architecture, the live 3D isometric simulation, a rigorous benchmark of seven pathfinding algorithms, and our final empirical results."*

---

### ⏱️ 0:45 – 1:45 | Slide 2: Problem Statement & Motivation
> *"In the aftermath of major disasters—such as earthquakes, building collapses, and industrial fires—ground-level search and rescue teams face extreme hazards: unstable rubble, toxic gas plumes, and active fires. Unmanned Aerial Vehicles provide invaluable overhead vision. However, deploying a single drone is insufficient due to limited battery life and sensor coverage.*  
> *Conversely, deploying multiple uncoordinated drones causes redundant sweeps, mid-air collision risks, and uncoordinated rescues. Our objective was to develop an autonomous multi-UAV swarm system operating in a realistic 3D volumetric space that can systematically partition search sectors, coordinate victim handoffs, and dynamically replan around expanding hazards in real time."*

---

### ⏱️ 1:45 – 2:30 | Slide 3: Recap of Previous Evaluation & Feedback
> *"During our Mid-Term evaluation, the committee recommended three pivotal improvements:*  
> *First, move beyond a planar 2D grid to a true 3D altitude-aware environment with vertical obstacles and multi-level flyovers.*  
> *Second, introduce dynamic hazards rather than static obstacles, simulating propagating fire and smoke.*  
> *Third, empirically justify our choice of pathfinding algorithm rather than assuming A-Star is optimal.*  
> *In this final phase, we have fully addressed all three recommendations: our system now features a full 3D voxel engine, cellular hazard expansion, and a comprehensive benchmark of seven distinct pathfinding paradigms."*

---

### ⏱️ 2:30 – 3:45 | Slide 4: System Architecture & Coordination
> *"Here is our high-level architecture. At the top level, the **Swarm Coordinator** partitions the disaster grid into non-overlapping geometric sectors along the primary axis, assigning one UAV per sector.*  
> *Each UAV agent operates an autonomous five-state finite state machine: Exploring at search altitude, Rescuing upon survivor detection, Returning when battery reaches the critical distance threshold, Charging at ground launchpads, and Dead if drained.*  
> *A key contribution is our **Cross-Sector Mutual Assistance** protocol: once a drone completes sweeping its assigned sector, instead of idling at base, it queries the coordinator for unassigned survivors across adjacent sectors and transits to assist its peers, dramatically reducing the swarm's Mean Time to Rescue."*

---

### ⏱️ 3:45 – 4:45 | Slide 5: Dynamic 3D Environment & Hazard Engine
> *"Our simulation models an urban disaster area across a 25 by 20 grid with 6 vertical altitude levels.*  
> *Structural buildings are modeled as vertical voxel columns with realistic rooftops, helipads, and antennas. Trapped survivors emit pulsing SOS distress beacons on the ground level.*  
> *Furthermore, every 8 seconds, the hazard engine propagates fire and smoke voxels upward and laterally using a 3D cellular automata model. This means flight corridors that were safe when a mission started can suddenly become blocked, requiring real-time replanning."*

---

### ⏱️ 4:45 – 5:45 | Slide 6: Pathfinding Algorithms Evaluated
> *"To determine the most resilient planner for expanding hazards, we implemented seven distinct algorithms:*  
> *1. Standard 3D A-Star with Manhattan heuristic.*  
> *2. Uniform-cost BFS / Dijkstra.*  
> *3. D-Star Lite for incremental backward replanning.*  
> *4. 3D Jump Point Search (JPS) for symmetric pruning.*  
> *5. Theta-Star for any-angle line-of-sight shortcuts.*  
> *6. RRT (Rapidly-exploring Random Tree) for stochastic exploration.*  
> *7. Artificial Potential Fields for reactive gradient descent.*  
> *All algorithms were evaluated on identical seeds to test collision safety, node expansion efficiency, and computational latency."*

---

### ⏱️ 5:45 – 7:30 | Slide 7: Live Simulation Demonstration
*(Show live Pygame screen capture or switch to the running application)*  
> *"Let us examine the system in action.*  
> *Here in the main 3D isometric view, you can see 5 UAVs executing smooth 60-FPS visual interpolation. Each drone features procedural quadcopter geometry, spinning rotors, and status-colored navigation LEDs.*  
> *On the right, our tactical HUD displays live telemetry: individual UAV battery percentages, coverage progress, and survivor counts.*  
> *By pressing [T], the operator can toggle our FLIR Thermal Night-Vision mode, highlighting victim body heat signatures and drone searchlight cones.*  
> *Notice when UAV 3 finishes its sector, the coordinator triggers cross-sector mutual assistance, dispatching it to assist UAV 4 in sector 4. Upon mission completion, an automated Mission Debrief scorecard grades fleet coordination efficiency."*

---

### ⏱️ 7:30 – 8:45 | Slide 8: Benchmark Results & Analysis
> *"Moving to our empirical results: across 5 randomized seeds, **D-Star Lite emerged as the clear winner**:*  
> *- It achieved a **100% mission success rate**, clearing all survivors in an average of just 64.2 ticks with optimal flight distance.*  
> *- Most importantly, D-Star Lite explored only **10.2 nodes per path call**, representing an **89.4% reduction in explored nodes** compared to uniform-cost BFS.*  
> *- While original A-Star achieved an 80% success rate, it timed out on Seed 1024 due to an oscillation trap caused by expanding fire. D-Star Lite resolved this seamlessly.*  
> *- Theta-Star struggled with voxel corner-clipping collisions (20% success), and Potential Fields suffered classic local minima traps (0% success).*  
> *Consequently, we integrated D-Star Lite as the default planning engine across the entire codebase."*

---

### ⏱️ 8:45 – 9:30 | Slide 9: Conclusion & Future Scope
> *"In conclusion, we have delivered a robust, 3D multi-agent UAV swarm simulation that integrates sector partitioning, dynamic mutual assistance, and D-Star Lite replanning to conquer urban disaster challenges.*  
> *In the future, we plan to extend this system to heterogeneous swarms with varied drone payloads, model wind and thermal updraft physics, and deploy the coordinator logic onto real PX4 micro-air-vehicles using ROS2.*  
> *Thank you for your time, and we welcome your questions."*

---

## 📌 Video Recording Checklist
- [ ] Camera positioned so your face is clearly visible (top-right or bottom-right corner).
- [ ] Presentation slides open in full-screen presentation mode.
- [ ] Simulation demo video / window queued up and ready for Slide 7.
- [ ] Total recorded video duration checked: must be between **8:00 and 10:00 minutes**.
- [ ] Audio clear, no background hum.
- [ ] Google Drive link permissions verified: set to **"Anyone with the link can view"** and tested in an Incognito / Private window.
