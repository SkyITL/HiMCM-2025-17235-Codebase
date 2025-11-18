#!/usr/bin/env python3
"""
Test that the greedy AI model now uses 2 actions per tick
"""

import json
from simulator import Simulation
from demo_visualizer import SimpleGreedyModel

print("=" * 60)
print("TESTING DOUBLE ACTION AI MODEL")
print("=" * 60)

with open('config_example.json', 'r') as f:
    config = json.load(f)

sim = Simulation(
    config=config,
    num_firefighters=2,
    fire_origin='office_bottom_center',
    seed=42
)

model = SimpleGreedyModel()

print("\nRunning simulation with greedy AI model")
print("Each firefighter should use 2 actions per tick")

# Run a few ticks and inspect the actions
for tick_num in range(5):
    state = sim.read()
    actions = model.get_actions(state)

    print(f"\n--- Tick {sim.tick + 1} ---")
    for ff_id, ff_actions in actions.items():
        print(f"{ff_id}: {len(ff_actions)} actions")
        for i, action in enumerate(ff_actions, 1):
            print(f"  Action {i}: {action}")

    # Execute the actions
    result = sim.update(actions)

    # Show results
    if result['rescued_this_tick'] > 0:
        print(f"  → Rescued {result['rescued_this_tick']} people!")

print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

# Count total actions taken
with open('config_example.json', 'r') as f:
    config = json.load(f)

sim2 = Simulation(
    config=config,
    num_firefighters=2,
    fire_origin='office_bottom_center',
    seed=42
)

total_actions_taken = 0
ticks_run = 0

for tick_num in range(10):
    state = sim2.read()
    actions = model.get_actions(state)

    # Count actions
    tick_actions = sum(len(ff_actions) for ff_actions in actions.values())
    total_actions_taken += tick_actions
    ticks_run += 1

    result = sim2.update(actions)

num_firefighters = len(sim2.firefighters)
print(f"\nRan {ticks_run} ticks with {num_firefighters} firefighters")
print(f"Total actions taken: {total_actions_taken}")
print(f"Average actions per firefighter per tick: {total_actions_taken / (ticks_run * num_firefighters):.2f}")

expected_avg = 2.0
actual_avg = total_actions_taken / (ticks_run * num_firefighters)

if actual_avg >= 1.8:  # Allow some slack for edge cases
    print(f"\n✓ VERIFIED: AI model is using ~2 actions per tick")
    print(f"   (Expected: {expected_avg}, Actual: {actual_avg:.2f})")
else:
    print(f"\n⚠️  WARNING: AI model averaging fewer than 2 actions per tick")
    print(f"   (Expected: {expected_avg}, Actual: {actual_avg:.2f})")

print("\n" + "=" * 60)
print("PERFORMANCE COMPARISON")
print("=" * 60)

print(f"\nFinal results after 10 ticks:")
print(f"  Rescued: {sim2.rescued_count}")
print(f"  Dead: {sim2.dead_count}")
print(f"  Remaining: {sum(v.capable_count + v.incapable_count + v.instructed_capable_count for v in sim2.vertices.values())}")

survival_rate = sim2.rescued_count / max(1, sim2.rescued_count + sim2.dead_count) * 100
print(f"  Survival rate: {survival_rate:.1f}%")
