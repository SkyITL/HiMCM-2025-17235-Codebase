"""
Scenario Launcher - Easy way to run different building configurations
"""

import sys
import json
from visualizer import visualize_manual, visualize_auto


SCENARIOS = {
    "office": {
        "name": "Simple Office Building",
        "config": "config_example.json",
        "firefighters": 2,
        "description": "6-room office with central hallway and 2 exits"
    },
    "apartment": {
        "name": "Realistic Apartment",
        "config": "config_realistic_apartment.json",
        "firefighters": 3,
        "description": "13-space apartment with 7 rooms, stairwell, and 1 exit"
    }
}


def list_scenarios():
    """Print available scenarios"""
    print("="*60)
    print("AVAILABLE SCENARIOS")
    print("="*60)
    for key, scenario in SCENARIOS.items():
        print(f"\n{key.upper()}:")
        print(f"  Name: {scenario['name']}")
        print(f"  File: {scenario['config']}")
        print(f"  Firefighters: {scenario['firefighters']}")
        print(f"  Description: {scenario['description']}")


def run_scenario(scenario_key: str, mode: str = "manual"):
    """Run a specific scenario"""
    if scenario_key not in SCENARIOS:
        print(f"Error: Unknown scenario '{scenario_key}'")
        print(f"Available scenarios: {', '.join(SCENARIOS.keys())}")
        return

    scenario = SCENARIOS[scenario_key]

    print("="*60)
    print(f"RUNNING: {scenario['name']}")
    print("="*60)
    print(f"Config: {scenario['config']}")
    print(f"Firefighters: {scenario['firefighters']}")
    print(f"Mode: {mode.upper()}")
    print("="*60 + "\n")

    # Load config
    with open(scenario['config'], 'r') as f:
        config = json.load(f)

    # Import after pygame check
    from simulator import Simulation
    from demo_visualizer import SimpleGreedyModel

    # Create simulation
    sim = Simulation(
        config=config,
        num_firefighters=scenario['firefighters'],
        fire_origin=config.get('fire_params', {}).get('origin', list(config['vertices'])[0]['id']),
        seed=42
    )

    # Run visualizer
    from visualizer import EvacuationVisualizer

    if mode == "manual":
        print("MANUAL MODE:")
        print("  - Click firefighters to select (cycle through if overlapping)")
        print("  - Click adjacent rooms to queue movement")
        print("  - Click buttons to queue actions")
        print("  - Click 'Step' to execute and advance time")
        print()
        viz = EvacuationVisualizer(manual_mode=True)
    else:
        print("AUTO MODE:")
        print("  - AI controls firefighters automatically")
        print("  - Use Play/Pause and Speed controls")
        print()
        model = SimpleGreedyModel()
        viz = EvacuationVisualizer(manual_mode=False)
        viz.paused = False

    if mode == "manual":
        viz.run(sim)
    else:
        viz.run(sim, model)


def main():
    if len(sys.argv) < 2:
        print("Emergency Evacuation Scenario Launcher")
        print()
        print("Usage:")
        print("  python3 run_scenario.py list")
        print("  python3 run_scenario.py <scenario> [mode]")
        print()
        print("Examples:")
        print("  python3 run_scenario.py office manual")
        print("  python3 run_scenario.py apartment auto")
        print()
        list_scenarios()
        return

    command = sys.argv[1].lower()

    if command == "list":
        list_scenarios()
    elif command in SCENARIOS:
        mode = sys.argv[2].lower() if len(sys.argv) > 2 else "manual"
        if mode not in ["manual", "auto"]:
            print(f"Error: Mode must be 'manual' or 'auto', got '{mode}'")
            return
        run_scenario(command, mode)
    else:
        print(f"Error: Unknown command or scenario '{command}'")
        print()
        list_scenarios()


if __name__ == '__main__':
    main()
