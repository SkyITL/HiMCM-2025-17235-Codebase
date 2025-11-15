# Fire-Weight Parameter Sweep - STARTED

## Status: RUNNING

The parallel fire-weight parameter sweep has been successfully started and is currently running in the background.

## Configuration

- **Fire-weight values**: 20 points from 0.0 to 5.0
- **Trials per value**: 200 trials each
- **Firefighters**: 2
- **Max ticks**: 400 (~80 seconds simulated time)
- **Total trials**: 4,000 trials (20 fire-weights × 200 trials)
- **Parallel workers**: 15 (using all available CPU cores - 1)

## Current Progress

```
Completed: 0 / 20 fire-weight values
Active processes: 16 benchmarks running in parallel
Estimated completion: 2-4 hours from start
```

## Monitoring the Sweep

### Quick Status Check
```bash
./monitor_sweep.sh
```

### Continuous Monitoring
```bash
# Update every 5 seconds
watch -n 5 ./monitor_sweep.sh

# Or watch the log in real-time
tail -f fire_weight_sweep.log
```

### Check Completed Benchmarks
```bash
ls -1 sweep_fw*.json | wc -l
```

## Output Files

### Individual Benchmark Results
- `sweep_fw0.00.json` through `sweep_fw5.00.json` (20 files)
- Each contains 200 trial results for that specific fire-weight value

### Final Outputs (generated when sweep completes)
- `fire_weight_sweep_results.json` - Summary of all 20 fire-weight values
- `fire_weight_sweep.png` - Visualization with two panels:
  - Panel 1: Average and minimum survival rates vs fire-weight (with ±1σ shaded region)
  - Panel 2: Consistency metrics (range and std dev)

## Expected Timeline

With parallel processing (15 workers):
- **Per fire-weight value**: ~20-40 minutes (200 trials each)
- **Total estimated time**: 2-4 hours (vs 6-12 hours sequential)
- **Speedup**: 3-4x faster

The first batch of 15 fire-weight values will complete around 20-40 minutes from start. The remaining 5 will complete shortly after.

## What the Sweep Will Tell Us

1. **Optimal fire-weight value** for 2-firefighter evacuation scenarios
2. **Survival rate trends** across the fire-weight parameter space
3. **Consistency analysis** - which fire-weight values produce reliable results
4. **Performance trade-offs** - balance between average survival and worst-case scenarios

## Implementation Features

### Parallel Processing
- Uses Python's `concurrent.futures.ProcessPoolExecutor`
- Automatically detects and uses all available CPU cores
- Runs multiple fire-weight benchmarks simultaneously
- Robust error handling - failed benchmarks don't block others

### Progress Tracking
- Timestamped logs for each benchmark start/completion
- Real-time completion counter
- Total elapsed time reporting
- Per-benchmark performance metrics

### Output Includes
- Average survival rate for each fire-weight
- Minimum and maximum survival rates
- Standard deviation (consistency metric)
- Valid trials vs total trials ratio
- Complete results in JSON format

## Next Steps

Once the sweep completes, you'll receive:

1. **Comprehensive data**: All 20 fire-weight values tested with 200 trials each
2. **Visualization**: Publication-ready plot showing survival rate trends
3. **Optimal parameter**: Data-driven recommendation for best fire-weight value
4. **Statistical analysis**: Understanding of variability and consistency

The sweep process will automatically generate the visualization and summary table when all 20 benchmarks complete.

## Trapped Firefighter Redistribution

This sweep also tests the newly implemented **trapped firefighter item redistribution** feature:

- When a firefighter becomes trapped (no reachable exits), their remaining rescue items are automatically redistributed to active firefighters
- This prevents wasted rescue capacity and improves survival rates
- The feature is fully integrated and will be active during all 4,000 trials

---

**Started**: 2025-11-15
**Process**: Running in background with nohup
**Log file**: `fire_weight_sweep.log`
**Monitor script**: `./monitor_sweep.sh`
