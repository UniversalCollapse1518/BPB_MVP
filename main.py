import pygame
import sys
import json
from enum import Enum
from typing import List, Optional, Dict, Tuple
import math

# --- Constants ---
# These are global values that define the size and appearance of the game window.
# Using constants makes the code easier to read and modify.
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
GRID_SIZE = 40
BG_COLOR = (255, 255, 255)
FONT_COLOR = (10, 10, 10)
GRID_LINE_COLOR = (200, 200, 200)
INVALID_PLACEMENT_COLOR = (255, 0, 0, 100) # Semi-transparent red

# Backpack dimensions in grid units and screen pixels
BACKPACK_COLS = 9
BACKPACK_ROWS = 7
BACKPACK_X, BACKPACK_Y = 50, 50

# --- NEW SCALABLE LAYOUT ---
# Defines the positions and sizes of the UI panels on the right side.
PANEL_START_X = BACKPACK_X + (BACKPACK_COLS * GRID_SIZE) + 50
PANEL_Y = 50
PANEL_HEIGHT = 600

INFO_PANEL_X = PANEL_START_X
INFO_PANEL_WIDTH = 250

SHOP_X = INFO_PANEL_X + INFO_PANEL_WIDTH + 20
SHOP_WIDTH = 200

# --- Enums for Item Properties ---
# Enums (Enumerations) are used to create a set of named constants. This prevents typos
# (e.g., writing "OCCUPIIED" instead of "OCCUPIED") and makes the code more readable.
class GridType(Enum): EMPTY, OCCUPIED, STAR_A, STAR_B, STAR_C = 0, 1, 2, 3, 4
class Rarity(Enum): COMMON, RARE, EPIC, LEGENDARY, GODLY, UNIQUE = "Common", "Rare", "Epic", "Legendary", "Godly", "Unique"
class ItemClass(Enum): NEUTRAL, RANGER, REAPER, BERSERKER, PYROMANCER, MAGE, ADVENTURER = "Neutral", "Ranger", "Reaper", "Berserker", "Pyromancer", "Mage", "Adventurer"
class Element(Enum): MELEE, RANGED, MAGIC = "Melee", "Ranged", "Magic"
class ItemType(Enum): WEAPON, SHIELD, PET = "Weapon", "Shield", "Pet"

# --- Rarity and Star Colors ---
# Dictionaries that map an Enum value to a specific color. This keeps our styling centralized.
RARITY_BORDER_COLORS = { Rarity.COMMON: (150, 150, 150), Rarity.RARE: (0, 100, 255), Rarity.EPIC: (138, 43, 226), Rarity.LEGENDARY: (255, 165, 0), Rarity.GODLY: (255, 215, 0), Rarity.UNIQUE: (255, 20, 147) }
STAR_SHAPE_COLORS = { GridType.STAR_A: (255, 215, 0), GridType.STAR_B: (50, 205, 50), GridType.STAR_C: (148, 0, 211) }

