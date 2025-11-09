"""
Floor Plan Analyzer
Helps convert a real floor plan image into graph representation for the simulator.

Based on the floor plan provided, this creates a realistic multi-room configuration.
"""

import json
from typing import Dict, List, Tuple


def analyze_floorplan_from_image():
    """
    Analyze the provided floor plan and extract structure.

    Floor plan appears to show:
    - Multi-room residential/office space
    - Central stairwell area
    - Multiple rooms of varying sizes
    - Dimensions approximately 15m x 9m
    - Several doorways and connections
    """

    # Identified rooms from the floor plan (reading the layout)
    rooms = {
        # Top-left area
        "room_1": {
            "type": "room",
            "room_type": "bedroom",  # Appears to be bedroom size
            "dimensions": (3.6, 3.8),  # Approximate from plan
            "position": "top_left",
            "doors": ["hallway_west"]
        },

        # Top-center area
        "room_2": {
            "type": "room",
            "room_type": "bedroom",
            "dimensions": (3.6, 3.6),
            "position": "top_center",
            "doors": ["hallway_central"]
        },

        # Top-right area
        "room_3": {
            "type": "room",
            "room_type": "bedroom",
            "dimensions": (4.2, 3.8),
            "position": "top_right",
            "doors": ["hallway_east"]
        },

        # Large room on right side
        "living_room": {
            "type": "room",
            "room_type": "living_room",
            "dimensions": (6.0, 4.2),
            "position": "east_large",
            "doors": ["hallway_east", "entrance_hall"]
        },

        # Bottom-left rooms
        "room_4": {
            "type": "room",
            "room_type": "office",
            "dimensions": (3.3, 3.0),
            "position": "bottom_left",
            "doors": ["hallway_west"]
        },

        "room_5": {
            "type": "room",
            "room_type": "office",
            "dimensions": (3.6, 3.0),
            "position": "bottom_center_left",
            "doors": ["hallway_central"]
        },

        "room_6": {
            "type": "room",
            "room_type": "office",
            "dimensions": (3.9, 3.0),
            "position": "bottom_center_right",
            "doors": ["hallway_central"]
        },

        # Stairwell area
        "stairwell": {
            "type": "stairwell",
            "room_type": "stairs",
            "dimensions": (2.4, 4.2),
            "position": "central",
            "connects_floors": True,
            "doors": ["entrance_hall", "hallway_central"]
        },

        # Hallways/circulation
        "hallway_west": {
            "type": "hallway",
            "room_type": "none",
            "dimensions": (1.2, 8.0),
            "position": "west_corridor"
        },

        "hallway_central": {
            "type": "hallway",
            "room_type": "none",
            "dimensions": (2.0, 6.0),
            "position": "central_corridor"
        },

        "hallway_east": {
            "type": "hallway",
            "room_type": "none",
            "dimensions": (1.5, 6.0),
            "position": "east_corridor"
        },

        "entrance_hall": {
            "type": "hallway",
            "room_type": "none",
            "dimensions": (3.0, 3.0),
            "position": "entrance",
            "doors": ["exit_main"]
        },

        # Exit (main door)
        "exit_main": {
            "type": "exit",
            "room_type": "none",
            "dimensions": (1.0, 1.0),
            "position": "entrance_door"
        }
    }

    # Identify connections (edges)
    connections = [
        # Hallway connections
        ("hallway_west", "hallway_central"),
        ("hallway_central", "hallway_east"),
        ("hallway_central", "entrance_hall"),
        ("entrance_hall", "stairwell"),
        ("stairwell", "hallway_central"),

        # Room to hallway connections
        ("room_1", "hallway_west"),
        ("room_2", "hallway_central"),
        ("room_3", "hallway_east"),
        ("room_4", "hallway_west"),
        ("room_5", "hallway_central"),
        ("room_6", "hallway_central"),
        ("living_room", "hallway_east"),
        ("living_room", "entrance_hall"),

        # Exit
        ("entrance_hall", "exit_main"),
    ]

    return rooms, connections


