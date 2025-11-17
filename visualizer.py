"""
Emergency Evacuation Visualizer
Interactive visualization tool for the evacuation simulator with manual control support.
"""

import pygame
import json
import math
from typing import Dict, List, Tuple, Optional
from simulator import Simulation


# Colors
COLORS = {
    'background': (240, 240, 240),
    'room': (200, 220, 255),
    'hallway': (220, 220, 220),
    'exit': (100, 255, 100),
    'window_exit': (150, 255, 150),
    'wall': (50, 50, 50),
    'edge': (100, 100, 100),
    'edge_blocked': (255, 0, 0),
    'firefighter': (255, 150, 0),
    'fire': (255, 50, 0),
    'smoke_light': (180, 180, 180, 100),
    'smoke_medium': (120, 120, 120, 150),
    'smoke_heavy': (60, 60, 60, 200),
    'text': (0, 0, 0),
    'occupants': (0, 100, 200),
    'selected': (255, 255, 0),
    'button': (100, 150, 255),
    'button_hover': (150, 180, 255),
    'button_text': (255, 255, 255),
}


class LayoutVisualizer:
    """Handles the visual representation of the building layout"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.vertex_positions: Dict[str, Tuple[float, float]] = {}
        self.layout_calculated = False

    def calculate_layout(self, sim: Simulation):
        """Calculate positions for all vertices using manual or automatic layout"""

        # Check if we have a manual layout for this configuration
        if self._try_manual_layout(sim):
            self.layout_calculated = True
            return

        # Fall back to automatic layout
        self._automatic_layout(sim)
        self.layout_calculated = True

    def _try_manual_layout(self, sim: Simulation) -> bool:
        """Try to load layout from config visual_position hints"""

        margin = 100
        w = self.width - 2 * margin
        h = self.height - 2 * margin - 150

        # Check if vertices have visual_position hints in the config
        has_positions = False
        for vertex_id, vertex in sim.vertices.items():
            # Check if vertex has visual_position attribute
            if hasattr(vertex, 'visual_position') and vertex.visual_position:
                has_positions = True
                break

        if has_positions:
            # First, find the bounds of the coordinate system
            min_x, max_x = float('inf'), float('-inf')
            min_y, max_y = float('inf'), float('-inf')

            for vertex in sim.vertices.values():
                if hasattr(vertex, 'visual_position') and vertex.visual_position:
                    pos = vertex.visual_position
                    if 'x' in pos and 'y' in pos:
                        min_x = min(min_x, pos['x'])
                        max_x = max(max_x, pos['x'])
                        min_y = min(min_y, pos['y'])
                        max_y = max(max_y, pos['y'])

            # Normalize coordinates to 0.0-1.0 range
            x_range = max_x - min_x if max_x > min_x else 1.0
            y_range = max_y - min_y if max_y > min_y else 1.0

            # Use positions from config
            for vertex_id, vertex in sim.vertices.items():
                if hasattr(vertex, 'visual_position') and vertex.visual_position:
                    pos = vertex.visual_position
                    if 'x' in pos and 'y' in pos:
                        # Normalize to 0-1 using graph maker's coordinate system
                        norm_x = (pos['x'] - min_x) / x_range
                        norm_y = (pos['y'] - min_y) / y_range  # Use as-is from graph maker
                        x = margin + w * norm_x
                        y = margin + h * norm_y
                        self.vertex_positions[vertex_id] = (x, y)
            return True

        return False

    def _automatic_layout(self, sim: Simulation):
        """Automatic grid-based layout for simple configurations"""
        vertices = list(sim.vertices.keys())

        # Separate by type
        exits = [v for v in vertices if sim.vertices[v].type in ['exit', 'window_exit']]
        hallways = [v for v in vertices if sim.vertices[v].type == 'hallway']
        stairwells = [v for v in vertices if sim.vertices[v].type == 'stairwell']
        rooms = [v for v in vertices if sim.vertices[v].type == 'room']

        margin = 100
        usable_width = self.width - 2 * margin
        usable_height = self.height - 2 * margin - 150  # Reserve space for stats

        # Place exits on opposite sides
        if len(exits) >= 2:
            self.vertex_positions[exits[0]] = (margin, usable_height // 2 + margin)
            self.vertex_positions[exits[1]] = (self.width - margin, usable_height // 2 + margin)
            if len(exits) > 2:
                for i, exit_id in enumerate(exits[2:]):
                    x = margin + (i + 1) * usable_width // (len(exits) - 1)
                    self.vertex_positions[exit_id] = (x, margin)
        elif len(exits) == 1:
            self.vertex_positions[exits[0]] = (margin + usable_width * 0.1, margin + usable_height * 0.8)

        # Place hallways and stairwells
        circulation = hallways + stairwells
        if circulation:
            hallway_spacing = usable_width // (len(circulation) + 1)
            for i, hall_id in enumerate(circulation):
                x = margin + (i + 1) * hallway_spacing
                y = usable_height // 2 + margin
                self.vertex_positions[hall_id] = (x, y)

        # Place rooms around hallways
        if rooms:
            rooms_per_row = math.ceil(len(rooms) / 2)
            room_spacing_x = usable_width // (rooms_per_row + 1)

            for i, room_id in enumerate(rooms):
                col = i % rooms_per_row
                row = i // rooms_per_row

                x = margin + (col + 1) * room_spacing_x
                y = margin + (row * 2 + 1) * usable_height // 4

                self.vertex_positions[room_id] = (x, y)

    def draw_edge(self, screen: pygame.Surface, edge_id: str, sim: Simulation):
        """Draw an edge (corridor)"""
        edge = sim.edges[edge_id]

        if edge_id not in sim.edges or not edge.exists:
            return

        pos_a = self.vertex_positions.get(edge.vertex_a)
        pos_b = self.vertex_positions.get(edge.vertex_b)

        if pos_a and pos_b:
            color = COLORS['edge'] if edge.exists else COLORS['edge_blocked']
            # Scale line width based on corridor width (edge.width is in meters)
            # Use sqrt scaling so visual width scales more intuitively
            width = max(1, int(2 + edge.width * 0.8)) if edge.exists else 1

            if edge.exists:
                pygame.draw.line(screen, color, pos_a, pos_b, width)
            else:
                # Draw dashed line for blocked edges
                self._draw_dashed_line(screen, COLORS['edge_blocked'], pos_a, pos_b, 1)

    def _draw_dashed_line(self, screen, color, start, end, width):
        """Draw a dashed line"""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx**2 + dy**2)

        if distance == 0:
            return

        dashes = int(distance / 10)
        for i in range(0, dashes, 2):
            start_pos = (
                start[0] + dx * i / dashes,
                start[1] + dy * i / dashes
            )
            end_pos = (
                start[0] + dx * min(i + 1, dashes) / dashes,
                start[1] + dy * min(i + 1, dashes) / dashes
            )
            pygame.draw.line(screen, color, start_pos, end_pos, width)

    def draw_vertex(self, screen: pygame.Surface, vertex_id: str, sim: Simulation,
                   selected: bool = False, show_all_occupants: bool = True,
                   visited_vertices: set = None):
        """Draw a vertex (room, hallway, or exit)"""
        if vertex_id not in self.vertex_positions:
            return

        vertex = sim.vertices[vertex_id]
        pos = self.vertex_positions[vertex_id]

        # Calculate radius based on area (in square meters)
        # Use square root scaling so visual area is proportional to actual area
        # radius ∝ sqrt(area) means π*r² ∝ area
        area = vertex.area if hasattr(vertex, 'area') else 100.0

        # Enhanced scaling to make size differences more visible
        # Scale factor: sqrt(area) * 6.0 makes differences more apparent
        base_radius = math.sqrt(area) * 6.0

        # Apply type-specific adjustments with lower minimums
        if vertex.type in ['exit', 'window_exit']:
            radius = max(12, int(base_radius * 0.6))  # Exits
            color = COLORS['exit'] if vertex.type == 'exit' else COLORS['window_exit']
        elif vertex.type in ['hallway', 'corridor', 'intersection', 'stair']:
            radius = max(8, int(base_radius * 0.4))  # Hallways, corridors, intersections, stairs (smallest)
            color = COLORS['hallway']
        else:  # room
            radius = max(10, int(base_radius))  # Rooms (variable size, low minimum)
            color = COLORS['room']

        # Apply fire weight factor heat map coloring (only for rooms)
        # Shows the weighting factor used in fire spread calculations
        # Uses non-linear scaling to emphasize differences in high-weight ranges
        if vertex.type == 'room' and hasattr(vertex, 'fire_weight_factor'):
            weight = min(1.0, vertex.fire_weight_factor)

            # Apply power scaling to spread out high weights: weight^2 emphasizes differences
            # E.g., 0.74 -> 0.548, 0.88 -> 0.774, 1.0 -> 1.0
            scaled_weight = weight ** 2

            if scaled_weight >= 0.8:
                # Very high: DEEP RED
                t = (scaled_weight - 0.8) / 0.2
                r = 255
                g = int(20 * (1 - t))
                b = int(20 * (1 - t))
                color = (r, g, b)
            elif scaled_weight >= 0.6:
                # High: RED to ORANGE
                t = (scaled_weight - 0.6) / 0.2
                r = 255
                g = int(50 + (150 - 50) * t)
                b = 0
                color = (r, g, b)
            elif scaled_weight >= 0.4:
                # Medium-high: ORANGE to YELLOW
                t = (scaled_weight - 0.4) / 0.2
                r = 255
                g = int(150 + (220 - 150) * t)
                b = 0
                color = (r, g, b)
            elif scaled_weight >= 0.2:
                # Medium: YELLOW to LIGHT YELLOW
                t = (scaled_weight - 0.2) / 0.2
                r = 255
                g = int(220 + (240 - 220) * t)
                b = int(50 * t)
                color = (r, g, b)
            else:
                # Low: LIGHT color
                r = 255
                g = 245
                b = 150
                color = (r, g, b)

        # Modify color if burned (override with darkened red)
        if vertex.is_burned:
            color = COLORS['fire']

        # Draw smoke overlay - make it more visible
        if vertex.smoke_level > 0.05:
            # Make smoke extend beyond the vertex for better visibility
            smoke_radius = int(radius * (1 + vertex.smoke_level * 0.5))
            smoke_surface = pygame.Surface((smoke_radius * 2, smoke_radius * 2), pygame.SRCALPHA)

            # More visible smoke colors with stronger alpha (clamped to 255)
            if vertex.smoke_level < 0.3:
                alpha = min(255, int(100 + vertex.smoke_level * 400))
                smoke_color = (150, 150, 150, alpha)
            elif vertex.smoke_level < 0.7:
                alpha = min(255, int(150 + vertex.smoke_level * 250))
                smoke_color = (100, 100, 100, alpha)
            else:
                alpha = min(255, int(200 + vertex.smoke_level * 55))
                smoke_color = (50, 50, 50, alpha)

            pygame.draw.circle(smoke_surface, smoke_color, (smoke_radius, smoke_radius), smoke_radius)
            screen.blit(smoke_surface, (pos[0] - smoke_radius, pos[1] - smoke_radius))

        # Draw main circle
        pygame.draw.circle(screen, color, pos, radius)

        # Draw selection highlight
        if selected:
            pygame.draw.circle(screen, COLORS['selected'], pos, radius + 3, 3)

        # Draw border
        pygame.draw.circle(screen, COLORS['wall'], pos, radius, 2)

        # Draw area label for all rooms (showing size in m²)
        if vertex.type == 'room':
            font_tiny = pygame.font.Font(None, 14)
            area_text = f"{area:.1f}m²"
            text = font_tiny.render(area_text, True, (100, 100, 100))
            text_rect = text.get_rect(center=(pos[0], pos[1] - radius - 8))
            screen.blit(text, text_rect)

        # Draw occupant count if room (fog of war in manual mode)
        if vertex.type == 'room':
            # Only show occupants if: show_all_occupants=True OR room has been visited
            is_visible = show_all_occupants or (visited_vertices and vertex_id in visited_vertices)

            # Calculate total occupants
            total_occupants = vertex.capable_count + vertex.incapable_count + vertex.instructed_capable_count

            if is_visible and total_occupants > 0:
                font = pygame.font.Font(None, 18)
                # Display format: C:# I:# →:#
                display_text = f"C:{vertex.capable_count} I:{vertex.incapable_count}"
                if vertex.instructed_capable_count > 0:
                    display_text += f" →{vertex.instructed_capable_count}"

                text = font.render(display_text, True, COLORS['occupants'])
                # Offset text to bottom to avoid firefighter overlap
                text_rect = text.get_rect(center=(pos[0], pos[1] + 8))
                screen.blit(text, text_rect)
            elif not is_visible and not vertex.is_burned:
                # Show "?" for unvisited rooms
                font = pygame.font.Font(None, 24)
                text = font.render('?', True, (150, 150, 150))
                text_rect = text.get_rect(center=pos)
                screen.blit(text, text_rect)

            # Draw smoke level percentage if significant (always visible for rooms)
            if vertex.smoke_level > 0.2:
                font_small = pygame.font.Font(None, 16)
                smoke_text = f"{int(vertex.smoke_level * 100)}%"
                text = font_small.render(smoke_text, True, (255, 50, 50))
                # Position below occupant count
                text_rect = text.get_rect(center=(pos[0], pos[1] + 20))
                screen.blit(text, text_rect)

        # Draw instructed people in hallways/corridors (people in transit)
        if vertex.type in ['hallway', 'stairwell'] and vertex.instructed_capable_count > 0:
            # Draw small person icons moving through corridor
            font = pygame.font.Font(None, 18)
            transit_text = f"→{vertex.instructed_capable_count}"
            text = font.render(transit_text, True, (0, 150, 100))
            text_rect = text.get_rect(center=(pos[0], pos[1] + 5))

            # Draw background circle for visibility
            bg_radius = 12
            pygame.draw.circle(screen, (255, 255, 255, 200), text_rect.center, bg_radius)
            pygame.draw.circle(screen, (0, 150, 100), text_rect.center, bg_radius, 1)

            screen.blit(text, text_rect)

            # Draw smoke level percentage if significant (always visible)
            if vertex.smoke_level > 0.2:
                font_small = pygame.font.Font(None, 16)
                smoke_text = f"{int(vertex.smoke_level * 100)}%"
                text = font_small.render(smoke_text, True, (255, 50, 50))
                # Position below occupant count
                text_rect = text.get_rect(center=(pos[0], pos[1] + 20))
                screen.blit(text, text_rect)

        # Draw label
        font_small = pygame.font.Font(None, 16)
        label = vertex_id.replace('_', ' ').title()
        if len(label) > 15:
            label = vertex_id.split('_')[-1].title()

        text = font_small.render(label, True, COLORS['text'])
        text_rect = text.get_rect(center=(pos[0], pos[1] + radius + 12))
        screen.blit(text, text_rect)

    def draw_firefighter(self, screen: pygame.Surface, ff_id: str, sim: Simulation,
                        selected: bool = False, firefighters_at_same_pos: List[str] = None):
        """Draw a firefighter"""
        ff = sim.firefighters[ff_id]

        if ff.position not in self.vertex_positions:
            return

        base_pos = self.vertex_positions[ff.position]

        # Count firefighters at same position and get this one's index
        if firefighters_at_same_pos is None:
            firefighters_at_same_pos = [
                fid for fid, f in sim.firefighters.items()
                if f.position == ff.position
            ]

        ff_count = len(firefighters_at_same_pos)
        ff_index = firefighters_at_same_pos.index(ff_id)

        # Offset multiple firefighters at same location
        if ff_count > 1:
            offset_angle = ff_index * (2 * math.pi / ff_count)
            offset_distance = 20
        else:
            offset_angle = 0
            offset_distance = 0

        pos = (
            base_pos[0] + offset_distance * math.cos(offset_angle),
            base_pos[1] + offset_distance * math.sin(offset_angle)
        )

        # Draw firefighter
        pygame.draw.circle(screen, COLORS['firefighter'], pos, 12)

        if selected:
            pygame.draw.circle(screen, COLORS['selected'], pos, 15, 3)

        pygame.draw.circle(screen, COLORS['wall'], pos, 12, 2)

        # Draw ID
        font_small = pygame.font.Font(None, 14)
        text = font_small.render(ff_id, True, COLORS['text'])
        text_rect = text.get_rect(center=(pos[0], pos[1] - 20))
        screen.blit(text, text_rect)

        # Draw badge showing count if multiple firefighters at same position
        if ff_count > 1 and ff_index == 0:  # Only draw once per position
            badge_pos = (base_pos[0] + 25, base_pos[1] - 25)
            # Draw background circle
            pygame.draw.circle(screen, (255, 200, 0), badge_pos, 10)
            pygame.draw.circle(screen, COLORS['wall'], badge_pos, 10, 1)
            # Draw count
            font_tiny = pygame.font.Font(None, 16)
            text = font_tiny.render(f"x{ff_count}", True, COLORS['text'])
            text_rect = text.get_rect(center=badge_pos)
            screen.blit(text, text_rect)

        # Draw carrying indicator
        if ff.carrying_incapable > 0:
            carry_badge_pos = (pos[0] + 15, pos[1] + 15)
            pygame.draw.circle(screen, (100, 200, 255), carry_badge_pos, 8)
            pygame.draw.circle(screen, COLORS['wall'], carry_badge_pos, 8, 1)
            font_tiny = pygame.font.Font(None, 14)
            text = font_tiny.render("C", True, COLORS['text'])
            text_rect = text.get_rect(center=carry_badge_pos)
            screen.blit(text, text_rect)

    def get_vertex_at_position(self, pos: Tuple[int, int]) -> Optional[str]:
        """Get vertex ID at mouse position"""
        for vertex_id, vertex_pos in self.vertex_positions.items():
            distance = math.sqrt((pos[0] - vertex_pos[0])**2 + (pos[1] - vertex_pos[1])**2)
            if distance < 35:  # Max radius
                return vertex_id
        return None


class Button:
    """Simple button class for UI"""

    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 action: str, enabled: bool = True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.enabled = enabled
        self.hovered = False

    def draw(self, screen: pygame.Surface):
        """Draw the button"""
        if not self.enabled:
            color = (150, 150, 150)
        elif self.hovered:
            color = COLORS['button_hover']
        else:
            color = COLORS['button']

        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, COLORS['wall'], self.rect, 2, border_radius=5)

        font = pygame.font.Font(None, 20)
        text = font.render(self.text, True, COLORS['button_text'])
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events, returns True if clicked"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.enabled:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class EvacuationVisualizer:
    """Main visualizer class with manual control support"""

    def __init__(self, width: int = 1200, height: int = 800, manual_mode: bool = False):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Emergency Evacuation Visualizer")

        self.clock = pygame.time.Clock()
        self.layout = LayoutVisualizer(width, height)
        self.manual_mode = manual_mode

        self.selected_firefighter: Optional[str] = None
        self.paused = manual_mode  # Start paused in manual mode
        self.tick_speed = 1  # Ticks per second in auto mode

        # Manual mode: queue actions instead of executing immediately
        self.pending_actions: Dict[str, List] = {}

        # Multi-floor support
        self.current_floor: Optional[int] = None  # None = show all floors
        self.num_floors = 1  # Will be updated when simulation loads

        # Buttons
        self.buttons: List[Button] = []
        self._create_buttons()

    def _create_buttons(self):
        """Create UI buttons"""
        button_y = self.height - 40

        self.buttons = [
            Button(10, button_y, 100, 30, "Play/Pause", "toggle_pause"),
            Button(120, button_y, 80, 30, "Step", "step"),
            Button(210, button_y, 80, 30, "Reset", "reset"),
            Button(300, button_y, 100, 30, "Speed -", "speed_down"),
            Button(410, button_y, 100, 30, "Speed +", "speed_up"),
        ]

        # Floor selector buttons (only show if multi-floor building)
        if self.num_floors > 1:
            floor_btn_x = 920
            self.buttons.extend([
                Button(floor_btn_x, button_y, 100, 30, "All Floors", "floor_all"),
                Button(floor_btn_x + 110, button_y, 80, 30, "Floor -", "floor_down"),
                Button(floor_btn_x + 200, button_y, 80, 30, "Floor +", "floor_up"),
            ])

        if self.manual_mode:
            self.buttons.extend([
                Button(520, button_y, 120, 30, "Instruct", "instruct"),
                Button(650, button_y, 120, 30, "Pick Up", "pick_up"),
                Button(780, button_y, 120, 30, "Drop Off", "drop_off"),
            ])

    def draw_fire_stats(self, screen: pygame.Surface, sim: Simulation):
        """Draw fire statistics panel on the right side"""
        panel_x = self.width - 300
        panel_y = 10
        panel_width = 290
        panel_height = 200

        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (255, 250, 240), panel_rect)
        pygame.draw.rect(screen, COLORS['wall'], panel_rect, 2)

        font_title = pygame.font.Font(None, 22)
        font_small = pygame.font.Font(None, 18)

        y = panel_y + 10

        # Title
        title = font_title.render("Fire Spread Info", True, (150, 0, 0))
        screen.blit(title, (panel_x + 10, y))
        y += 30

        # Count burned vertices/edges
        burned_rooms = sum(1 for v in sim.vertices.values() if v.is_burned and v.type == 'room')
        burned_edges = sum(1 for e in sim.edges.values() if not e.exists)
        total_rooms = sum(1 for v in sim.vertices.values() if v.type == 'room')
        total_edges = len(sim.edges)

        # Burned stats
        text = font_small.render(f"Burned rooms: {burned_rooms}/{total_rooms}", True, COLORS['text'])
        screen.blit(text, (panel_x + 10, y))
        y += 22

        text = font_small.render(f"Burned corridors: {burned_edges}/{total_edges}", True, COLORS['text'])
        screen.blit(text, (panel_x + 10, y))
        y += 22

        # Average smoke level
        total_smoke = sum(v.smoke_level for v in sim.vertices.values())
        avg_smoke = total_smoke / max(1, len(sim.vertices))
        text = font_small.render(f"Avg smoke level: {avg_smoke*100:.1f}%", True, COLORS['text'])
        screen.blit(text, (panel_x + 10, y))
        y += 22

        # Highest smoke room
        highest_smoke_vertex = max(sim.vertices.values(), key=lambda v: v.smoke_level)
        text = font_small.render(f"Max smoke: {highest_smoke_vertex.id}", True, COLORS['text'])
        screen.blit(text, (panel_x + 10, y))
        y += 18
        text = font_small.render(f"  {highest_smoke_vertex.smoke_level*100:.1f}%", True, (200, 0, 0))
        screen.blit(text, (panel_x + 20, y))
        y += 26

        # Burn rate info
        text = font_small.render(f"Tick duration: {sim.TICK_DURATION}s", True, COLORS['text'])
        screen.blit(text, (panel_x + 10, y))
        y += 20

        text = font_small.render(f"Movement speed: 2.0 m/s", True, COLORS['text'])
        screen.blit(text, (panel_x + 10, y))
        y += 26

        # Heat map legend (using non-linear scaling)
        legend_title = font_small.render("Fire Weight Factor (Rooms):", True, (150, 0, 0))
        screen.blit(legend_title, (panel_x + 10, y))
        y += 20

        # Legend colors - with power scaling (weight^2)
        legend_items = [
            ((255, 20, 20), "0.89-1.0: Critical (Red)"),
            ((255, 100, 0), "0.77-0.89: High (Orange-Red)"),
            ((255, 190, 0), "0.63-0.77: Med-High (Orange)"),
            ((255, 230, 50), "0.45-0.63: Medium (Yellow)"),
            ((255, 245, 150), "< 0.45: Low (Light)"),
        ]

        for color, label in legend_items:
            # Draw small square
            pygame.draw.rect(screen, color, (panel_x + 15, y - 4, 10, 10))
            # Draw label
            text = font_small.render(label, True, (80, 80, 80))
            screen.blit(text, (panel_x + 30, y - 6))
            y += 18

    def draw_stats(self, screen: pygame.Surface, sim: Simulation):
        """Draw statistics panel"""
        stats = sim.get_stats()

        panel_y = self.height - 140
        panel_height = 90

        # Draw panel background
        panel_rect = pygame.Rect(0, panel_y, self.width, panel_height)
        pygame.draw.rect(screen, (250, 250, 250), panel_rect)
        pygame.draw.line(screen, COLORS['wall'], (0, panel_y), (self.width, panel_y), 2)

        # Draw stats
        font = pygame.font.Font(None, 28)
        font_small = pygame.font.Font(None, 20)

        y = panel_y + 10

        # Row 1: Time and basic stats
        time_text = f"Time: {stats['time_minutes']:.1f} min ({stats['tick']} ticks)"
        text = font.render(time_text, True, COLORS['text'])
        screen.blit(text, (20, y))

        rescued_text = f"Rescued: {stats['rescued']}"
        text = font.render(rescued_text, True, (0, 150, 0))
        screen.blit(text, (300, y))

        dead_text = f"Dead: {stats['dead']}"
        text = font.render(dead_text, True, (200, 0, 0))
        screen.blit(text, (500, y))

        remaining_text = f"Remaining: {stats['remaining']}"
        text = font.render(remaining_text, True, (0, 100, 200))
        screen.blit(text, (700, y))

        # Row 2: Mode info and survival rate
        y += 35
        mode = "MANUAL" if self.manual_mode else "AUTO"
        state_text = "PAUSED" if self.paused else "RUNNING"
        survival_rate = (stats['rescued'] / max(1, stats['total_initial'])) * 100

        # Show pending actions count in manual mode
        pending_count = sum(len(actions) for actions in self.pending_actions.values())
        if self.manual_mode and pending_count > 0:
            mode_text = f"Mode: {mode} | {state_text} | Pending: {pending_count} actions | Survival: {survival_rate:.1f}%"
        else:
            mode_text = f"Mode: {mode} | {state_text} | Speed: {self.tick_speed} tps | Survival: {survival_rate:.1f}%"

        # Add floor info if multi-floor building
        if self.num_floors > 1:
            floor_text = f" | Floor: {self.current_floor if self.current_floor else 'All'}"
            mode_text += floor_text

        text = font_small.render(mode_text, True, COLORS['text'])
        screen.blit(text, (20, y))

        # Selected firefighter info
        if self.selected_firefighter and self.selected_firefighter in sim.firefighters:
            ff = sim.firefighters[self.selected_firefighter]
            ff_text = f"Selected: {self.selected_firefighter} at {ff.position}"
            text = font_small.render(ff_text, True, COLORS['firefighter'])
            screen.blit(text, (550, y))

    def run(self, sim: Simulation, model=None):
        """
        Main visualization loop.

        Args:
            sim: Simulation instance
            model: Optional AI model that provides actions (for auto mode)
        """
        if not self.layout.layout_calculated:
            self.layout.calculate_layout(sim)

        # Detect number of floors in the building
        floors = set()
        for vertex in sim.vertices.values():
            if hasattr(vertex, 'floor'):
                floors.add(vertex.floor)
        self.num_floors = len(floors) if floors else 1

        # Recreate buttons if multi-floor building detected
        if self.num_floors > 1:
            self._create_buttons()

        running = True
        ticks_since_update = 0

        while running:
            dt = self.clock.tick(60) / 1000.0  # 60 FPS

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Button handling
                for button in self.buttons:
                    if button.handle_event(event):
                        action = button.action

                        if action == "toggle_pause":
                            self.paused = not self.paused
                        elif action == "step":
                            # In manual mode, execute queued actions (or empty action to advance time)
                            if self.manual_mode:
                                actions_to_execute = self.pending_actions if self.pending_actions else {}
                                if actions_to_execute:
                                    print(f"Executing {sum(len(a) for a in actions_to_execute.values())} pending action(s)")
                                results = sim.update(actions_to_execute)
                                self.pending_actions = {}  # Clear queue
                                if results['rescued_this_tick'] > 0:
                                    print(f"  Rescued {results['rescued_this_tick']} people!")
                                if results['dead_this_tick'] > 0:
                                    print(f"  {results['dead_this_tick']} deaths this tick")
                            else:
                                self._do_simulation_step(sim, model)
                        elif action == "reset":
                            # Reset simulation (would need to store initial config)
                            print("Reset not implemented - restart program")
                        elif action == "speed_down":
                            self.tick_speed = max(1, self.tick_speed - 5)
                        elif action == "speed_up":
                            self.tick_speed = min(60, self.tick_speed + 5)
                        elif action == "floor_all":
                            self.current_floor = None  # Show all floors
                        elif action == "floor_down":
                            if self.current_floor is None:
                                self.current_floor = self.num_floors
                            else:
                                self.current_floor = max(1, self.current_floor - 1)
                        elif action == "floor_up":
                            if self.current_floor is None:
                                self.current_floor = 1
                            else:
                                self.current_floor = min(self.num_floors, self.current_floor + 1)
                        elif action == "instruct" and self.selected_firefighter:
                            self._manual_instruct(sim)
                        elif action == "pick_up" and self.selected_firefighter:
                            self._manual_pick_up(sim)
                        elif action == "drop_off" and self.selected_firefighter:
                            self._manual_drop_off(sim)

                # Manual controls
                if self.manual_mode:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        # First, check if we clicked on a vertex (for movement)
                        clicked_vertex = self.layout.get_vertex_at_position(event.pos)

                        # Find firefighters VERY close to click (direct firefighter selection)
                        clicked_firefighters = []
                        for ff_id in sim.firefighters.keys():
                            ff = sim.firefighters[ff_id]
                            if ff.position in self.layout.vertex_positions:
                                pos = self.layout.vertex_positions[ff.position]
                                distance = math.sqrt((event.pos[0] - pos[0])**2 +
                                                   (event.pos[1] - pos[1])**2)
                                # Smaller radius (15px) for direct firefighter clicks
                                if distance < 15:
                                    clicked_firefighters.append(ff_id)

                        # Priority 1: If clicked directly on firefighter icon, select/cycle
                        if clicked_firefighters:
                            if (self.selected_firefighter in clicked_firefighters and
                                len(clicked_firefighters) > 1):
                                # Cycle to next firefighter at this position
                                current_idx = clicked_firefighters.index(self.selected_firefighter)
                                next_idx = (current_idx + 1) % len(clicked_firefighters)
                                self.selected_firefighter = clicked_firefighters[next_idx]
                                print(f"Switched to {self.selected_firefighter} ({next_idx + 1}/{len(clicked_firefighters)} at this location)")
                            else:
                                # Select first firefighter at this position
                                self.selected_firefighter = clicked_firefighters[0]
                                if len(clicked_firefighters) > 1:
                                    print(f"Selected {self.selected_firefighter} (1/{len(clicked_firefighters)} at this location)")
                                else:
                                    print(f"Selected {self.selected_firefighter}")

                        # Priority 2: If clicked on a vertex and have selected FF
                        elif clicked_vertex and self.selected_firefighter:
                            # Move to clicked vertex
                            self._manual_move(sim, clicked_vertex)

                        # Priority 3: Nothing clicked, deselect
                        else:
                            pass  # Keep current selection

            # Auto-update simulation
            if not self.paused:
                ticks_since_update += dt * self.tick_speed

                if ticks_since_update >= 1.0:
                    self._do_simulation_step(sim, model)
                    ticks_since_update = 0

            # Render
            self.screen.fill(COLORS['background'])

            # Draw edges (filter by floor if selected)
            for edge_id in sim.edges.keys():
                edge = sim.edges[edge_id]
                vertex_a = sim.vertices.get(edge.vertex_a)
                vertex_b = sim.vertices.get(edge.vertex_b)

                # Skip edge if floor filter active and edge vertices don't match
                if self.current_floor is not None and vertex_a and vertex_b:
                    vertex_a_floor = getattr(vertex_a, 'floor', 1)
                    vertex_b_floor = getattr(vertex_b, 'floor', 1)
                    # Only draw if both endpoints are on the current floor
                    if vertex_a_floor != self.current_floor or vertex_b_floor != self.current_floor:
                        continue

                self.layout.draw_edge(self.screen, edge_id, sim)

            # Draw vertices (with fog of war in manual mode)
            # Collect all visited vertices by any firefighter
            all_visited = set()
            if self.manual_mode:
                for ff in sim.firefighters.values():
                    all_visited.update(ff.visited_vertices)

            for vertex_id in sim.vertices.keys():
                vertex = sim.vertices[vertex_id]

                # Skip vertex if floor filter active and doesn't match
                if self.current_floor is not None:
                    vertex_floor = getattr(vertex, 'floor', 1)
                    if vertex_floor != self.current_floor:
                        continue

                self.layout.draw_vertex(
                    self.screen, vertex_id, sim,
                    show_all_occupants=not self.manual_mode,
                    visited_vertices=all_visited
                )

            # Draw firefighters (filter by floor if selected)
            for ff_id in sim.firefighters.keys():
                ff = sim.firefighters[ff_id]

                # Skip firefighter if floor filter active and doesn't match
                if self.current_floor is not None:
                    ff_vertex = sim.vertices.get(ff.position)
                    if ff_vertex:
                        ff_floor = getattr(ff_vertex, 'floor', 1)
                        if ff_floor != self.current_floor:
                            continue

                selected = (ff_id == self.selected_firefighter)
                self.layout.draw_firefighter(self.screen, ff_id, sim, selected)

            # Draw stats
            self.draw_stats(self.screen, sim)

            # Draw fire statistics panel
            self.draw_fire_stats(self.screen, sim)

            # Draw buttons
            for button in self.buttons:
                button.draw(self.screen)

            pygame.display.flip()

        pygame.quit()

    def _do_simulation_step(self, sim: Simulation, model=None):
        """Execute one simulation step"""
        if model:
            # AI model provides actions
            state = sim.read()
            actions = model.get_actions(state)
        else:
            # No actions in manual mode unless manually triggered
            actions = {}

        results = sim.update(actions)

        # Debug output for rescues
        if results['rescued_this_tick'] > 0:
            print(f"Tick {results['tick']}: Rescued {results['rescued_this_tick']} people! Total rescued: {sim.rescued_count}")

        if results['dead_this_tick'] > 0:
            print(f"Tick {results['tick']}: {results['dead_this_tick']} deaths. Total dead: {sim.dead_count}")

    def _manual_move(self, sim: Simulation, target_vertex: str):
        """Queue move action for selected firefighter (executed on 'step')"""
        if not self.selected_firefighter:
            return

        ff = sim.firefighters[self.selected_firefighter]
        neighbors = [n for n, _ in sim.adjacency[ff.position]]

        if target_vertex in neighbors or target_vertex == ff.position:
            # Queue the action instead of executing immediately
            if self.selected_firefighter not in self.pending_actions:
                self.pending_actions[self.selected_firefighter] = []

            self.pending_actions[self.selected_firefighter].append({
                'type': 'move',
                'target': target_vertex
            })
            print(f"Queued: Move {self.selected_firefighter} to {target_vertex} (click 'Step' to execute)")

    def _manual_instruct(self, sim: Simulation):
        """Queue instruct action for selected firefighter (executed on 'step')"""
        if not self.selected_firefighter:
            return

        ff = sim.firefighters[self.selected_firefighter]
        current_vertex = sim.vertices[ff.position]

        if current_vertex.capable_count == 0:
            print(f"No capable people at {ff.position} to instruct")
            return

        # Queue the action
        if self.selected_firefighter not in self.pending_actions:
            self.pending_actions[self.selected_firefighter] = []

        self.pending_actions[self.selected_firefighter].append({
            'type': 'instruct'
        })
        print(f"Queued: Instruct {current_vertex.capable_count} capable people at {ff.position} (click 'Step' to execute)")

    def _manual_pick_up(self, sim: Simulation):
        """Queue pick_up_incapable action for selected firefighter (executed on 'step')"""
        if not self.selected_firefighter:
            return

        ff = sim.firefighters[self.selected_firefighter]
        current_vertex = sim.vertices[ff.position]

        if ff.carrying_incapable >= 1:
            print(f"{self.selected_firefighter} is already carrying someone")
            return

        if current_vertex.incapable_count == 0:
            print(f"No incapable people at {ff.position} to pick up")
            return

        # Queue the action
        if self.selected_firefighter not in self.pending_actions:
            self.pending_actions[self.selected_firefighter] = []

        self.pending_actions[self.selected_firefighter].append({
            'type': 'pick_up_incapable'
        })
        print(f"Queued: Pick up incapable person at {ff.position} (click 'Step' to execute)")

    def _manual_drop_off(self, sim: Simulation):
        """Queue drop_off action for selected firefighter (executed on 'step')"""
        if not self.selected_firefighter:
            return

        ff = sim.firefighters[self.selected_firefighter]

        if ff.carrying_incapable == 0:
            print(f"{self.selected_firefighter} is not carrying anyone")
            return

        # Queue the action
        if self.selected_firefighter not in self.pending_actions:
            self.pending_actions[self.selected_firefighter] = []

        self.pending_actions[self.selected_firefighter].append({
            'type': 'drop_off'
        })
        print(f"Queued: Drop off carried person at {ff.position} (click 'Step' to execute)")


def visualize_layout(config_file: str):
    """Visualize just the building layout (static)"""
    with open(config_file, 'r') as f:
        config = json.load(f)

    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin=config.get('fire_params', {}).get('origin', 'office_bottom_center'),
        seed=42
    )

    viz = EvacuationVisualizer(manual_mode=False)
    viz.run(sim)


def visualize_manual(config_file: str):
    """Run visualizer in manual control mode"""
    with open(config_file, 'r') as f:
        config = json.load(f)

    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin=config.get('fire_params', {}).get('origin', 'office_bottom_center'),
        seed=42
    )

    viz = EvacuationVisualizer(manual_mode=True)
    print("\n" + "="*60)
    print("MANUAL CONTROL MODE")
    print("="*60)
    print("Controls:")
    print("  - Click on firefighters to select them")
    print("  - Click on adjacent vertices to move")
    print("  - Use 'Pick Up' button to collect occupants")
    print("  - Use 'Drop Off' button at exits to rescue")
    print("  - Play/Pause to control time")
    print("  - Step to advance one tick")
    print("="*60 + "\n")

    viz.run(sim)


def visualize_auto(config_file: str, model=None):
    """Run visualizer with AI model (auto mode)"""
    with open(config_file, 'r') as f:
        config = json.load(f)

    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin=config.get('fire_params', {}).get('origin', 'office_bottom_center'),
        seed=42
    )

    viz = EvacuationVisualizer(manual_mode=False)
    viz.run(sim, model)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'manual':
        visualize_manual('config_example.json')
    else:
        visualize_auto('config_example.json')
