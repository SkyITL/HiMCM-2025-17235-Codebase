"""
Quick visual test - opens visualizer for 5 seconds then auto-closes
Tests that pygame window opens and smoke displays correctly
"""

import json
import pygame
from simulator import Simulation
from visualizer import EvacuationVisualizer
from demo_visualizer import SimpleGreedyModel


def test_visual():
    """Quick 5-second visual test"""
    print("="*60)
    print("Visual Test - Window will auto-close after 5 seconds")
    print("="*60)
    print("Testing:")
    print("  - Pygame window opens")
    print("  - Smoke visualization renders")
    print("  - Rescued count updates")
    print("  - No color errors")
    print()

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
    viz = EvacuationVisualizer(manual_mode=False)
    viz.paused = False  # Auto-run

    # Calculate layout
    viz.layout.calculate_layout(sim)

    # Run for exactly 5 seconds (300 frames at 60fps)
    print("Opening pygame window...")
    max_frames = 300
    frame = 0
    ticks_since_update = 0

    running = True
    while running and frame < max_frames:
        dt = viz.clock.tick(60) / 1000.0
        frame += 1

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update simulation at speed 10 tps
        ticks_since_update += dt * 10
        if ticks_since_update >= 1.0:
            state = sim.read()
            actions = model.get_actions(state)
            results = sim.update(actions)
            ticks_since_update = 0

            # Print key events
            if results['rescued_this_tick'] > 0:
                print(f"  Tick {sim.tick}: Rescued {results['rescued_this_tick']}, Total={sim.rescued_count}")

        # Render
        viz.screen.fill((240, 240, 240))

        # Draw edges
        for edge_id in sim.edges.keys():
            viz.layout.draw_edge(viz.screen, edge_id, sim)

        # Draw vertices (this tests smoke rendering and fog of war)
        all_visited = set()
        for ff in sim.firefighters.values():
            all_visited.update(ff.visited_vertices)

        for vertex_id in sim.vertices.keys():
            viz.layout.draw_vertex(viz.screen, vertex_id, sim,
                                 show_all_occupants=True,
                                 visited_vertices=all_visited)

        # Draw firefighters
        for ff_id in sim.firefighters.keys():
            viz.layout.draw_firefighter(viz.screen, ff_id, sim, False)

        # Draw stats
        viz.draw_stats(viz.screen, sim)

        # Draw buttons
        for button in viz.buttons:
            button.draw(viz.screen)

        pygame.display.flip()

    pygame.quit()

    # Final results
    stats = sim.get_stats()
    print()
    print("="*60)
    print("Test Complete!")
    print("="*60)
    print(f"Simulation ran for {stats['tick']} ticks")
    print(f"Rescued: {stats['rescued']}")
    print(f"Dead: {stats['dead']}")
    print(f"Remaining: {stats['remaining']}")
    print(f"Survival rate: {stats['rescued'] / max(1, stats['total_initial']) * 100:.1f}%")
    print()
    print("✓ No errors - visualizer working correctly!")


if __name__ == '__main__':
    test_visual()
