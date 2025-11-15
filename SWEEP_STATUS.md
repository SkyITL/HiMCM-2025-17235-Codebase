# Fire-Weight Parameter Sweep - Status

## Configuration

- **Fire-weight values**: 20 points from 0.0 to 5.0
  - [0.00, 0.26, 0.53, 0.79, 1.05, 1.32, 1.58, 1.84, 2.11, 2.37, 2.63, 2.89, 3.16, 3.42, 3.68, 3.95, 4.21, 4.47, 4.74, 5.00]
- **Trials per value**: 200
- **Firefighters**: 2
- **Max ticks**: 400 (~80 seconds simulated time)
- **Total trials**: 20 × 200 = **4,000 trials**
- **Execution mode**: **Parallel processing** (uses all available CPU cores - 1)

## Progress Monitoring

Check progress with:
```bash
# View live log
tail -f fire_weight_sweep.log

# Count completed benchmarks
ls -1 sweep_fw*.json 2>/dev/null | wc -l

# Check latest results
ls -ltr sweep_fw*.json | tail -5
```

## Outputs

### JSON Files
- `sweep_fw0.00.json` through `sweep_fw5.00.json` (20 files)
- `fire_weight_sweep_results.json` - Summary of all results

### Visualization
- `fire_weight_sweep.png` - Two-panel plot:
  - **Panel 1**: Average and minimum survival rates vs fire-weight (with ±1σ shaded region)
  - **Panel 2**: Consistency metrics (range and std dev)

## Expected Completion Time

**With parallel processing** (running multiple fire-weight values simultaneously):
- Each fire-weight value: ~20-40 minutes (200 trials)
- With CPU cores running in parallel: **2-4 hours total** (was 6-12 hours sequential)
- Speedup: ~3-4x faster with parallel execution

## Current Status

**RUNNING** - Started with updated parameters:
- max_ticks: 400 (changed from 350)
- trials: 200 per fire-weight value
- All fixes applied (replanning working, correct survival rate formula, phase transition filtering)

Monitor the sweep with `tail -f fire_weight_sweep.log` to see real-time progress.

## What This Will Tell Us

1. **Optimal fire-weight value** for 2-firefighter scenarios
2. **Survival rate trend** across fire-weight parameter space
3. **Consistency analysis** - which fire-weight values produce most reliable results
4. **Performance trade-offs** - balance between average survival and worst-case scenarios

## Next Steps After Completion

1. Analyze `fire_weight_sweep_results.json`
2. Review generated plot `fire_weight_sweep.png`
3. Identify optimal fire-weight for HiMCM paper
4. Compare to our earlier 4-point comparison (0.0, 1.0, 2.0, 5.0)
