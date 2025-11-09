"""
Test the realistic apartment floor plan configuration
"""

import json
from simulator import Simulation
from demo_visualizer import SimpleGreedyModel


def test_realistic_apartment():
    """Test simulation with the realistic apartment layout"""
    print("="*60)
    print("TESTING REALISTIC APARTMENT FLOOR PLAN")
    print("="*60)

    # Load the realistic apartment config
    with open('config_realistic_apartment.json', 'r') as f:
        config = json.load(f)

    print(f"\nBuilding: {config['description']}")
    print(f"Dimensions: {config['dimensions']['width_m']}m x {config['dimensions']['height_m']}m")
    print(f"Total area: {config['dimensions']['total_area_sqm']} sqm")
    print(f"Vertices: {len(config['vertices'])}")
    print(f"Edges: {len(config['edges'])}")

    # Create simulation with more firefighters for larger building
    sim = Simulation(
        config=config,
        num_firefighters=3,  # 3 firefighters for apartment
        fire_origin=config['fire_params']['origin'],
        seed=42
    )

    initial_stats = sim.get_stats()
    print(f"\nInitial occupants: {initial_stats['total_initial']}")

    # Run with greedy AI
    model = SimpleGreedyModel()
    max_ticks = 200

    print("\nRunning simulation...")
    for tick in range(max_ticks):
        stats = sim.get_stats()

        if stats['remaining'] == 0:
            print(f"\n✓ All occupants accounted for at tick {tick}")
            break

        state = sim.read()
        actions = model.get_actions(state)
        results = sim.update(actions)

        if results['rescued_this_tick'] > 0:
            print(f"Tick {tick}: Rescued {results['rescued_this_tick']} people! Total: {sim.rescued_count}")

        if tick % 20 == 0:
            print(f"Tick {tick}: Rescued={stats['rescued']}, Dead={stats['dead']}, Remaining={stats['remaining']}")

    # Final results
    final_stats = sim.get_stats()
    print(f"\n{'='*60}")
    print("FINAL RESULTS - REALISTIC APARTMENT")
    print(f"{'='*60}")
    print(f"Time: {final_stats['time_minutes']:.1f} minutes ({final_stats['tick']} ticks)")
    print(f"Rescued: {final_stats['rescued']}")
    print(f"Dead: {final_stats['dead']}")
    print(f"Remaining: {final_stats['remaining']}")
    print(f"Total: {final_stats['total_initial']}")
    print(f"Survival rate: {final_stats['rescued'] / max(1, final_stats['total_initial']) * 100:.1f}%")

    # Compare to simple office building
    print(f"\n{'='*60}")
    print("COMPARISON TO SIMPLE OFFICE BUILDING")
    print(f"{'='*60}")
    print("Realistic Apartment:")
    print(f"  - 13 vertices (7 rooms, 4 hallways, 1 stairwell, 1 exit)")
    print(f"  - 135 sqm total area")
    print(f"  - 3 firefighters")
    print(f"  - Mixed use: bedrooms (high priority) + offices")
    print(f"  - Stairwell (can connect multiple floors)")
    print()
    print("Simple Office:")
    print(f"  - 11 vertices (6 rooms, 3 hallways, 2 exits)")
    print(f"  - ~600 sqm total area")
    print(f"  - 2 firefighters")
    print(f"  - Single use: offices only")

    return final_stats


if __name__ == '__main__':
    stats = test_realistic_apartment()

    print(f"\n{'='*60}")
    print("TEST COMPLETE")
    print(f"{'='*60}")
    print("\nTo visualize this floor plan:")
    print("  1. Edit demo_visualizer.py")
    print("  2. Change 'config_example.json' to 'config_realistic_apartment.json'")
    print("  3. Run: python3 demo_visualizer.py manual")
