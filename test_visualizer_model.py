"""
Test the greedy model to verify rescued counts work properly
"""

import json
from simulator import Simulation
from demo_visualizer import SimpleGreedyModel


def test_greedy_model():
    """Test that the greedy model properly rescues people"""
    print("="*60)
    print("Testing Greedy Model with Simulator")
    print("="*60)

    # Load config
    with open('config_example.json', 'r') as f:
        config = json.load(f)

    # Create simulation
    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin=config['fire_params']['origin'],
        seed=42
    )

    model = SimpleGreedyModel()

    initial_stats = sim.get_stats()
    print(f"\nInitial state:")
    print(f"  Total occupants: {initial_stats['total_initial']}")

    # Run simulation for 100 ticks
    max_ticks = 100

    for tick in range(max_ticks):
        stats = sim.get_stats()

        # Stop if all accounted for
        if stats['remaining'] == 0:
            print(f"\n✓ All occupants accounted for at tick {tick}")
            break

        # Get actions from model
        state = sim.read()
        actions = model.get_actions(state)

        # Update simulation
        results = sim.update(actions)

        # Print rescue events
        if results['rescued_this_tick'] > 0:
            print(f"Tick {tick}: Rescued {results['rescued_this_tick']} people! Total: {sim.rescued_count}")

        # Print every 10 ticks
        if tick % 10 == 0:
            print(f"Tick {tick}: Rescued={stats['rescued']}, Dead={stats['dead']}, Remaining={stats['remaining']}")

    # Final stats
    final_stats = sim.get_stats()
    print(f"\n{'='*60}")
    print("FINAL RESULTS:")
    print(f"{'='*60}")
    print(f"Time: {final_stats['time_minutes']:.1f} minutes ({final_stats['tick']} ticks)")
    print(f"Rescued: {final_stats['rescued']}")
    print(f"Dead: {final_stats['dead']}")
    print(f"Remaining: {final_stats['remaining']}")
    print(f"Total: {final_stats['total_initial']}")
    print(f"Survival rate: {final_stats['rescued'] / max(1, final_stats['total_initial']) * 100:.1f}%")

    # Verify accounting
    total_accounted = final_stats['rescued'] + final_stats['dead'] + final_stats['remaining']
    if total_accounted == final_stats['total_initial']:
        print(f"\n✓ Accounting correct: {total_accounted} = {final_stats['total_initial']}")
    else:
        print(f"\n✗ Accounting ERROR: {total_accounted} ≠ {final_stats['total_initial']}")


if __name__ == '__main__':
    test_greedy_model()
