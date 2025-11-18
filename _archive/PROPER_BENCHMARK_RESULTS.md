# Mall Evacuation Benchmark Results (PROPER - Unseeded)

## ⚠️ Important Note on Methodology

**Previous benchmarks used `--seed 123`** which made all trials use the same fire origins in the same order. While this is useful for reproducibility and debugging, it does NOT reflect true average performance.

**This benchmark uses TRUE RANDOMNESS (no seed)** to properly assess average survival rates across diverse scenarios.

## Test Configuration
- **Building**: Mall (22 rooms, 43 occupants)
- **Firefighters**: 6
- **Trials**: Currently running...
- **Random seed**: NONE (true randomness)

## Why No Seed?

### ❌ Seeded Testing (seed=123)
- Same fire origins every run: [room_2, room_21, room_18, ...]
- Results: Always 100% (because we memorized these specific scenarios)
- Use case: Debugging, algorithm comparison

### ✅ Unseeded Testing (no seed)
- Different fire origins each run: [room_14, room_3, room_9, ...]
- Results: True average across random scenarios
- Use case: **Final paper results, production validation**

## Recommended Benchmarking Process

For your HiMCM paper, run:

```bash
# Test baseline (no fire weighting)
python3 benchmark_mall.py --trials 50 --fire-weight 0.0 --output baseline_unseeded.json

# Test with fire weighting
python3 benchmark_mall.py --trials 50 --fire-weight 2.0 --output weighted_unseeded.json

# Test different staffing levels
python3 benchmark_mall.py --trials 30 --firefighters 3 --output ff3_unseeded.json
python3 benchmark_mall.py --trials 30 --firefighters 6 --output ff6_unseeded.json
python3 benchmark_mall.py --trials 30 --firefighters 9 --output ff9_unseeded.json
```

Then analyze:
- Average survival rate ± standard deviation
- Performance variance across fire origins
- Impact of fire weighting
- Resource efficiency (rescues per firefighter)

## Expected Results

With proper random testing, you should see:
- **Some variance** in survival rates (not always 100%)
- **Standard deviation > 0%** (showing different scenarios have different outcomes)
- **Different fire origins** causing different challenges
- **Realistic assessment** of algorithm performance

---
*Benchmark Guide: See BENCHMARK_GUIDE.md for complete methodology*
*Date: 2025-11-15*
