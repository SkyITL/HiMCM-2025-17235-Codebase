# Critical Fixes - Replanning Bug

## Issue 1: Replanning Never Triggered

### Root Cause
The `_detect_graph_changes()` method in `optimal_rescue_model.py:370-393` was checking `len(graph['edges'])`, which doesn't change when edges burn.

**Why it failed:**
- When hallways burn, `edge.exists` is set to `False`
- But edges remain in the `graph['edges']` dictionary
- So `len(graph['edges'])` stays constant at 70
- Replanning never triggered, even though edges were burning

### The Fix
Changed line 382 in `optimal_rescue_model.py`:

**Before:**
```python
current_edge_count = len(graph['edges'])
```

**After:**
```python
current_edge_count = sum(1 for e in graph['edges'].values() if e.get('exists', True))
```

### Verification
Tested with seed=42:
```
Phase transitioned at tick 33
⚠️  REPLANNING #1 - Graph changed (edges burned)
   Replanning complete. No people affected
REPLANNING TRIGGERED at tick 91!
⚠️  REPLANNING #2 - Graph changed (edges burned)
⚠️  REPLANNING #3 - Graph changed (edges burned)
Total replans: 3
```

✓ Replanning now works correctly!

## Issue 2: Missing Last Rescue Tick Metric

### Added Tracking
Modified `benchmark_mall_fast.py` to track when the last person was rescued vs total evacuation time.

**Changes:**
- Added `last_rescue_tick` and `last_rescued_count` tracking
- Updated return dictionary to include `last_rescue_tick`
- Added `avg_last_rescue_tick` to summary statistics

**Use case:**
- Identify "wasted time" after last person rescued
- Distinguish timeout trials (hit 3000 ticks) from completed evacuations
- Better understand evacuation efficiency

## Benchmark Results Summary

### Fire-Weight Tuning (100 trials each)

| Fire Weight | Survival | Std Dev | Timeout Rate |
|-------------|----------|---------|--------------|
| 0.0 (Baseline) | 97.78% | 4.23% | 29.0% |
| 1.0 (Moderate) | 97.77% | 4.69% | 21.0% |
| 2.0 (Strong) | 97.09% | 6.29% | 27.0% |
| **5.0 (Best)** | **98.41%** | **2.66%** | **18.0%** |

### Key Findings

1. **Fire-weight=5.0 performs best**
   - Highest survival rate: 98.41% (±2.66%)
   - Lowest timeout rate: 18% (vs 29% baseline)
   - Most consistent (lowest std dev)
   - +0.63% improvement over baseline

2. **18-29% trials hit timeout (3000 ticks)**
   - Timeout = >10 minutes simulated time
   - Represents failed evacuations
   - Higher fire-weight reduces timeout rate

3. **Replanning was not triggered in old benchmarks**
   - All 400 trials showed 0 replans
   - This is because they were run before the fix
   - **Need to re-run benchmarks with fixed replanning**

## Next Steps

### 1. Re-run Benchmarks with Replanning Fix
Since the old benchmarks didn't have working replanning, we need fresh results:

```bash
# Run with fixed replanning + last_rescue_tick metric
python3 benchmark_mall_fast.py --trials 500 --fire-weight 0.0 --output fixed_fw0.0.json
python3 benchmark_mall_fast.py --trials 500 --fire-weight 5.0 --output fixed_fw5.0.json
```

### 2. Compare Results
Expected improvements with working replanning:
- Lower timeout rate (adaptive to burned edges)
- Better survival rates (routes around fire damage)
- Higher replan counts (confirms it's working)

### 3. Analyze Last Rescue Tick
With the new metric, we can:
- Identify wasted time after last rescue
- Optimize phase transition logic
- Better understand timeout trials

## Files Modified

1. **optimal_rescue_model.py:382** - Fixed edge count detection for replanning
2. **benchmark_mall_fast.py:90-135** - Added last_rescue_tick tracking
3. **analyze_fire_weight.py:32-33** - Fixed fire_weight extraction
4. **analyze_detailed.py** - New comprehensive analysis script

## Impact

**Before fix:**
- Replanning never triggered (0% of trials)
- Firefighters executed stale routes through burned hallways
- Higher timeout rates due to blocked paths

**After fix:**
- Replanning triggers when edges burn
- Adaptive routing around fire damage
- Expected: Lower timeout rates, better survival

**Old benchmarks are invalid** - they didn't have working replanning, so results don't reflect the system's true capabilities.
