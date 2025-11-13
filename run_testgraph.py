#!/usr/bin/env python3
"""
Run simulation on testgraph.json
"""

import json
from simulator import Simulation


def run_simulation_on_graph(graph_file: str):
    """Run simulation on a graph JSON file"""
    # Load the graph
    with open(graph_file, 'r') as f:
        graph_data = json.load(f)

    # Create a config by adding occupancy and fire parameters
    config = {
        "description": "Simulation of testgraph",
        "vertices": graph_data["vertices"],
        "edges": graph_data["edges"],
        "occupancy_probabilities": {},  # Add probabilities for room vertices
        "fire_params": {
            "origin": None,
            "initial_smoke_level": 0.3
        }
    }

    # Add occupancy probabilities for rooms
    for vertex in config["vertices"]:
        if vertex["type"] == "room":
            config["occupancy_probabilities"][vertex["id"]] = {
                "capable": 0.05,  # 5% chance per person
                "incapable": 0.005  # 0.5% chance per person
            }

    # Find a room to set as fire origin (prefer one in the middle)
    room_vertices = [v for v in config["vertices"] if v["type"] == "room"]
    if room_vertices:
        config["fire_params"]["origin"] = room_vertices[0]["id"]
        print(f"Fire origin: {config['fire_params']['origin']}")

    # Create and run simulation
    print(f"\nLoaded graph: {len(config['vertices'])} vertices, {len(config['edges'])} edges")

    sim = Simulation(
        config=config,
        num_firefighters=3,
        fire_origin=config['fire_params']['origin'],
        seed=42
    )

    # Print initial state
    state = sim.read()
    stats = sim.get_stats()
    print(f"\nInitial stats:")
    print(f"  Total occupants: {stats['total_initial']}")
    print(f"  Firefighters: {len(state['firefighters'])}")

    # Run simulation
    print("\nRunning simulation...")
    max_ticks = 500
    tick = 0

    while tick < max_ticks:
        stats = sim.get_stats()
        if stats['remaining'] == 0:
            break

        sim.update({})  # No actions, just let it run automatically
        tick += 1

        if tick % 50 == 0:
            print(f"  Tick {tick}: Rescued={stats['rescued']}, Dead={stats['dead']}, Remaining={stats['remaining']}")

    # Final stats
    stats = sim.get_stats()
    print(f"\nFinal Results (Tick {tick}):")
    print(f"  Rescued: {stats['rescued']}")
    print(f"  Dead: {stats['dead']}")
    print(f"  Remaining: {stats['remaining']}")
    print(f"  Survival rate: {stats['rescued'] / max(1, stats['total_initial']) * 100:.1f}%")

    return sim


if __name__ == "__main__":
    run_simulation_on_graph('/Users/skyliu/Downloads/testgraph.json')
