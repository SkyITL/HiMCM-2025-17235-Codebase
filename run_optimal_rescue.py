#!/usr/bin/env python3
"""
Test runner for optimal rescue model.

Runs the mall1withoccupants.json scenario with the optimal rescue algorithm.
Compares performance with and without the optimization.
"""

import json
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel
from visualizer import EvacuationVisualizer


def run_with_optimal_model(config_path: str, use_lp: bool = False, visualize: bool = False):
    """
    Run simulation with optimal rescue model.

    Args:
        config_path: Path to JSON configuration file
        use_lp: Use LP solver (if available) vs greedy
        visualize: Show pygame visualization

    Returns:
        Final statistics dict
    """
    print("="*70)
    print(f"Running Optimal Rescue Model (LP={use_lp})")
    print("="*70)

    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Extract firefighter parameters
    ff_params = config.get('firefighter_params', {})
    num_firefighters = ff_params.get('num_firefighters', 3)

    # Extract fire parameters
    fire_params = config.get('fire_params', {})
    fire_origin = fire_params.get('origin', 'room_1')

    print(f"\nConfiguration:")
    print(f"  Fire origin: {fire_origin}")
    print(f"  Firefighters: {num_firefighters}")
    print(f"  Config file: {config_path}")

    # Create simulation
    sim = Simulation(
        config=config,
        num_firefighters=num_firefighters,
        fire_origin=fire_origin,
        seed=42
    )

    # Create optimal rescue model
    model = OptimalRescueModel(use_lp=use_lp)

    # Print initial state
    initial_stats = sim.get_stats()
    print(f"\nInitial State:")
    print(f"  Total occupants: {initial_stats['remaining']}")
    print(f"  Firefighters: {num_firefighters}")

    if visualize:
        # Run with visualization
        print("\nStarting visualization...")
        print("Controls:")
        print("  SPACE: Pause/Resume")
        print("  R: Reset")
        print("  Q/ESC: Quit")

        viz = EvacuationVisualizer(width=1400, height=900, manual_mode=False)
        viz.paused = False  # Auto-run
        viz.run(sim, model)
    else:
        # Run headless (fast)
        print("\nRunning simulation (headless)...")
        max_ticks = 1000
        tick = 0

        while tick < max_ticks:
            # Get state
            state = sim.read()

            # Generate actions
            actions = model.get_actions(state)

            # Update simulation
            results = sim.update(actions)

            # Check if done
            stats = sim.get_stats()
            if stats['remaining'] == 0:
                print(f"  All occupants evacuated or deceased at tick {tick}")
                break

            # Progress update
            if tick % 50 == 0:
                print(f"  Tick {tick}: {stats['rescued']} rescued, {stats['dead']} dead, {stats['remaining']} remaining")
                print(f"    Model phase: {model.phase}")

            tick += 1

    # Print final statistics
    print("\n" + "="*70)
    print("FINAL STATISTICS")
    print("="*70)

    final_stats = sim.get_stats()
    print(f"Total ticks: {final_stats['tick']}")
    print(f"Total time: {final_stats['time_minutes']:.2f} minutes")
    print(f"Rescued: {final_stats['rescued']}")
    print(f"Dead: {final_stats['dead']}")
    print(f"Remaining: {final_stats['remaining']}")

    if final_stats['rescued'] + final_stats['dead'] > 0:
        survival_rate = final_stats['rescued'] / (final_stats['rescued'] + final_stats['dead']) * 100
        print(f"Survival rate: {survival_rate:.1f}%")

    # Room and corridor damage
    burned_rooms = sum(1 for v in sim.vertices.values()
                      if v.is_burned and v.type == 'room')
    total_rooms = sum(1 for v in sim.vertices.values() if v.type == 'room')

    burned_corridors = sum(1 for e in sim.edges.values() if not e.exists)
    total_corridors = len(sim.edges)

    print(f"\nDamage:")
    print(f"  Burned rooms: {burned_rooms}/{total_rooms}")
    print(f"  Burned corridors: {burned_corridors}/{total_corridors}")

    print("\n" + "="*70)

    return final_stats


def main():
    """Main entry point."""
    import sys

    # Default config
    config_path = '/Users/skyliu/Downloads/mall1withoccupants.json'

    # Parse command line arguments
    use_lp = '--lp' in sys.argv
    visualize = '--viz' in sys.argv or '--visualize' in sys.argv

    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        config_path = sys.argv[1]

    # Run simulation
    stats = run_with_optimal_model(config_path, use_lp=use_lp, visualize=visualize)

    print("\nDone!")


if __name__ == '__main__':
    main()
