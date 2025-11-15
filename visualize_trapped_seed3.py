#!/usr/bin/env python3
"""
Visualize seed 3 which gets stuck in rescue with moderate replans.
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
    print("VISUALIZING SEED 3 - Stuck in rescue with moderate replans")
    print("="*80)
    print("This trial gets stuck during rescue phase")
    print("Watch for firefighter movements and replanning")
    print()
    print("Controls:")
    print("  SPACE: Pause/Resume")
    print("  Q/ESC: Quit")
    print("  +/-: Adjust speed")
    print()

    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin='room_10',
        seed=3
    )

    model = OptimalRescueModel(fire_priority_weight=0.0)
    viz = EvacuationVisualizer(manual_mode=False)

    print("Starting visualization...")
    print()

    # Run visualization with the model
    viz.run(sim, model=model)


if __name__ == '__main__':
    main()
