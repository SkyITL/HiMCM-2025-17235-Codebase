#!/usr/bin/env python3
"""
Run simulation on the mall configuration.
"""

import json
import sys
from simulator import Simulation
from visualizer import EvacuationVisualizer

def main():
    # Load the mall configuration
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'

    print(f"Loading configuration from: {config_file}")
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Extract firefighter parameters
    firefighter_params = config.get('firefighter_params', {})
    num_firefighters = firefighter_params.get('num_firefighters', 3)
    spawn_vertices = firefighter_params.get('spawn_vertices', [])

    # Extract fire parameters
    fire_params = config.get('fire_params', {})
    fire_origin = fire_params.get('origin', 'room_1')

    print(f"\nSimulation Configuration:")
    print(f"  Fire origin: {fire_origin}")
    print(f"  Number of firefighters: {num_firefighters}")
    print(f"  Spawn vertices: {spawn_vertices if spawn_vertices else 'Auto (at exits)'}")

    # Count rooms with occupants
    num_rooms_with_occupants = len(config.get('occupancy_probabilities', {}))
    print(f"  Rooms with occupancy: {num_rooms_with_occupants}")

    # Create simulation
    print("\nCreating simulation...")
    sim = Simulation(
        config=config,
        num_firefighters=num_firefighters,
        fire_origin=fire_origin,
        seed=42
    )

    # Print initial state
    print(f"\nInitial State:")
    stats = sim.get_stats()
    print(f"  Total occupants: {stats['remaining']}")
    print(f"  Firefighters: {len(sim.firefighters)}")

    # Run visualization
    print("\nStarting visualization...")
    print("Controls:")
    print("  SPACE: Pause/Resume")
    print("  RIGHT ARROW: Step forward (when paused)")
    print("  LEFT ARROW: Step backward (when paused)")
    print("  R: Reset simulation")
    print("  Q or ESC: Quit")

    viz = EvacuationVisualizer(width=1400, height=900, manual_mode=True)
    viz.run(sim)

    # Print final statistics
    print("\n" + "="*50)
    print("FINAL STATISTICS")
    print("="*50)
    final_stats = sim.get_stats()
    print(f"Total ticks: {final_stats['tick']}")
    print(f"Total time: {final_stats['time_minutes']:.2f} minutes")
    print(f"Rescued: {final_stats['rescued']}")
    print(f"Dead: {final_stats['dead']}")
    print(f"Remaining: {final_stats['remaining']}")

    if final_stats['rescued'] + final_stats['dead'] > 0:
        survival_rate = final_stats['rescued'] / (final_stats['rescued'] + final_stats['dead']) * 100
        print(f"Survival rate: {survival_rate:.1f}%")

    # Room and corridor status
    burned_rooms = sum(1 for v in sim.vertices.values()
                      if v.is_burned and v.type == 'room')
    total_rooms = sum(1 for v in sim.vertices.values() if v.type == 'room')

    burned_corridors = sum(1 for e in sim.edges.values() if not e.exists)
    total_corridors = len(sim.edges)

    print(f"\nDamage:")
    print(f"  Burned rooms: {burned_rooms}/{total_rooms}")
    print(f"  Burned corridors: {burned_corridors}/{total_corridors}")

if __name__ == '__main__':
    main()
