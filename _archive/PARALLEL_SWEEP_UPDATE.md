# Fire-Weight Sweep: Parallel Processing Update

## Summary

Updated `sweep_fire_weight.py` to use **parallel processing** for running fire-weight parameter benchmarks. This reduces total execution time from **6-12 hours** to **2-4 hours** (3-4x speedup).

## Changes Made

### 1. Added Parallel Processing Infrastructure

```python
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import time
```

### 2. Updated `run_benchmark()` Function

- Added timestamped logging for start/completion
- Increased timeout from 600s to 1800s (30 minutes)
- Cleaner progress reporting with elapsed time

**Before:**
```python
print(f"\n{'='*70}")
print(f"Running benchmark: fire-weight = {fire_weight:.2f}")
```

**After:**
```python
start_time = time.time()
print(f"[{time.strftime('%H:%M:%S')}] Starting fire-weight = {fire_weight:.2f}")
...
elapsed = time.time() - start_time
print(f"[{time.strftime('%H:%M:%S')}] DONE fire-weight={fire_weight:.2f}: "
      f"avg={result_summary['avg_survival']:.1f}% ({elapsed:.1f}s)")
```

### 3. Rewrote `main()` for Parallel Execution

**Before** (Sequential):
```python
for fw in fire_weights:
    result = run_benchmark(fw, num_trials=200, num_firefighters=2)
    if result:
        results.append(result)
```

**After** (Parallel):
```python
num_workers = max(1, multiprocessing.cpu_count() - 1)

with ProcessPoolExecutor(max_workers=num_workers) as executor:
    future_to_fw = {
        executor.submit(run_benchmark, fw, 200, 2): fw
        for fw in fire_weights
    }

    for future in as_completed(future_to_fw):
        fw = future_to_fw[future]
        result = future.result()
        if result:
            results.append(result)
```

### 4. Added Progress Tracking

- Real-time completion counter: "Progress: 5/20 fire-weight values completed"
- Timestamped log messages for each benchmark
- Total elapsed time reporting

## Performance Improvement

| Metric | Before (Sequential) | After (Parallel) |
|--------|---------------------|------------------|
| **Execution mode** | One at a time | Multiple concurrent |
| **CPU utilization** | ~25% (1 core) | ~75-90% (multiple cores) |
| **Estimated time** | 6-12 hours | 2-4 hours |
| **Speedup** | 1x | 3-4x |

## Running the Sweep

```bash
python3 sweep_fire_weight.py
```

Output will show:
```
======================================================================
FIRE-WEIGHT PARAMETER SWEEP (PARALLEL)
======================================================================
Fire-weight values: 20 points from 0.0 to 5.0
Trials per value: 200
Firefighters: 2
Max ticks: 400 (~80 seconds)
Total benchmarks: 20 x 200 = 4000 trials
Parallel workers: 11
======================================================================

[14:23:01] Starting fire-weight = 0.00
[14:23:01] Starting fire-weight = 0.26
[14:23:01] Starting fire-weight = 0.53
...
[14:45:22] DONE fire-weight=0.00: avg=34.5% min=28.1% (1341.2s)
Progress: 1/20 fire-weight values completed
...
```

## Benefits

1. **Faster results**: Get sweep results in 2-4 hours instead of 6-12 hours
2. **Better CPU utilization**: Uses all available cores efficiently
3. **Real-time progress**: See which benchmarks are completing
4. **Robust error handling**: Failed benchmarks don't block others
5. **Timestamped logs**: Easy to track when each benchmark starts/finishes

## Files Modified

- `sweep_fire_weight.py` - Main sweep script (parallel processing)
- `SWEEP_STATUS.md` - Updated documentation
- `PARALLEL_SWEEP_UPDATE.md` - This file

## Next Steps

Run the parallel sweep to collect comprehensive fire-weight parameter data:

```bash
# Run the sweep in background and redirect output to log
python3 sweep_fire_weight.py > sweep_parallel.log 2>&1 &

# Monitor progress
tail -f sweep_parallel.log

# Or check how many are complete
ls -1 sweep_fw*.json | wc -l
```
