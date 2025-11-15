#!/usr/bin/env python3
"""
Visualize seed 6 which gets stuck in sweep with 0 replans.
This shows a different type of issue - stuck without detecting it.
"""

import json
import pygame
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel
from visualizer import EvacuationVisualizer


def main():
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    print("="*80)
    print("VISUALIZING SEED 6 - Stuck in SWEEP with 0 replans")
    print("="*80)
    print("This trial gets stuck during exploration phase")
    print("Watch for when firefighters stop moving")
    print()
    print("Controls:")
    print("  SPACE: Pause/Resume")
    print("  Q/ESC: Quit")
    print("  +/-: Adjust speed")
    print()

    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin='room_2',
        seed=6
    )

    model = OptimalRescueModel(fire_priority_weight=0.0)
    viz = EvacuationVisualizer(manual_mode=False)

    print("Starting visualization...")
    print()

    # Run visualization with the model
    viz.run(sim, model=model)


if __name__ == '__main__':
    main()
