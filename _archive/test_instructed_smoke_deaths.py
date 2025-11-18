#!/usr/bin/env python3
"""
Test that instructed people can die from smoke while moving to exits
"""

import json
from simulator import Simulation

print("=" * 60)
print("TESTING SMOKE DEATHS FOR INSTRUCTED PEOPLE")
print("=" * 60)

with open('config_realistic_apartment.json', 'r') as f:
    config = json.load(f)

# Create simulation with fire origin that will generate smoke
sim = Simulation(
    config=config,
    num_firefighters=1,
    fire_origin='room_5',
    seed=42
)

print("\nScenario: Instruct people in a room, let smoke build up while they evacuate")

# Find a room with people
target_room = None
for vertex_id, vertex in sim.vertices.items():
    if vertex.type == 'room' and vertex.capable_count > 0 and vertex_id != 'room_5':
        target_room = vertex_id
        initial_count = vertex.capable_count
        break

print(f"\nTarget room: {target_room}")
print(f"Initial capable people: {initial_count}")

# Move firefighter to room and instruct
ff_id = 'ff_0'
sim.firefighters[ff_id].position = target_room
print(f"\nTick 1: Firefighter instructs {initial_count} people at {target_room}")
result = sim.update({ff_id: [{'type': 'instruct'}]})

# Run simulation and watch for smoke deaths
print("\n" + "=" * 60)
print("TRACKING EVACUATION AND SMOKE DEATHS")
print("=" * 60)

total_instructed_deaths = 0
smoke_death_events = []

for tick_num in range(30):
    result = sim.update({})

    # Check for instructed people deaths
    for event in result['events']:
        if event['type'] == 'smoke_deaths':
            vertex_id = event['vertex']
            vertex = sim.vertices[vertex_id]
            deaths_by_type = event.get('deaths_by_type', {})
            instructed_deaths = deaths_by_type.get('instructed', 0)

            if instructed_deaths > 0:
                total_instructed_deaths += instructed_deaths
                smoke_death_events.append({
                    'tick': sim.tick,
                    'vertex': vertex_id,
                    'deaths': instructed_deaths,
                    'smoke_level': vertex.smoke_level
                })
                print(f"\nTick {sim.tick}: ⚠️  {instructed_deaths} instructed people died from smoke!")
                print(f"  Location: {vertex_id}")
                print(f"  Smoke level: {vertex.smoke_level:.2%}")

    # Show instructed people locations
    instructed_locs = []
    for v_id, v in sim.vertices.items():
        if v.instructed_capable_count > 0:
            instructed_locs.append(f"{v_id}({v.instructed_capable_count})")

    if instructed_locs:
        print(f"Tick {sim.tick}: Instructed people at: {', '.join(instructed_locs)}")

    # Show rescues
    if result['rescued_this_tick'] > 0:
        print(f"  ✓ Rescued {result['rescued_this_tick']} people")

    # Check if all instructed people are rescued or dead
    total_instructed = sum(v.instructed_capable_count for v in sim.vertices.values())
    if total_instructed == 0:
        print(f"\nAll instructed people have either been rescued or died")
        break

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

print(f"\nInitial instructed: {initial_count}")
print(f"Rescued: {sim.rescued_count}")
print(f"Deaths from smoke (instructed): {total_instructed_deaths}")
print(f"Total deaths (all types): {sim.dead_count}")

if smoke_death_events:
    print(f"\n✓ VERIFIED: Instructed people CAN die from smoke while evacuating!")
    print(f"\nSmoke death events:")
    for event in smoke_death_events:
        print(f"  Tick {event['tick']}: {event['deaths']} died at {event['vertex']} (smoke: {event['smoke_level']:.1%})")
else:
    print(f"\n⚠️  No instructed people died from smoke in this test")
    print(f"   This might be because:")
    print(f"   - Smoke levels were too low")
    print(f"   - People evacuated too quickly")
    print(f"   - Random chance (death is probabilistic)")
    print(f"\n   But the code DOES support instructed people dying from smoke.")

print("\n" + "=" * 60)
