#!/usr/bin/env python3
"""
Unified Evacuation Visualization Script
Compatible with: Office, Mall (1-floor), Mall (2-floors), Childcare

Usage:
    python visualize_building.py <config_file> [num_firefighters] [fire_weight]

Examples:
    python visualize_building.py configs/office.json 2
    python visualize_building.py configs/mall_1floor.json 2 3.9744
    python visualize_building.py configs/mall_2floors.json 2 3.9744
    python visualize_building.py configs/childcare.json 3 3.9744
"""

import sys
import json
import random
import os

sys.path.insert(0, '/Users/skyliu/HiMCM2025')

from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel
from visualizer import EvacuationVisualizer

# Default paths for building configs
CONFIG_PATHS = {
    'office': '/Users/skyliu/Desktop/office.json',
    'mall_1floor': '/Users/skyliu/Downloads/mall f1.json',
    'mall_2floors': '/Users/skyliu/Downloads/mall_2floors_indestructible_stairs.json',
    'childcare': '/Users/skyliu/Desktop/childcare.json',
}

def find_config_file(config_input):
    """Find config file from various input types."""
    # If full path provided
    if os.path.exists(config_input):
        return config_input

    # If building name provided (office, mall_1floor, mall_2floors, childcare)
    if config_input in CONFIG_PATHS:
        path = CONFIG_PATHS[config_input]
        if os.path.exists(path):
            return path

    raise FileNotFoundError(f"Config file not found: {config_input}")

def get_building_name(config_path):
    """Determine building type from config path."""
    path_lower = config_path.lower()
    if 'office' in path_lower:
        return 'office'
    elif 'childcare' in path_lower:
        return 'childcare'
    elif '2floor' in path_lower or 'two.floor' in path_lower:
        return 'mall_2floors'
    elif 'mall' in path_lower or 'f1' in path_lower:
        return 'mall_1floor'
    return 'building'

def main():
    # Parse command line arguments
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    config_input = sys.argv[1]
    num_firefighters = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    fire_weight = float(sys.argv[3]) if len(sys.argv) > 3 else 3.9744

    # Find and load config
    try:
        config_file = find_config_file(config_input)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Loading building from: {config_file}")

    with open(config_file, 'r') as f:
        config = json.load(f)

    # Identify building type
    building_name = get_building_name(config_file)
    print(f"Building type: {building_name}")

    # Get all rooms for random fire origin
    rooms = [v['id'] for v in config['vertices'] if v['type'] == 'room']
    fire_origin = random.choice(rooms)
    print(f"Fire origin: {fire_origin}")

    # Create simulation
    print(f"Initializing simulation with {num_firefighters} firefighters")
    sim = Simulation(
        config=config,
        num_firefighters=num_firefighters,
        fire_origin=fire_origin,
        seed=42
    )

    # Create optimal rescue model
    model = OptimalRescueModel(fire_priority_weight=fire_weight)

    print("\nStarting evacuation visualization...")
    print(f"Fire weight: {fire_weight}")
    print("=" * 70)
    print()

    # Create visualizer and run
    viz = EvacuationVisualizer()
    viz.run(sim, model)

    print("\nSimulation completed!")

if __name__ == '__main__':
    main()
