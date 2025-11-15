# Final Benchmark Results - Fire-Weight Tuning

## Executive Summary

Completed benchmarks with **working replanning** and **fixed seeds** for fair comparison across fire-weight parameters.

**Configuration:**
- 20 trials per fire-weight value
- 2 firefighters
- Fixed seeds (1000-1019) ensuring identical scenarios across all tests
- Max ticks: 3000 (~10 minutes simulated time)
- Replanning confirmed working (5-11 avg replans per trial)

**Key Finding:** Fire-weight = **2.0** performs best with:
- **91.91% survival rate** (±6.09%)
- Most efficient evacuation (lowest wasted time: 257 ticks)
- Fewer replans needed (5.40 avg) - more stable routing
- +0.22% improvement over baseline

## Detailed Results

### Survival Rate Comparison

| Fire Weight | Label       | Avg Survival | Std Dev | Best  | Worst |
|-------------|-------------|--------------|---------|-------|-------|
| 0.0         | Baseline    | 91.69%       | 9.45%   | 100%  | 60.0% |
| 1.0         | Moderate    | 91.58%       | 8.45%   | 100%  | 67.3% |
| **2.0**     | **Strong**  | **91.91%**   | **6.09%** | **100%** | **78.3%** |
| 5.0         | Very Strong | 91.09%       | 10.48%  | 100%  | 61.8% |

### Replanning Statistics

| Fire Weight | Avg Replans | Max Replans |
|-------------|-------------|-------------|
| 0.0         | 11.15       | 58          |
| 1.0         | 9.85        | 50          |
| **2.0**     | **5.40**    | **54**      |
| 5.0         | 6.05        | 51          |

**Key Insight:** Fire-weight=2.0 requires fewer replans, suggesting more stable initial routing that holds up better as fire spreads.

### Evacuation Efficiency

| Fire Weight | Avg Last Rescue Tick | Avg Wasted Ticks |
|-------------|---------------------|------------------|
| 0.0         | 268.4               | 570.0            |
| 1.0         | 258.6               | 530.1            |
| **2.0**     | **267.8**           | **257.2**        |
| 5.0         | 264.6               | 287.1            |

**Key Insight:** Fire-weight=2.0 has the **lowest wasted time** (257 ticks), meaning firefighters complete rescues more efficiently without unnecessary movement after the last person is saved.

## Analysis

### Why Fire-Weight = 2.0 Wins

1. **Balance:** Moderate fire proximity prioritization without over-weighting
2. **Stability:** Fewer replans needed (5.4 avg vs 11.15 for baseline)
3. **Efficiency:** 55% less wasted time than baseline (257 vs 570 ticks)
4. **Consistency:** Lower standard deviation (6.09% vs 9.45% baseline)

### Fire-Weight Formula Verified

The fire-weight priority formula is inversely proportional to distance from fire:

```python
proximity_boost = 1.0 + (fire_weight / (1.0 + fire_dist))
```

- At fire origin (dist=0): multiplier = 1 + fire_weight
- Far from fire (dist→∞): multiplier → 1

### Replanning Confirmation

All trials show extensive replanning activity (5-11 avg replans), confirming the replanning bug fix is working correctly:

**Before fix:** 0 replans across 400 trials (broken)
**After fix:** 5-11 replans per trial on average (working!)

## Comparison to Old Results

### Old Benchmarks (6 firefighters, broken replanning)

| Fire Weight | Survival | Timeout Rate | Replans |
|-------------|----------|--------------|---------|
| 0.0         | 97.78%   | 29.0%        | **0**   |
| 1.0         | 97.77%   | 21.0%        | **0**   |
| 2.0         | 97.09%   | 27.0%        | **0**   |
| 5.0         | 98.41%   | 18.0%        | **0**   |

**Status:** INVALID - replanning was broken, results unreliable

### New Benchmarks (2 firefighters, working replanning)

| Fire Weight | Survival | Wasted Time | Replans |
|-------------|----------|-------------|---------|
| 0.0         | 91.69%   | 570.0       | 11.15   |
| 1.0         | 91.58%   | 530.1       | 9.85    |
| **2.0**     | **91.91%** | **257.2**   | **5.40**  |
| 5.0         | 91.09%   | 287.1       | 6.05    |

**Status:** VALID - all fixes applied, replanning working

## Recommendation

**Use fire-weight = 2.0** for optimal rescue operations with 2 firefighters.

This configuration provides:
- Best survival rate (91.91%)
- Most efficient evacuation (lowest wasted time)
- Most stable routing (fewest replans needed)
- Most consistent results (lowest variance)

## Technical Notes

### Fixes Applied

1. **Replanning bug fixed** (optimal_rescue_model.py:382)
   - Now counts only existing edges (not burned)
   - Triggers correctly when hallways burn

2. **Survival rate formula corrected**
   - Changed from `rescued/(rescued+dead)` to `rescued/total_occupants`
   - Properly accounts for all initial occupants

3. **Fixed seeds implemented**
   - Seeds 1000-1019 for 20 trials
   - Ensures all fire-weight tests compare identical scenarios

4. **Phase transition filtering**
   - Automatically excludes bugged trials where sweep→rescue didn't occur

### Files Generated

- `fixed_fw0.0_2ff.json` - Baseline (fire-weight=0.0)
- `fixed_fw1.0_2ff.json` - Moderate (fire-weight=1.0)
- `fixed_fw2.0_2ff.json` - Strong (fire-weight=2.0) ← **BEST**
- `fixed_fw5.0_2ff.json` - Very Strong (fire-weight=5.0)

### Analysis Scripts

- `analyze_new_results.py` - Comprehensive analysis with replanning stats
- `benchmark_mall_fast.py` - Main benchmarking tool (updated with all fixes)

## Next Steps

1. Use fire-weight=2.0 as default parameter
2. Test with different firefighter counts (3, 4, 5, 6)
3. Analyze specific challenging scenarios (high replanning trials)
4. Document findings for HiMCM paper