# --- Item Class ---
# This class represents a single item in the game. It holds all its properties and handles its own drawing logic.
class Item(pygame.sprite.Sprite):
    # The __init__ method is the constructor for the class. It's called whenever a new Item is created.
    # Input: All the properties of the item, loaded from the JSON file.
    def __init__(self, x: int, y: int, name: str, rarity: Rarity,
                 item_class: ItemClass, elements: List[Element], types: List[ItemType],
                 shape_matrix: List[List[GridType]]):
        super().__init__()
        # Store all the item's core properties.
        self.name = name
        self.rarity = rarity
        self.item_class = item_class
        self.elements = elements
        self.types = types
        self.shape_matrix = shape_matrix
        
        # Calculate the item's size in grid units from its matrix.
        self.grid_width = len(shape_matrix[0]) if shape_matrix else 0
        self.grid_height = len(shape_matrix)
        
        # Create the visual representation of the item's body.
        self.body_image = self.create_body_surface()
        # The 'rect' is a Pygame object that stores the position and size of the item on the screen.
        self.rect = self.body_image.get_rect(topleft=(x, y))
        self.base_y = y # Store the original y-position for scrolling calculations.
        
        # State variables
        self.dragging = False
        self.activated_stars = {GridType.STAR_A: 0, GridType.STAR_B: 0, GridType.STAR_C: 0}

    # This method creates the visual for the item's physical body and its name.
    # Input: None (it uses the item's own properties).
    # Output: A `pygame.Surface` object, which is essentially an image of the item's body.
    def create_body_surface(self):
        width_px, height_px = self.grid_width * GRID_SIZE, self.grid_height * GRID_SIZE
        surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA) # SRCALPHA allows for transparency.
        
        occupied_coords = []
        # First, draw all the physical (OCCUPIED) cells.
        for r, row in enumerate(self.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED:
                    occupied_coords.append((c, r))
                    pygame.draw.rect(surface, (200, 200, 200), (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE))
                    pygame.draw.rect(surface, RARITY_BORDER_COLORS[self.rarity], (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE), 2)
        
        # If the item has a physical body, calculate its geometric center to place the name.
        if occupied_coords:
            min_c = min(c for c, r in occupied_coords)
            max_c = max(c for c, r in occupied_coords)
            min_r = min(r for c, r in occupied_coords)
            max_r = max(r for c, r in occupied_coords)
            
            center_x = (min_c + max_c + 1) * GRID_SIZE / 2
            center_y = (min_r + max_r + 1) * GRID_SIZE / 2
            
            font = pygame.font.SysFont(None, 20)
            name_text = (self.name[:4] + '..') if len(self.name) > 6 else self.name
            text_surf = font.render(name_text, True, FONT_COLOR)
            surface.blit(text_surf, text_surf.get_rect(center=(center_x, center_y)))
        return surface

    # This method draws the star shapes. It's separate from the body to allow for layering.
    # Input: The main `screen` to draw on, and the `top_left_pos` of the item.
    # Output: None (it draws directly onto the screen).
    def draw_stars(self, screen, top_left_pos):
        for r, row in enumerate(self.shape_matrix):
            for c, cell in enumerate(row):
                if cell in STAR_SHAPE_COLORS:
                    cx, cy = top_left_pos[0] + c*GRID_SIZE + GRID_SIZE//2, top_left_pos[1] + r*GRID_SIZE + GRID_SIZE//2
                    color = STAR_SHAPE_COLORS[cell]
                    # Each star type has its own polygon points.
                    if cell == GridType.STAR_A:
                        pts = []
                        for i in range(5):
                            for ang in [18, 54]:
                                rad = math.radians(ang + i*72); scale = GRID_SIZE/2 if ang == 18 else GRID_SIZE/4
                                pts.append((cx + scale*math.cos(rad), cy + scale*math.sin(rad)))
                        pygame.draw.polygon(screen, color, pts)
                    elif cell == GridType.STAR_B: pygame.draw.polygon(screen, color, [(cx,cy-GRID_SIZE*0.4), (cx+GRID_SIZE*0.4,cy), (cx,cy+GRID_SIZE*0.4), (cx-GRID_SIZE*0.4,cy)])
                    elif cell == GridType.STAR_C: pygame.draw.polygon(screen, color, [(cx,cy-GRID_SIZE*0.35), (cx-GRID_SIZE*0.35,cy+GRID_SIZE*0.35), (cx+GRID_SIZE*0.35,cy+GRID_SIZE*0.35)])

    # This method checks if the mouse is currently over a physical part of the item.
    # Input: The current `mouse_pos`, and the item's `current_pos` on the screen.
    # Output: `True` if the mouse is on an OCCUPIED cell, `False` otherwise.
    def is_mouse_over_body(self, mouse_pos, current_pos):
        # We perform a precise check by iterating through each physical cell.
        for r, row in enumerate(self.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED:
                    cell_rect = pygame.Rect(current_pos[0] + c * GRID_SIZE, current_pos[1] + r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    if cell_rect.collidepoint(mouse_pos):
                        return True
        return False
        
    # This method rotates the item's data 90 degrees clockwise.
    # Input: None.
    # Output: None (it modifies the item's own `shape_matrix` and `body_image`).
    def rotate(self):
        # This is a standard Python trick for rotating a 2D list.
        self.shape_matrix = [list(row)[::-1] for row in zip(*self.shape_matrix)]
        # Update the dimensions and recreate the visual surface.
        self.grid_height, self.grid_width = len(self.shape_matrix), len(self.shape_matrix[0])
        self.body_image = self.create_body_surface()

# --- Calculation Engine ---
# This class encapsulates all the logic for analyzing the backpack's contents.
class CalculationEngine:
    # This is the main method of the engine.
    # Input: The `placed_items` dictionary, which contains all items in the backpack and their positions.
    # Output: None (it modifies the `activated_stars` attribute of each item in the `placed_items` dict directly).
    def run(self, placed_items: Dict[Tuple[int, int], Item]):
        # --- Pass 1: Build the Occupancy Grid ---
        # Create a 9x7 grid representing the backpack, initially empty (filled with None).
        occupancy_grid: List[List[Optional[Item]]] = [[None for _ in range(BACKPACK_COLS)] for _ in range(BACKPACK_ROWS)]
        # For each item on the board, fill in the grid cells with a reference to the item itself.
        for (gx, gy), item in placed_items.items():
            for r, row in enumerate(item.shape_matrix):
                for c, cell_type in enumerate(row):
                    if cell_type == GridType.OCCUPIED:
                        abs_x, abs_y = gx + c, gy + r
                        if 0 <= abs_y < BACKPACK_ROWS and 0 <= abs_x < BACKPACK_COLS: 
                            occupancy_grid[abs_y][abs_x] = item
        
        # --- Pass 2: Calculate Star Activations ---
        # Now, iterate through each placed item again to see if its stars are activated.
        for (gx, gy), source_item in placed_items.items():
            source_item.activated_stars = {GridType.STAR_A: 0, GridType.STAR_B: 0, GridType.STAR_C: 0} # Reset counts
            # This dictionary of sets is crucial for the "count once" rule.
            triggered_by = {GridType.STAR_A: set(), GridType.STAR_B: set(), GridType.STAR_C: set()}

            # Check each cell in the item's shape matrix.
            for r, row in enumerate(source_item.shape_matrix):
                for c, cell_type in enumerate(row):
                    if cell_type in triggered_by: # Is this cell a star?
                        abs_x, abs_y = gx + c, gy + r
                        # Is the star's position inside the backpack?
                        if 0 <= abs_y < BACKPACK_ROWS and 0 <= abs_x < BACKPACK_COLS:
                            # Look up what item is on this star cell in our master grid.
                            target_item = occupancy_grid[abs_y][abs_x]
                            # If there is an item, it's not the same item, and it hasn't already triggered this star type...
                            if target_item and target_item is not source_item and target_item not in triggered_by[cell_type]:
                                # Then it's a valid activation!
                                source_item.activated_stars[cell_type] += 1
                                # Add the item to the set to prevent it from counting again for this star type.
                                triggered_by[cell_type].add(target_item)

# --- Data Loading and Helper Functions ---
# This function reads the item data from the JSON file at the start of the game.
# Input: The file path to the JSON file.
# Output: A list of `Item` objects for the shop.
def load_items_from_file(filepath: str) -> List[Item]:
    items = []
    try:
        with open(filepath, 'r') as f: data = json.load(f)
        y_offset = 0
        for item_data in data.values():
            # This part parses the string data from JSON and converts it into our Enum types.
            item = Item(SHOP_X + 10, PANEL_Y + 10 + y_offset, item_data['name'], Rarity[item_data['rarity']], 
                        ItemClass[item_data['item_class']], [Element[e] for e in item_data.get('elements', [])], 
                        [ItemType[t] for t in item_data.get('types', [])], [[GridType(c) for c in r] for r in item_data['shape_matrix']])
            items.append(item)
            y_offset += item.rect.height + 10
    except Exception as e: print(f"Error loading items: {e}")
    return items

# This function checks if an item can be legally placed on the backpack grid.
# Input: The `item` to place, its target `gx, gy` grid coordinates, and the dictionary of already `placed_items`.
# Output: `True` if the placement is valid, `False` otherwise.
def is_placement_valid(item, gx, gy, items_dict):
    occupied_cells = set()
    # First, build a set of all currently occupied grid cells.
    for (px, py), p_item in items_dict.items():
        for r, row in enumerate(p_item.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED: occupied.add((px + c, py + r))
    # Then, check each physical part of the new item.
    for r, row in enumerate(item.shape_matrix):
        for c, cell in enumerate(row):
            if cell == GridType.OCCUPIED:
                ax, ay = gx + c, gy + r
                # Is it out of bounds?
                if not (0 <= ax < BACKPACK_COLS and 0 <= ay < BACKPACK_ROWS): return False
                # Is it colliding with another item?
                if (ax, ay) in occupied: return False
    return True

# --- Main Game Function ---
# This is the entry point of the program. It initializes Pygame, creates all objects, and runs the main game loop.
def game_loop():
    pygame.init() # Starts Pygame
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Backpack Battles - Final Bug Fixes")
    clock = pygame.time.Clock() # Used to control the frame rate.

    # --- Initialization ---
    items_in_shop = load_items_from_file('items.json')
    placed_items = {}
    selected_item = None
    engine = CalculationEngine()
    
    font_large, font_small = pygame.font.SysFont(None, 36), pygame.font.SysFont(None, 28)
    calc_button = pygame.Rect(PANEL_START_X, 660, INFO_PANEL_WIDTH + SHOP_WIDTH + 20, 30)
    shop_area_rect = pygame.Rect(SHOP_X, PANEL_Y, SHOP_WIDTH, PANEL_HEIGHT)
    info_panel_rect = pygame.Rect(INFO_PANEL_X, PANEL_Y, INFO_PANEL_WIDTH, PANEL_HEIGHT)
    
    shop_scroll_y, info_scroll_y = 0, 0
    total_shop_height = sum(item.rect.height + 10 for item in items_in_shop) if items_in_shop else 0
    
    # --- Main Loop ---
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos() # Get mouse position once per frame for efficiency.
        
        # --- Event Handling ---
        # This loop processes all user input (mouse clicks, keyboard presses, etc.).
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle scrolling with the mouse wheel.
                if event.button == 4: # Scroll Up
                    if shop_area_rect.collidepoint(mouse_pos): shop_scroll_y = max(0, shop_scroll_y - 20)
                    if info_panel_rect.collidepoint(mouse_pos): info_scroll_y = max(0, info_scroll_y - 20)
                elif event.button == 5: # Scroll Down
                    if shop_area_rect.collidepoint(mouse_pos):
                        max_scroll = max(0, total_shop_height - shop_area_rect.height)
                        shop_scroll_y = min(max_scroll, shop_scroll_y + 20)
                    if info_panel_rect.collidepoint(mouse_pos):
                        max_scroll = max(0, 50 + len(placed_items) * 60 - info_panel_rect.height)
                        info_scroll_y = min(max_scroll, info_scroll_y + 20)
                # Handle rotation with a right-click.
                elif event.button == 3 and selected_item and selected_item.dragging:
                    rx, ry = mouse_pos[0]-selected_item.rect.x, mouse_pos[1]-selected_item.rect.y
                    pc, pr = rx // GRID_SIZE, ry // GRID_SIZE
                    ogh = selected_item.grid_height
                    selected_item.rotate() 
                    npc, npr = ogh-1-pr, pc
                    npx_off, npy_off = npc*GRID_SIZE, npr*GRID_SIZE
                    nr = selected_item.body_image.get_rect(x=mouse_pos[0]-npx_off, y=mouse_pos[1]-npy_off)
                    selected_item.rect, offset_x, offset_y = nr, nr.x-mouse_pos[0], nr.y-mouse_pos[1]
                # Handle pickup/clicking with a left-click.
                elif event.button == 1:
                    clicked_item_found = False
                    # We check the backpack items in reverse to pick the "topmost" one first.
                    for pos, item in reversed(list(placed_items.items())):
                        item_pos_on_screen = (BACKPACK_X + pos[0] * GRID_SIZE, BACKPACK_Y + pos[1] * GRID_SIZE)
                        if item.is_mouse_over_body(mouse_pos, item_pos_on_screen):
                            selected_item = item
                            offset_x = item_pos_on_screen[0] - mouse_pos[0]
                            offset_y = item_pos_on_screen[1] - mouse_pos[1]
                            selected_item.dragging = True
                            selected_item.rect.topleft = item_pos_on_screen
                            del placed_items[pos]
                            clicked_item_found = True
                            break 
                    
                    if not clicked_item_found:
                        for item_t in items_in_shop:
                            current_item_pos = item_t.rect.topleft
                            if item_t.is_mouse_over_body(mouse_pos, current_item_pos):
                                # Create a clone of the shop item to drag.
                                selected_item = Item(item_t.rect.x, item_t.rect.y, item_t.name, item_t.rarity, item_t.item_class, item_t.elements, item_t.types, item_t.shape_matrix)
                                selected_item.dragging = True
                                offset_x, offset_y = item_t.rect.x - mouse_pos[0], item_t.rect.y - mouse_pos[1]
                                break
                    
                    if calc_button.collidepoint(mouse_pos): 
                        engine.run(placed_items)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and selected_item:
                    selected_item.dragging = False
                    gx, gy = round((selected_item.rect.left-BACKPACK_X)/GRID_SIZE), round((selected_item.rect.top-BACKPACK_Y)/GRID_SIZE)
                    if is_placement_valid(selected_item, gx, gy, placed_items): 
                        placed_items[(gx, gy)] = selected_item
                    selected_item = None # The item is either placed or discarded.
            
            elif event.type == pygame.MOUSEMOTION:
                if selected_item and selected_item.dragging:
                    selected_item.rect.x, selected_item.rect.y = mouse_pos[0]+offset_x, mouse_pos[1]+offset_y
        
        # --- Drawing ---
        # This section happens every single frame to draw everything on the screen.
        screen.fill(BG_COLOR) # Clear the screen first.
        
        # Draw the static UI elements.
        pygame.draw.rect(screen, (230,230,230), pygame.Rect(BACKPACK_X, BACKPACK_Y, BACKPACK_COLS*GRID_SIZE, BACKPACK_ROWS*GRID_SIZE))
        pygame.draw.rect(screen, (240,240,240), shop_area_rect, 2); pygame.draw.rect(screen, (220,220,220), info_panel_rect); pygame.draw.rect(screen, (180,180,180), info_panel_rect, 2)
        for x in range(BACKPACK_X, BACKPACK_X+BACKPACK_COLS*GRID_SIZE+1, GRID_SIZE): pygame.draw.line(screen, GRID_LINE_COLOR, (x, BACKPACK_Y), (x, BACKPACK_Y+BACKPACK_ROWS*GRID_SIZE))
        for y in range(BACKPACK_Y, BACKPACK_Y+BACKPACK_ROWS*GRID_SIZE+1, GRID_SIZE): pygame.draw.line(screen, GRID_LINE_COLOR, (BACKPACK_X, y), (BACKPACK_X+BACKPACK_COLS*GRID_SIZE, y))

        # --- Draw Scrollable Info Panel ---
        screen.set_clip(info_panel_rect) # Only draw within the bounds of this panel.
        screen.blit(font_large.render("Backpack Contents", True, FONT_COLOR), (info_panel_rect.x+10, info_panel_rect.y+10-info_scroll_y))
        y_off = 50
        for item in placed_items.values():
            star_txt = f"A:{item.activated_stars[GridType.STAR_A]} B:{item.activated_stars[GridType.STAR_B]} C:{item.activated_stars[GridType.STAR_C]}"
            screen.blit(font_small.render(f"- {item.name}", True, FONT_COLOR), (info_panel_rect.x+15, info_panel_rect.y+y_off-info_scroll_y))
            screen.blit(font_small.render(star_txt, True, (60,60,60)), (info_panel_rect.x+25, info_panel_rect.y+y_off+25-info_scroll_y))
            y_off += 60
        screen.set_clip(None) # Reset clipping to draw on the whole screen again.
        
        # --- Reworked Drawing Passes for Bug Fixes ---
        all_items_to_draw = []
        for pos, item in placed_items.items():
            all_items_to_draw.append((item, (BACKPACK_X + pos[0] * GRID_SIZE, BACKPACK_Y + pos[1] * GRID_SIZE)))
        for item in items_in_shop:
            item.rect.y = item.base_y - shop_scroll_y
            all_items_to_draw.append((item, item.rect.topleft))

        # Pass 1: Draw all bodies
        for item, pos in all_items_to_draw:
            if shop_area_rect.colliderect(pygame.Rect(pos, item.body_image.get_size())) or info_panel_rect.x > pos[0]:
                 screen.blit(item.body_image, pos)

        # Pass 2: Draw all stars on hover
        for item, pos in all_items_to_draw:
            if item.is_mouse_over_body(mouse_pos, pos):
                # We need to clip drawing to the shop area to prevent stars from appearing outside it.
                is_in_shop = shop_area_rect.colliderect(pygame.Rect(pos, item.body_image.get_size()))
                if is_in_shop: screen.set_clip(shop_area_rect)
                item.draw_stars(screen, pos)
                if is_in_shop: screen.set_clip(None)
        
        # Pass 3: Draw the item currently being dragged
        if selected_item and selected_item.dragging:
            screen.blit(selected_item.body_image, selected_item.rect)
            selected_item.draw_stars(screen, selected_item.rect.topleft) # Always show stars on dragged item
            gx, gy = round((selected_item.rect.left-BACKPACK_X)/GRID_SIZE), round((selected_item.rect.top-BACKPACK_Y)/GRID_SIZE)
            if not is_placement_valid(selected_item, gx, gy, placed_items):
                tint = pygame.Surface(selected_item.rect.size, pygame.SRCALPHA); tint.fill(INVALID_PLACEMENT_COLOR)
                screen.blit(tint, selected_item.rect.topleft)

        pygame.draw.rect(screen, (100, 200, 100), calc_button)
        screen.blit(font_small.render("Calculate", True, FONT_COLOR), calc_button.inflate(-10,-10))
        
        pygame.display.flip() # Update the full display screen to show everything that was drawn.
        clock.tick(60) # Limit the game to 60 frames per second.
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__": 
    game_loop()

