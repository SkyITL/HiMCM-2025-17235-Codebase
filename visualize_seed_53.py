#!/usr/bin/env python3
"""
Visualize seed 53 which is stuck in sweep phase.
"""

import json
import pygame
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel
from visualizer import EvacuationVisualizer


def main():
    """
    Run visualization for seed 53.
    """
    print("="*70)
    print("VISUALIZING SEED 53 (STUCK IN SWEEP)")
    print("="*70)

    # Load mall config
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Create simulation with seed 53
    # Seed in benchmark is 42 + trial_num, so trial 11 = seed 53
    # NOTE: Benchmark uses 6 firefighters, visualization demo used 2
    sim = Simulation(
        config=config,
        num_firefighters=2,  # Using 2 firefighters like visualization demo
        fire_origin='room_2',  # From benchmark results
        seed=53
    )

    # Get initial state
    initial_state = sim.read()
    initial_stats = sim.get_stats()

    print(f"\nInitial setup:")
    print(f"  Total occupants: {initial_stats['remaining']}")
    print(f"  Firefighters: {len(initial_state['firefighters'])}")
    print(f"  Fire origin: room_2")
    print(f"  Seed: 53")

    # Create model with sweep coordinator
    model = OptimalRescueModel(fire_priority_weight=0.0)

    # Create visualizer
    viz = EvacuationVisualizer(manual_mode=False)

    print(f"\nStarting visualization...")
    print(f"  This is trial 11 from benchmark (seed=42+11=53)")
    print(f"  Expected to get stuck in sweep phase")
    print(f"\nControls:")
    print(f"  SPACE: Pause/Resume")
    print(f"  Q/ESC: Quit")
    print(f"  +/-: Adjust speed")

    # Run visualization with the model
    viz.run(sim, model=model)


if __name__ == '__main__':
    main()
