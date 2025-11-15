#!/usr/bin/env python3
"""
Visualize seed 1 which gets stuck in rescue with 20 replans.
This will show the trapped firefighter situation.
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
    print("VISUALIZING SEED 1 - Stuck in rescue with 20 replans")
    print("="*80)
    print("This trial gets trapped and triggers many replans")
    print("Watch for firefighter positions and replan events")
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
        seed=1
    )

    model = OptimalRescueModel(fire_priority_weight=0.0)
    viz = EvacuationVisualizer(manual_mode=False)

    print("Starting visualization...")
    print()

    # Run visualization with the model
    viz.run(sim, model=model)


if __name__ == '__main__':
    main()