def generate_config_from_floorplan(filename: str = "config_realistic_apartment.json"):
    """Generate a complete simulation config from the floor plan analysis"""

    rooms, connections = analyze_floorplan_from_image()

    # Convert to simulation format
    vertices = []
    edges = []
    occupancy_probs = {}

    vertex_id = 0
    room_name_to_id = {}

    # Define visual positions (normalized 0.0 to 1.0)
    # These will be used by the visualizer
    visual_positions = {
        # Exit and entrance
        'exit_main': {'x': 0.1, 'y': 0.8},
        'entrance_hall': {'x': 0.2, 'y': 0.7},

        # Stairwell
        'stairwell': {'x': 0.35, 'y': 0.75},

        # Hallways
        'hallway_central': {'x': 0.5, 'y': 0.5},
        'hallway_west': {'x': 0.25, 'y': 0.35},
        'hallway_east': {'x': 0.75, 'y': 0.5},

        # Bedrooms (top row)
        'room_1': {'x': 0.15, 'y': 0.15},
        'room_2': {'x': 0.5, 'y': 0.15},
        'room_3': {'x': 0.75, 'y': 0.15},

        # Living room (right side)
        'living_room': {'x': 0.85, 'y': 0.6},

        # Offices (bottom)
        'room_4': {'x': 0.15, 'y': 0.55},
        'room_5': {'x': 0.4, 'y': 0.75},
        'room_6': {'x': 0.6, 'y': 0.75},
    }

    # Create vertices
    for room_name, room_data in rooms.items():
        vid = room_name  # Use room name as ID for clarity
        room_name_to_id[room_name] = vid

        # Calculate area
        if "dimensions" in room_data:
            area = room_data["dimensions"][0] * room_data["dimensions"][1]
        else:
            area = 20.0  # Default

        # Determine capacity based on room type
        if room_data["type"] == "room":
            if room_data["room_type"] == "bedroom":
                capacity = 4
                priority = 3  # High priority (people sleeping)
                sweep_time = 3
                occ_prob = 0.15  # 15% chance per sqm (bedrooms often occupied)
            elif room_data["room_type"] == "living_room":
                capacity = 10
                priority = 2
                sweep_time = 4
                occ_prob = 0.10
            else:  # office
                capacity = 6
                priority = 2
                sweep_time = 2
                occ_prob = 0.08
        elif room_data["type"] == "hallway":
            capacity = 20
            priority = 1
            sweep_time = 1
            occ_prob = 0.0  # No one in hallways initially
        elif room_data["type"] == "stairwell":
            capacity = 10
            priority = 1
            sweep_time = 2
            occ_prob = 0.0
        else:  # exit
            capacity = 100
            priority = 0
            sweep_time = 0
            occ_prob = 0.0

        vertex = {
            "id": vid,
            "type": room_data["type"],
            "room_type": room_data["room_type"],
            "capacity": capacity,
            "priority": priority,
            "sweep_time": sweep_time,
            "area": area,
            "visual_position": visual_positions.get(vid, {'x': 0.5, 'y': 0.5})  # Add position hint
        }

        vertices.append(vertex)

        if occ_prob > 0:
            occupancy_probs[vid] = occ_prob

    # Create edges
    edge_id = 0
    for room_a, room_b in connections:
        edge = {
            "id": f"e_{edge_id}",
            "vertex_a": room_a,
            "vertex_b": room_b,
            "max_flow": 5,  # Standard doorway
            "base_burn_rate": 0.0002  # Slightly higher for residential
        }
        edges.append(edge)
        edge_id += 1

    # Assemble config
    config = {
        "description": "Realistic apartment/office floor plan - approximately 15m x 9m with 7 rooms, hallways, stairwell, and main exit",
        "floor_plan_source": "Architectural drawing analysis",
        "dimensions": {
            "width_m": 15.0,
            "height_m": 9.0,
            "total_area_sqm": 135.0
        },
        "vertices": vertices,
        "edges": edges,
        "occupancy_probabilities": occupancy_probs,
        "fire_params": {
            "origin": "room_5",  # Fire starts in one of the offices
            "initial_smoke_level": 0.3
        }
    }

    # Save to file
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"Generated config: {filename}")
    print(f"  Vertices: {len(vertices)}")
    print(f"  Edges: {len(edges)}")
    print(f"  Rooms with occupants: {len(occupancy_probs)}")

    # Print summary
    print("\nFloor Plan Summary:")
    print(f"  Total area: ~135 sqm")
    print(f"  Bedrooms: 3")
    print(f"  Living room: 1 (large)")
    print(f"  Offices: 3")
    print(f"  Hallways: 3 corridors")
    print(f"  Stairwell: 1 (connects floors)")
    print(f"  Exits: 1 main door")

    return config


def print_graph_structure():
    """Print a text representation of the graph structure"""
    rooms, connections = analyze_floorplan_from_image()

    print("\n" + "="*60)
    print("GRAPH STRUCTURE")
    print("="*60)

    print("\nVERTICES:")
    for room_name, room_data in rooms.items():
        dims = room_data.get("dimensions", (0, 0))
        area = dims[0] * dims[1]
        print(f"  {room_name:20} | Type: {room_data['type']:10} | "
              f"Room: {room_data['room_type']:12} | Area: {area:5.1f}m²")

    print("\nEDGES (Connections):")
    for i, (a, b) in enumerate(connections, 1):
        print(f"  {i:2}. {a:20} <--> {b:20}")

    print("\n" + "="*60)


if __name__ == "__main__":
    print("="*60)
    print("FLOOR PLAN ANALYZER")
    print("="*60)

    # Generate the config
    config = generate_config_from_floorplan()

    # Print structure
    print_graph_structure()

    print("\n" + "="*60)
    print("Configuration saved to: config_realistic_apartment.json")
    print("="*60)
    print("\nTo use this configuration:")
    print("  python3 demo_visualizer.py manual")
    print("  # Then modify the code to load 'config_realistic_apartment.json'")
    print("\nOr test with:")
    print("  python3 test_simulator.py")
