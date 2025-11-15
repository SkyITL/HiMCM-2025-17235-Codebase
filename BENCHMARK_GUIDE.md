# Benchmark Guide for Optimal Rescue System

## Purpose

This guide explains how to properly benchmark the optimal rescue system to assess **average survival rates** across different random scenarios.

## Important: Seeding vs Random Testing

### ❌ DO NOT use `--seed` for final benchmarks
```bash
# WRONG - This gives same fire origins every time
python3 benchmark_mall.py --trials 20 --seed 123
```

**Why?** Using a fixed seed means:
- Same fire origins in same order every run
- Not testing true variability
- Results don't reflect average performance across random scenarios
- Only useful for debugging/reproducibility of specific bugs

### ✅ DO use true randomness for final results
```bash
# CORRECT - Different fire origins each run
python3 benchmark_mall.py --trials 20

# CORRECT - Multiple independent runs
python3 benchmark_mall.py --trials 50 --output run1.json
python3 benchmark_mall.py --trials 50 --output run2.json
python3 benchmark_mall.py --trials 50 --output run3.json
```

**Why?** True randomness:
- Tests system robustness across diverse scenarios
- Gives realistic average survival rates
- Captures variance in performance
- Validates the algorithm works for ANY fire origin

## Benchmark Commands

### Basic Benchmark (No Fire Weighting)
```bash
python3 benchmark_mall.py \
  --trials 20 \
  --fire-weight 0.0 \
  --firefighters 6 \
  --output baseline_results.json
```

### With Fire Priority Weighting
```bash
python3 benchmark_mall.py \
  --trials 20 \
  --fire-weight 2.0 \
  --firefighters 6 \
  --output fire_weighted_results.json
```

### Testing Different Firefighter Counts
```bash
# Minimal staffing
python3 benchmark_mall.py --trials 20 --firefighters 3 --output ff3.json

# Medium staffing
python3 benchmark_mall.py --trials 20 --firefighters 6 --output ff6.json

# Full staffing
python3 benchmark_mall.py --trials 20 --firefighters 10 --output ff10.json
```

### Stress Testing (Many Trials)
```bash
# Large sample for statistical significance
python3 benchmark_mall.py \
  --trials 100 \
  --firefighters 6 \
  --output large_sample.json
```

## When TO Use Seeds

Seeds are ONLY appropriate for:

1. **Debugging specific scenarios**
   ```bash
   # Reproduce a specific bug
   python3 benchmark_mall.py --trials 5 --seed 42
   ```

2. **Comparing two algorithms**
   ```bash
   # Run both with same scenarios
   python3 benchmark_mall.py --trials 10 --seed 123 --fire-weight 0.0 --output algo_a.json
   python3 benchmark_mall.py --trials 10 --seed 123 --fire-weight 2.0 --output algo_b.json
   ```

3. **Unit testing**
   ```bash
   # Ensure consistent test results in CI/CD
   python3 benchmark_mall.py --trials 3 --seed 999 --quiet
   ```

## Interpreting Results

### Key Metrics

1. **Average Survival Rate**
   - Most important metric
   - Should be reported with standard deviation
   - Example: "95.3% ± 4.2%"

2. **Average Time**
   - How long to evacuate
   - Lower is better
   - Example: "0.73 minutes (44 seconds)"

3. **Average Replans**
   - How often adaptive replanning triggers
   - Shows system's dynamic response
   - Example: "2.3 replans per trial"

4. **Best/Worst Trials**
   - Shows performance range
   - Identifies problematic fire origins
   - Example: "Best: 100% (fire: room_1), Worst: 87% (fire: room_14)"

### Statistical Significance

For reliable results, run:
- **Minimum 20 trials** for quick testing
- **50-100 trials** for publication-quality results
- **Multiple independent runs** to verify consistency

### Example Analysis

```
Trial 1 (20 runs, no seed): 98.2% ± 3.1%
Trial 2 (20 runs, no seed): 97.8% ± 2.9%
Trial 3 (20 runs, no seed): 98.5% ± 3.4%

Conclusion: Consistent ~98% survival across runs
            Standard deviation ~3%, showing some variability
```

## Comparing Configurations

### Fire Weighting Impact
```bash
# Run both configurations
python3 benchmark_mall.py --trials 50 --fire-weight 0.0 --output baseline.json
python3 benchmark_mall.py --trials 50 --fire-weight 2.0 --output weighted.json

# Compare results
cat baseline.json | python3 -m json.tool | grep "avg_survival_rate"
cat weighted.json | python3 -m json.tool | grep "avg_survival_rate"
```

### Resource Sensitivity
```bash
# Test with different firefighter counts
for ff in 3 6 9 12; do
    python3 benchmark_mall.py \
        --trials 30 \
        --firefighters $ff \
        --output "ff${ff}_results.json"
done
```

## Output Files

Results are saved as JSON with structure:
```json
{
  "trials": [
    {
      "fire_origin": "room_X",
      "rescued": N,
      "dead": M,
      "survival_rate": X.X,
      "time_minutes": X.XX,
      "replan_count": N
    },
    ...
  ],
  "summary": {
    "avg_survival_rate": X.X,
    "std_survival_rate": X.X,
    "avg_time_minutes": X.XX,
    "avg_replan_count": X.X,
    ...
  },
  "config": {
    "num_trials": N,
    "fire_priority_weight": X.X,
    "num_firefighters": N
  }
}
```

## Best Practices

1. ✅ **No seeds for final benchmarks** (except for algorithm comparisons)
2. ✅ **Run multiple independent trials** (20-100)
3. ✅ **Report mean ± std deviation**
4. ✅ **Test multiple configurations** (different firefighter counts, fire weights)
5. ✅ **Save results to JSON** for later analysis
6. ✅ **Document methodology** (trials, config, date)

## Summary

**For HiMCM Paper:**
- Run at least 50 trials WITHOUT seed
- Test multiple configurations (3, 6, 9 firefighters)
- Compare baseline vs fire-weighted approaches
- Report: "Average survival rate: XX% ± YY% (n=50 trials)"

**For Debugging:**
- Use fixed seed to reproduce issues
- Run small number of trials (3-5)
- Compare before/after fixes with same seed

---
*Last updated: 2025-11-15*
