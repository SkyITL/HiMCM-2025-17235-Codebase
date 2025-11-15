# Benchmark Summary - Updated Settings

## Critical Fixes Applied

### 1. Replanning Bug Fix
**Issue**: Replanning was never triggered because `_detect_graph_changes()` checked `len(graph['edges'])` which doesn't change when edges burn.

**Fix** (optimal_rescue_model.py:382):
```python
# OLD (broken):
current_edge_count = len(graph['edges'])

# NEW (fixed):
current_edge_count = sum(1 for e in graph['edges'].values() if e.get('exists', True))
```

**Verification**: Tested with seed=42, replanning now triggers correctly:
- Replanning #1 at tick 91
- Replanning #2 and #3 follow as more edges burn
- ✓ Working correctly!

### 2. Last Rescue Tick Metric
Added tracking for when the last person was rescued (vs total evacuation time).

**Purpose**:
- Distinguish timeout trials from completed evacuations
- Identify "wasted time" after last rescue
- Better understand evacuation efficiency

## New Benchmark Parameters

### Configuration
- **Firefighters**: 2 (changed from 6)
- **Max ticks**: 3000 (~10 minutes simulated time)
- **Trials**: 100 per fire-weight value
- **Fire-weight values**: 0.0, 1.0, 2.0, 5.0

### Output Files
```
fixed_fw0.0_2ff.json   # Baseline (no fire priority)
fixed_fw1.0_2ff.json   # Moderate fire priority
fixed_fw2.0_2ff.json   # Strong fire priority
fixed_fw5.0_2ff.json   # Very strong fire priority
```

## Previous Results (INVALID - No Replanning)

The old benchmarks (sweep_*.json) are **invalid** because:
1. Replanning was broken (0 replans across all 400 trials)
2. Firefighters executed stale routes through burned hallways
3. Results don't reflect the system's true capabilities

### Old Results Summary (6 firefighters, broken replanning)

| Fire Weight | Survival | Timeout Rate |
|-------------|----------|--------------|
| 0.0         | 97.78%   | 29.0%        |
| 1.0         | 97.77%   | 21.0%        |
| 2.0         | 97.09%   | 27.0%        |
| 5.0         | 98.41%   | 18.0%        |

**Note**: These results had 0 replans, making them unreliable.

## Expected Improvements with Fixes

With working replanning (2 firefighters, max_ticks=3000):

1. **Adaptive routing**: Firefighters reroute around burned edges
2. **Lower timeout rate**: Better path planning avoids dead ends
3. **Replanning counts > 0**: Confirms system is working
4. **More realistic**: Reflects how firefighters would actually respond

## Analysis Commands

Once benchmarks complete:

```bash
# Update analyze_detailed.py to use new filenames
# Then run:
python3 analyze_detailed.py

# Or check individual results:
jq '.summary' fixed_fw0.0_2ff.json
jq '.summary' fixed_fw5.0_2ff.json
```

## Next Steps

1. **Wait for benchmarks to complete** (~running now)
2. **Analyze results** with updated analysis script
3. **Compare to old results** (6ff vs 2ff, with vs without replanning)
4. **Identify optimal fire-weight** for 2-firefighter scenario
5. **Document findings** for HiMCM paper

## Files Modified

1. **benchmark_mall_fast.py**:
   - max_ticks: 500 → 3000
   - default firefighters: 6 → 2
   - Added last_rescue_tick tracking

2. **optimal_rescue_model.py**:
   - Fixed edge count detection (line 382)
   - Replanning now triggers correctly

3. **analyze_detailed.py**:
   - Updated timeout thresholds (500 → 3000)
   - Fixed fire_weight extraction from config

4. **analyze_fire_weight.py**:
   - Fixed fire_weight extraction from config

## Running Benchmarks

Current status: **In progress**

Started 4 parallel benchmarks:
- fw=0.0 (baseline)
- fw=1.0 (moderate)
- fw=2.0 (strong)
- fw=5.0 (very strong)

Each with 2 firefighters, 100 trials, max_ticks=3000.
