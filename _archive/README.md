# HiMCM2025 Repository - Archive Folder

This folder contains archived files that are not essential for the core modeling implementation.

## Contents

### Markdown Documentation Files
- All development notes and documentation (*.md files)
- Status updates and implementation guides
- Analysis documents and change logs

### Benchmark JSON Data Files
- Historical benchmark results and sweep analysis data
- Fire-weight optimization data
- Sweep algorithm testing results

### Test and Debug Scripts
- Test files (test_*.py)
- Debug scripts (debug_*.py)
- Analysis helper scripts
- Analyzer scripts

### Analysis Outputs
- Benchmarking graphs and visualization data
- Performance comparison charts
- Fire-weight sweep results

## Core Repository Structure

The main repository contains only the essential modeling and visualization code:

**Core Simulation:**
- `simulator.py` - Fire spread, smoke, and occupant evacuation physics
- `optimal_rescue_model.py` - Optimal rescue algorithm implementation
- `optimal_rescue_optimizer.py` - LP solver optimization wrapper
- `sweep_coordinator.py` - K-medoids sweep phase partitioning
- `sweep_fire_weight.py` - Fire-weight tuning utilities
- `visualizer.py` - Real-time evacuation visualization
- `graph_maker.py` - Floor plan graph creation tool

**Configuration:**
- `config_example.json` - Example building configuration

**Directories:**
- `graph_maker/` - Graph creation UI tools
- `benchmark_overnight/` - Current benchmark results
- `benchmark_overnight_childcare/` - Childcare benchmark results
- `benchmark_responders/` - Firefighter sensitivity benchmark (1-6 FF)
- `benchmark_responders_extended/` - Firefighter sensitivity benchmark (7-10 FF)

## For Publication

To maintain a clean repository for publication, only the core modeling files are recommended:
- All `*.py` simulation and visualization files
- `graph_maker/` directory
- Configuration examples
- Benchmark results directories
- .git history

Archive this folder separately for reference.
