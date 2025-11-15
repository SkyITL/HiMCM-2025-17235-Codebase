#!/usr/bin/env python3
"""
Visualize the K-medoids + MST sweep strategy in action.

Shows both phases:
1. Sweep phase: Systematic room discovery using MST traversal
2. Optimal rescue phase: Coordinated rescue of incapable occupants
"""

import json
import pygame
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel
from visualizer import EvacuationVisualizer


def main():
    """
    Run visualization with both sweep and optimal rescue phases.
    """
    print("="*70)
    print("K-MEDOIDS + MST SWEEP STRATEGY VISUALIZATION")
    print("="*70)

    # Load mall config
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Create simulation
    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin='room_10',
        seed=42
    )

    # Get initial state
    initial_state = sim.read()
    initial_stats = sim.get_stats()

    print(f"\nInitial setup:")
    print(f"  Total occupants: {initial_stats['remaining']}")
    print(f"  Firefighters: {len(initial_state['firefighters'])}")
    print(f"  Fire origin: room_10")

    # Create model with sweep coordinator
    model = OptimalRescueModel(fire_priority_weight=0.0)

    # Create visualizer
    viz = EvacuationVisualizer(manual_mode=False)

    print(f"\nStarting visualization...")
    print(f"  - Watch firefighters systematically explore using MST paths")
    print(f"  - Observe balanced partitioning across 2 clusters")
    print(f"  - Phase will switch when all rooms discovered + all capable instructed")
    print(f"\nControls:")
    print(f"  SPACE: Pause/Resume")
    print(f"  Q/ESC: Quit")
    print(f"  +/-: Adjust speed")

    # Run visualization with the model
    viz.run(sim, model=model)


if __name__ == '__main__':
    main()
