#!/bin/bash
# Monitor the fire-weight parameter sweep progress

echo "======================================================================"
echo "FIRE-WEIGHT SWEEP PROGRESS MONITOR"
echo "======================================================================"
echo ""

# Count completed benchmarks
completed=$(ls -1 sweep_fw*.json 2>/dev/null | wc -l | tr -d ' ')
echo "Completed benchmarks: $completed / 20"

# List completed fire-weight values
if [ $completed -gt 0 ]; then
    echo ""
    echo "Completed fire-weight values:"
    ls -1 sweep_fw*.json 2>/dev/null | sed 's/sweep_fw//g' | sed 's/.json//g' | sort -n | tr '\n' ', ' | sed 's/,$/\n/'
fi

echo ""
echo "Active benchmark processes: $(ps aux | grep 'benchmark_mall_fast' | grep -v grep | wc -l | tr -d ' ')"

echo ""
echo "Sweep process status:"
if ps aux | grep 'sweep_fire_weight.py' | grep -v grep > /dev/null; then
    echo "  RUNNING ✓"
else
    echo "  NOT RUNNING ✗"
fi

echo ""
echo "Recent log output:"
echo "----------------------------------------------------------------------"
tail -10 fire_weight_sweep.log

echo ""
echo "======================================================================"
echo "To monitor continuously: watch -n 5 ./monitor_sweep.sh"
echo "To view full log: tail -f fire_weight_sweep.log"
echo "======================================================================"
