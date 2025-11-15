# Benchmark Status

## Current Runs

### Sweep Coordinator Benchmarks (100 trials each)

**Fire-weight parameter tuning** - Testing different priority weights for proximity to fire origin:

1. **fire_weight = 0.0** (Baseline - no fire priority)
   - Status: Running
   - File: `sweep_benchmark_100.json`

2. **fire_weight = 1.0** (Moderate fire priority)
   - Status: Running
   - File: `sweep_fw1.0.json`

3. **fire_weight = 2.0** (Strong fire priority)
   - Status: Running
   - File: `sweep_fw2.0.json`

4. **fire_weight = 5.0** (Very strong fire priority)
   - Status: Running
   - File: `sweep_fw5.0.json`

## Fire-Weight Implementation

The fire-weight parameter controls how much priority is given to rescuing people closer to the fire origin:

```python
# Formula in pathfinding.py:344-347
proximity_boost = 1.0 + (fire_priority_weight / (1.0 + fire_dist))

# At fire origin (dist=0):  boost = 1 + weight
# At distance=1:            boost = 1 + weight/2
# At distance=∞:            boost = 1
```

**Effect**:
- **Higher weight** = Prioritize rooms closer to fire (rescue them first before fire spreads)
- **Lower weight (0.0)** = No fire proximity consideration (pure time efficiency)

## Expected Results

### Hypothesis
Fire-weight tuning should improve survival rates by:
1. Rescuing people closer to fire before they're cut off by flames
2. Preventing firefighters from wasting time on far rooms while near rooms burn
3. Optimizing the trade-off between shortest-path efficiency and fire urgency

### Metrics to Compare
- **Average survival rate** (primary metric)
- **Standard deviation** (consistency)
- **Average rescued** (total people saved)
- **Average dead** (fire casualties)

## Analysis Commands

Once benchmarks complete, run:

```bash
# Analyze all fire-weight results
python3 analyze_fire_weight.py

# View individual results
jq '.summary' sweep_benchmark_100.json
jq '.summary' sweep_fw1.0.json
jq '.summary' sweep_fw2.0.json
jq '.summary' sweep_fw5.0.json
```

## Sweep Coordinator Performance

The integrated MST-based sweep strategy:

- ✓ K-medoids partitioning (corridor distance)
- ✓ Complete graph construction (all-pairs shortest paths)
- ✓ MST using Prim's algorithm
- ✓ DFS 2× traversal generation
- ✓ Dynamic replanning when edges burn
- ✓ Stall detection for trapped rooms
- ✓ Oppor tunistic capable instruction during sweep

**Test results** (seeds 42, 99):
- Sweep phase: 31-35 ticks
- Phase transition: Successful
- Survival rates: 93-100%
- All rooms discovered: Yes

## Next Steps

After benchmarks complete:

1. **Identify optimal fire-weight** from results
2. **Run larger benchmark** (500-1000 trials) with optimal setting
3. **Compare to baseline** (old greedy BFS exploration)
4. **Document improvements** in survival rate
5. **Tune other parameters** if needed (under-capacity penalty, etc.)
