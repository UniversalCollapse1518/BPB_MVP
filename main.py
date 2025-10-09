# =============================================================================
# --- IMPORTS ---
# =============================================================================
import pygame  # The core library for all graphics, input, and game loop management.
import sys     # Used for system-level operations, specifically to exit the application cleanly.
import json    # Used to load the item data from the items.json file.
from enum import Enum  # Allows for the creation of enumerated types (like Rarity, ItemClass) for clear, readable code.
from typing import List, Optional, Dict, Tuple  # Provides type hints for better code readability and error checking.
import math    # Used for mathematical calculations, specifically for drawing the star shapes.
# --- NEW: Import for logging timestamp ---
from datetime import datetime # Used in the log_event function to timestamp logs.

# --- MODIFICATION: Import from the new shared definitions file ---
# This imports the custom Enum definitions from a separate file, allowing both
# main.py and editor.py to use the same set of definitions without duplication.
from definitions import GridType, Rarity, ItemClass, Element, ItemType

# =============================================================================
# --- CONSTANTS ---
# =============================================================================
# These are global, unchanging values used throughout the application for
# configuration and styling, making the code easier to modify.

# -- Screen and Grid Configuration --
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
GRID_SIZE = 40  # The size of one grid cell in pixels. All item rendering is based on this.

# -- UI Layout Coordinates and Dimensions --
# Defines the position and size of the main UI components: the backpack,
# the item shop, and the information panel.
BACKPACK_COLS, BACKPACK_ROWS = 9, 7
BACKPACK_X, BACKPACK_Y = 50, 50
PANEL_START_X = BACKPACK_X + (BACKPACK_COLS * GRID_SIZE) + 50
PANEL_Y = 50
PANEL_HEIGHT = 550
INFO_PANEL_X, INFO_PANEL_WIDTH = PANEL_START_X, 350
SHOP_X, SHOP_WIDTH = INFO_PANEL_X + INFO_PANEL_WIDTH + 20, 200

# -- Color Definitions --
BG_COLOR = (255, 255, 255)
FONT_COLOR = (10, 10, 10)
GRID_LINE_COLOR = (200, 200, 200)
INVALID_PLACEMENT_COLOR = (255, 0, 0, 100) # Semi-transparent red for the invalid placement overlay.

# Dictionaries mapping Enum members to specific colors for rendering.
RARITY_BORDER_COLORS = {
    Rarity.COMMON: (150, 150, 150),
    Rarity.RARE: (0, 100, 255),
    Rarity.EPIC: (138, 43, 226),
    Rarity.LEGENDARY: (255, 165, 0),
    Rarity.GODLY: (255, 215, 0),
    Rarity.UNIQUE: (255, 20, 147)
}
STAR_SHAPE_COLORS = {
    GridType.STAR_A: (255, 215, 0),
    GridType.STAR_B: (50, 205, 50),
    GridType.STAR_C: (148, 0, 211)
}


# =============================================================================
# --- ITEM CLASS ---
# =============================================================================
class Item(pygame.sprite.Sprite):
    """
    Represents a single item in the game.
    This class holds all data for an item (name, shape, score, etc.) and handles
    its visual representation and user interactions like rotation.
    """
    def __init__(self, x: int, y: int, name: str, rarity: Rarity,
                 item_class: ItemClass, elements: List[Element], types: List[ItemType],
                 shape_matrix: List[List[GridType]], base_score: int, star_effects: dict):
        """
        Initializes an Item object.

        Args:
            x (int): The initial x-coordinate (in pixels) on the screen.
            y (int): The initial y-coordinate (in pixels) on the screen.
            name (str): The display name of the item.
            rarity (Rarity): The rarity of the item (e.g., COMMON, RARE).
            item_class (ItemClass): The class of the item (e.g., RANGER, MAGE).
            elements (List[Element]): A list of elements associated with the item (e.g., FIRE, MAGIC).
            types (List[ItemType]): A list of types for the item (e.g., WEAPON, FOOD).
            shape_matrix (List[List[GridType]]): A 2D list representing the item's shape and star locations.
            base_score (int): The item's intrinsic score before any modifiers.
            star_effects (dict): A dictionary defining the effects of its stars.
        """
        super().__init__()
        # --- Core Item Properties from JSON ---
        self.name = name
        self.rarity = rarity
        self.item_class = item_class
        self.elements = elements
        self.types = types
        self.shape_matrix = shape_matrix
        self.base_score = base_score
        self.star_effects = star_effects

        # --- Derived and State Properties ---
        self.grid_width = len(shape_matrix[0]) if shape_matrix else 0
        self.grid_height = len(shape_matrix) if shape_matrix else 0
        self.body_image = self.create_body_surface() # The pre-rendered visual of the item's body.
        self.rect = self.body_image.get_rect(topleft=(x, y)) # The Pygame Rect object for positioning and collision.
        self.base_y = y # Stores the original y-position in the shop for scrolling.
        self.dragging = False # A flag to indicate if the user is currently moving this item.

        # --- Calculation-Related Properties ---
        # These are reset and recalculated by the CalculationEngine.
        self.final_score = 0
        self.score_modifiers = [] # A list of strings describing score changes (e.g., "+2.0 from Banana").
        self.activated_stars = {GridType.STAR_A: 0, GridType.STAR_B: 0, GridType.STAR_C: 0} # Counts how many stars are activated.
        self.occupying_stars = [] # Stores which stars from other items are affecting this one.

    def create_body_surface(self) -> pygame.Surface:
        """
        Creates a Pygame Surface for the item's main body (occupied cells).
        This method pre-renders the item's shape, border, and name onto a
        transparent surface, which is efficient for drawing (blitting).

        Returns:
            pygame.Surface: A transparent surface with the item's body drawn on it.
        """
        width_px, height_px = self.grid_width * GRID_SIZE, self.grid_height * GRID_SIZE
        surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA) # Use SRCALPHA for transparency.

        # Find all coordinates that are part of the item's body.
        occupied_coords = [(c, r) for r, row in enumerate(self.shape_matrix) for c, cell in enumerate(row) if cell == GridType.OCCUPIED]
        
        if occupied_coords:
            # Draw the filled rectangle and rarity border for each occupied cell.
            for c, r in occupied_coords:
                pygame.draw.rect(surface, (200, 200, 200), (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE))
                pygame.draw.rect(surface, RARITY_BORDER_COLORS[self.rarity], (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE), 2)
            
            # To center the name, find the bounding box of the occupied cells.
            min_c, max_c = min(c for c,r in occupied_coords), max(c for c,r in occupied_coords)
            min_r, max_r = min(r for c,r in occupied_coords), max(r for c,r in occupied_coords)
            center_x = (min_c + max_c + 1) * GRID_SIZE / 2
            center_y = (min_r + max_r + 1) * GRID_SIZE / 2
            
            # Render and blit the item's name onto the surface.
            font = pygame.font.SysFont(None, 20)
            name_text = (self.name[:4] + '..') if len(self.name) > 6 else self.name
            text_surf = font.render(name_text, True, FONT_COLOR)
            surface.blit(text_surf, text_surf.get_rect(center=(center_x, center_y)))
            
        return surface

    def draw_stars(self, screen: pygame.Surface, top_left_pos: Tuple[int, int]):
        """
        Draws the item's stars directly onto the main screen.
        This is done separately from the body because stars are drawn on top of
        all items and only when the item is hovered.

        Args:
            screen (pygame.Surface): The main display surface to draw on.
            top_left_pos (Tuple[int, int]): The (x, y) pixel coordinate of the item's top-left corner on the screen.
        """
        for r, row in enumerate(self.shape_matrix):
            for c, cell in enumerate(row):
                if cell in STAR_SHAPE_COLORS:
                    # Calculate the center pixel of the star's grid cell.
                    cx = top_left_pos[0] + c * GRID_SIZE + GRID_SIZE // 2
                    cy = top_left_pos[1] + r * GRID_SIZE + GRID_SIZE // 2
                    color = STAR_SHAPE_COLORS[cell]
                    
                    # Draw the specific shape for each star type using trigonometry and polygon drawing.
                    if cell == GridType.STAR_A: # 5-pointed star
                        pts = [(cx + (GRID_SIZE/2 if a==18 else GRID_SIZE/4)*math.cos(math.radians(a+i*72)), cy + (GRID_SIZE/2 if a==18 else GRID_SIZE/4)*math.sin(math.radians(a+i*72))) for i in range(5) for a in [18,54]]
                        pygame.draw.polygon(screen, color, pts)
                    elif cell == GridType.STAR_B: # Diamond
                        pygame.draw.polygon(screen, color, [(cx,cy-GRID_SIZE*0.4),(cx+GRID_SIZE*0.4,cy),(cx,cy+GRID_SIZE*0.4),(cx-GRID_SIZE*0.4,cy)])
                    elif cell == GridType.STAR_C: # Triangle
                        pygame.draw.polygon(screen, color, [(cx,cy-GRID_SIZE*0.35),(cx-GRID_SIZE*0.35,cy+GRID_SIZE*0.35),(cx+GRID_SIZE*0.35,cy+GRID_SIZE*0.35)])

    def is_mouse_over_body(self, mouse_pos: Tuple[int, int], current_pos: Tuple[int, int]) -> bool:
        """
        Checks if the mouse cursor is colliding with any of the item's body parts (occupied cells).
        This is more precise than a simple rectangle collision, as it ignores empty
        parts of the item's shape matrix.

        Args:
            mouse_pos (Tuple[int, int]): The current (x, y) position of the mouse.
            current_pos (Tuple[int, int]): The current top-left (x, y) position of the item on the screen.

        Returns:
            bool: True if the mouse is over an occupied cell, False otherwise.
        """
        for r, row in enumerate(self.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED:
                    # Create a temporary Rect for just this one cell and check for collision.
                    cell_rect = pygame.Rect(current_pos[0] + c * GRID_SIZE, current_pos[1] + r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    if cell_rect.collidepoint(mouse_pos):
                        return True
        return False
        
    def rotate(self):
        """
        Rotates the item 90 degrees clockwise by manipulating its shape_matrix.
        This is a standard matrix rotation algorithm: transpose the matrix and then
        reverse each row. It then regenerates the item's visual surface.
        """
        # Transpose and reverse rows to rotate the matrix.
        self.shape_matrix = [list(row)[::-1] for row in zip(*self.shape_matrix)]
        # Update dimensions.
        self.grid_height, self.grid_width = len(self.shape_matrix), len(self.shape_matrix[0])
        # Re-create the visual surface to match the new shape.
        self.body_image = self.create_body_surface()


# =============================================================================
# --- CALCULATION ENGINE CLASS ---
# =============================================================================
class CalculationEngine:
    """
    Handles all the logic for calculating the final scores of items in the backpack.
    It works in a multi-pass process to ensure all effects are applied correctly.
    """
    def _check_condition(self, condition_data: dict, source_item: Item, target_item: Optional[Item]) -> bool:
        """
        A helper method to check if a single condition for a star effect is met.

        Args:
            condition_data (dict): The dictionary defining the condition (e.g., {"requires_type": "FOOD"}).
            source_item (Item): The item that owns the star.
            target_item (Optional[Item]): The item that the star is pointing to (can be None for empty cells).

        Returns:
            bool: True if the condition is satisfied, False otherwise.
        """
        if condition_data.get("requires_empty", False): return target_item is None
        if target_item is None: return False
        if "requires_element" in condition_data and Element[condition_data["requires_element"]] not in target_item.elements: return False
        if "requires_type" in condition_data and ItemType[condition_data["requires_type"]] not in target_item.types: return False
        if condition_data.get("must_be_different", False) and source_item.name == target_item.name: return False
        return True

    def _get_effect_value(self, effect_data: dict, source_item: Item) -> float:
        """
        A helper method to calculate the numerical value of a star's effect.
        Handles both static values and dynamic values that depend on other activated stars.

        Args:
            effect_data (dict): The dictionary defining the effect's value.
            source_item (Item): The item that owns the star, used for dynamic value calculations.

        Returns:
            float: The calculated numerical value of the effect.
        """
        value_data = effect_data.get("value", 0)
        # If the value is just a number, return it.
        if isinstance(value_data, (int, float)): return value_data
        
        # If the value is a dictionary, it's a dynamic value.
        final_value = value_data.get("base", 0.0)
        if "dynamic_bonus" in value_data:
            bonus_data = value_data["dynamic_bonus"]
            per_star_type = GridType[bonus_data["per_activated_star"]]
            num_activated = source_item.activated_stars.get(per_star_type, 0)
            final_value += num_activated * bonus_data.get("add", 0)
        return final_value

    def run(self, placed_items: Dict[Tuple[int, int], Item]):
        """
        The main method of the engine. It takes the current backpack layout and calculates all scores.

        Args:
            placed_items (Dict[Tuple[int, int], Item]): A dictionary mapping grid coordinates (gx, gy) to the Item objects placed there.
        """
        # --- Pass 0: Reset all items ---
        # Clear previous calculation results from all items.
        occupancy_grid: List[List[Optional[Item]]] = [[None for _ in range(BACKPACK_COLS)] for _ in range(BACKPACK_ROWS)]
        for item in placed_items.values():
            item.final_score, item.score_modifiers, item.occupying_stars = item.base_score, [], []
            item.activated_stars = {GridType.STAR_A: 0, GridType.STAR_B: 0, GridType.STAR_C: 0}
        
        # Create a 2D grid that maps each cell to the item occupying it, for easy lookups.
        for (gx, gy), item in placed_items.items():
            for r, row in enumerate(item.shape_matrix):
                for c, cell in enumerate(row):
                    if cell == GridType.OCCUPIED and 0 <= gy+r < BACKPACK_ROWS and 0 <= gx+c < BACKPACK_COLS:
                        occupancy_grid[gy+r][gx+c] = item

        # --- Pass 1: Star Activation ---
        # Determine which stars are "activated" by checking their conditions.
        # This must be done for all items before applying any score effects.
        for (gx, gy), source_item in placed_items.items():
            triggered_by = {GridType.STAR_A: set(), GridType.STAR_B: set(), GridType.STAR_C: set()}
            for r, row in enumerate(source_item.shape_matrix):
                for c, cell_type in enumerate(row):
                    if cell_type in triggered_by and (cell_type.name in source_item.star_effects):
                        abs_x, abs_y = gx + c, gy + r
                        target_item = occupancy_grid[abs_y][abs_x] if 0 <= abs_y < BACKPACK_ROWS and 0 <= abs_x < BACKPACK_COLS else None
                        
                        effect_data = source_item.star_effects[cell_type.name]
                        conditions = effect_data.get("conditions", [effect_data.get("condition", {})])
                        if any(self._check_condition(cond, source_item, target_item) for cond in conditions):
                            if target_item is None or target_item not in triggered_by[cell_type]:
                                source_item.activated_stars[cell_type] += 1
                                if target_item:
                                    target_item.occupying_stars.append((cell_type, source_item.name))
                                    triggered_by[cell_type].add(target_item)

        # --- Pass 2: Apply Effects ---
        # First, gather all effects that need to be applied from activated stars.
        all_effects = []
        for (gx, gy), source_item in placed_items.items():
             for r, row in enumerate(source_item.shape_matrix):
                for c, cell_type in enumerate(row):
                    if cell_type.name in source_item.star_effects:
                         abs_x, abs_y = gx + c, gy + r
                         target_item = occupancy_grid[abs_y][abs_x] if 0 <= abs_y < BACKPACK_ROWS and 0 <= abs_x < BACKPACK_COLS else None
                         effect_data = source_item.star_effects[cell_type.name]
                         if "effect" in effect_data:
                            conditions = effect_data.get("conditions", [effect_data.get("condition", {})])
                            if any(self._check_condition(cond, source_item, target_item) for cond in conditions):
                                value = self._get_effect_value(effect_data, source_item)
                                all_effects.append({"source": source_item, "target": target_item, "effect": effect_data["effect"], "value": value})
        
        # Apply all additive effects first.
        for effect_type in ["ADD_SCORE_TO_SELF", "ADD_SCORE_TO_TARGET"]:
            for eff in all_effects:
                if eff["effect"] == effect_type:
                    if eff["effect"] == "ADD_SCORE_TO_SELF": eff["source"].final_score += eff["value"]; eff["source"].score_modifiers.append(f"+{eff['value']:.1f} (self)")
                    elif eff["target"]: eff["target"].final_score += eff["value"]; eff["target"].score_modifiers.append(f"+{eff['value']:.1f} from {eff['source'].name}")
        
        # Then, apply all multiplicative effects. This order of operations is crucial.
        for effect_type in ["MULTIPLY_SCORE_OF_SELF", "MULTIPLY_SCORE_OF_TARGET"]:
            for eff in all_effects:
                if eff["effect"] == effect_type:
                    if eff["effect"] == "MULTIPLY_SCORE_OF_SELF": eff["source"].final_score *= eff["value"]; eff["source"].score_modifiers.append(f"x{eff['value']:.2f} (self)")
                    elif eff["target"]: eff["target"].final_score *= eff["value"]; eff["target"].score_modifiers.append(f"x{eff['value']:.2f} from {eff['source'].name}")


# =============================================================================
# --- HELPER FUNCTIONS ---
# =============================================================================
def load_items_from_file(filepath: str) -> List[Item]:
    """
    Reads the items.json file, parses it, and creates a list of Item objects.
    These items are used to populate the shop panel.

    Args:
        filepath (str): The path to the items.json file.

    Returns:
        List[Item]: A list of Item instances, one for each item in the JSON file.
    """
    items = []
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        y_offset = 0
        for item_data in data.values():
            # Create an Item instance for each entry in the JSON.
            item = Item(
                x=SHOP_X + 10, y=PANEL_Y + 10 + y_offset,
                name=item_data['name'],
                rarity=Rarity[item_data['rarity']],
                item_class=ItemClass[item_data['item_class']],
                elements=[Element[e] for e in item_data.get('elements', [])],
                types=[ItemType[t] for t in item_data.get('types', [])],
                shape_matrix=[[GridType(c) for c in r] for r in item_data['shape_matrix']],
                base_score=item_data.get('base_score', 0),
                star_effects=item_data.get('star_effects', {})
            )
            items.append(item)
            y_offset += item.rect.height + 10 # Stack items vertically in the shop.
    except Exception as e:
        print(f"Error loading items: {e}")
    return items

def is_placement_valid(item: Item, gx: int, gy: int, items_dict: Dict[Tuple[int, int], Item]) -> bool:
    """
    Checks if an item can be legally placed at a given grid coordinate.
    An item cannot be placed if any of its body parts are outside the backpack
    bounds or overlap with another already-placed item.

    Args:
        item (Item): The item being placed.
        gx (int): The target grid x-coordinate for the item's top-left corner.
        gy (int): The target grid y-coordinate for the item's top-left corner.
        items_dict (Dict[Tuple[int, int], Item]): The dictionary of currently placed items.

    Returns:
        bool: True if the placement is valid, False otherwise.
    """
    # First, build a set of all currently occupied grid cells.
    occupied_cells = set()
    for (px, py), p_item in items_dict.items():
        for r, row in enumerate(p_item.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED:
                    occupied_cells.add((px + c, py + r))
    
    # Now, check each body part of the new item.
    for r, row in enumerate(item.shape_matrix):
        for c, cell in enumerate(row):
            if cell == GridType.OCCUPIED:
                ax, ay = gx + c, gy + r
                # Check if it's outside the backpack grid.
                if not (0 <= ax < BACKPACK_COLS and 0 <= ay < BACKPACK_ROWS):
                    return False
                # Check if it overlaps with an existing item.
                if (ax, ay) in occupied_cells:
                    return False
    return True

def log_event(event_name: str, placed_items: Dict[Tuple[int, int], Item]):
    """
    A debugging function to print formatted log messages to the console.

    Args:
        event_name (str): A string describing the event (e.g., "LEFT_CLICK_DOWN").
        placed_items (Dict[Tuple[int, int], Item]): The current dictionary of placed items.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    placed_items_repr = {pos: item.name for pos, item in placed_items.items()}
    print(f"[{timestamp}] - {event_name} - {placed_items_repr}")


# =============================================================================
# --- MAIN GAME FUNCTION ---
# =============================================================================
def game_loop():
    """
    This is the main function that runs the entire application, including
    the game loop, event handling, and rendering.
    """
    # --- Initialization ---
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Backpack Battles - Final Scoring Engine")
    clock = pygame.time.Clock()

    # --- Game State Variables ---
    items_in_shop = load_items_from_file('items.json') # Load all possible items.
    placed_items = {}  # The primary data structure for the backpack layout.
    selected_item = None # The item currently being dragged by the user.
    engine = CalculationEngine() # The instance of our calculation engine.
    
    # --- UI and Font Initialization ---
    font_large = pygame.font.SysFont(None, 32)
    font_medium = pygame.font.SysFont(None, 24)
    font_small = pygame.font.SysFont(None, 20)
    calc_button = pygame.Rect(PANEL_START_X, 660, INFO_PANEL_WIDTH + SHOP_WIDTH + 20, 30)
    shop_area_rect = pygame.Rect(SHOP_X, PANEL_Y, SHOP_WIDTH, PANEL_HEIGHT)
    info_panel_rect = pygame.Rect(INFO_PANEL_X, PANEL_Y, INFO_PANEL_WIDTH, PANEL_HEIGHT)
    
    # --- Scroll State Variables ---
    shop_scroll_y = 0
    info_scroll_y = 0
    total_shop_height = sum(item.rect.height + 10 for item in items_in_shop) if items_in_shop else 0
    total_score = 0
    
    # --- Main Game Loop ---
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # --- Event Handling ---
        # This loop processes all user input (mouse, keyboard, etc.) for the current frame.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # --- Mouse Button Down Events ---
            elif event.type == pygame.MOUSEBUTTONDOWN:
                log_event(f"MOUSEBUTTONDOWN_{event.button}", placed_items)

                # Scrolling with the mouse wheel.
                if event.button == 4: # Scroll Up
                    if shop_area_rect.collidepoint(mouse_pos): shop_scroll_y = max(0, shop_scroll_y - 20)
                    if info_panel_rect.collidepoint(mouse_pos): info_scroll_y = max(0, info_scroll_y - 20)
                elif event.button == 5: # Scroll Down
                    if shop_area_rect.collidepoint(mouse_pos):
                        shop_scroll_y = min(max(0, total_shop_height - shop_area_rect.height), shop_scroll_y + 20)
                    if info_panel_rect.collidepoint(mouse_pos):
                        info_h = 50 + sum(160 + len(i.score_modifiers)*20 + len(i.occupying_stars)*20 for i in placed_items.values())
                        info_scroll_y = min(max(0, info_h - info_panel_rect.height), info_scroll_y + 20)

                # Rotate item with right-click.
                elif event.button == 3 and selected_item and selected_item.dragging:
                    # Complex rotation logic to keep the item centered under the mouse.
                    rx, ry = mouse_pos[0]-selected_item.rect.x, mouse_pos[1]-selected_item.rect.y
                    pc, pr = rx // GRID_SIZE, ry // GRID_SIZE
                    ogh = selected_item.grid_height
                    selected_item.rotate()
                    npc, npr = ogh-1-pr, pc
                    npx, npy = npc*GRID_SIZE, npr*GRID_SIZE
                    nr = selected_item.body_image.get_rect(x=mouse_pos[0]-npx, y=mouse_pos[1]-npy)
                    selected_item.rect = nr
                    offset_x, offset_y = nr.x-mouse_pos[0], nr.y-mouse_pos[1]

                # Pick up or create item with left-click.
                elif event.button == 1:
                    # First, check if the user is clicking on an already-placed item.
                    item_to_pick_info = None
                    for pos, item in reversed(list(placed_items.items())): # Reversed to pick top item first.
                        item_pos_on_screen = (BACKPACK_X + pos[0] * GRID_SIZE, BACKPACK_Y + pos[1] * GRID_SIZE)
                        if item.is_mouse_over_body(mouse_pos, item_pos_on_screen):
                            item_to_pick_info = (pos, item)
                            break
                    
                    if item_to_pick_info: # If we found an item to pick up...
                        pos, item = item_to_pick_info
                        selected_item = item
                        item_pos_on_screen = (BACKPACK_X + pos[0] * GRID_SIZE, BACKPACK_Y + pos[1] * GRID_SIZE)
                        # Calculate mouse offset to make dragging feel natural.
                        offset_x = item_pos_on_screen[0] - mouse_pos[0]
                        offset_y = item_pos_on_screen[1] - mouse_pos[1]
                        selected_item.dragging = True
                        selected_item.rect.topleft = item_pos_on_screen
                        # Remove the item from the placed_items dict while it's being dragged.
                        del placed_items[pos]
                    
                    else: # If not clicking a placed item, check the shop.
                        for item_t in items_in_shop:
                            if item_t.is_mouse_over_body(mouse_pos, item_t.rect.topleft):
                                # Create a NEW instance of the item from the shop template.
                                selected_item = Item(item_t.rect.x, item_t.rect.y, item_t.name, item_t.rarity, item_t.item_class, item_t.elements, item_t.types, item_t.shape_matrix, item_t.base_score, item_t.star_effects)
                                selected_item.dragging = True
                                offset_x, offset_y = item_t.rect.x - mouse_pos[0], item_t.rect.y - mouse_pos[1]
                                break
                    
                    # Check if the "Calculate" button was clicked.
                    if calc_button.collidepoint(mouse_pos): 
                        engine.run(placed_items)
                        total_score = sum(item.final_score for item in placed_items.values())

            # --- Mouse Button Up Events ---
            elif event.type == pygame.MOUSEBUTTONUP:
                log_event("MOUSEBUTTONUP", placed_items)
                if event.button == 1 and selected_item:
                    selected_item.dragging = False
                    # Convert pixel coordinates to grid coordinates to place the item.
                    gx = round((selected_item.rect.left - BACKPACK_X) / GRID_SIZE)
                    gy = round((selected_item.rect.top - BACKPACK_Y) / GRID_SIZE)
                    
                    # If the placement is valid, add it to the placed_items dictionary.
                    if is_placement_valid(selected_item, gx, gy, placed_items):
                        placed_items[(gx, gy)] = selected_item
                    
                    # The item is no longer selected, whether it was placed or not.
                    selected_item = None
            
            # --- Mouse Motion Events ---
            elif event.type == pygame.MOUSEMOTION:
                if selected_item and selected_item.dragging:
                    # Update the dragged item's position to follow the mouse.
                    selected_item.rect.x = mouse_pos[0] + offset_x
                    selected_item.rect.y = mouse_pos[1] + offset_y
        
        # --- Drawing / Rendering ---
        # This section happens every single frame to draw the current state of the game.
        # The order of drawing is important (background -> items -> UI -> dragged item).
        
        # 1. Clear the screen with the background color.
        screen.fill(BG_COLOR)
        
        # 2. Draw static UI elements (backpack grid, panels, etc.).
        bp_rect = pygame.Rect(BACKPACK_X, BACKPACK_Y, BACKPACK_COLS*GRID_SIZE, BACKPACK_ROWS*GRID_SIZE)
        pygame.draw.rect(screen, (230,230,230), bp_rect)
        pygame.draw.rect(screen, (240,240,240), shop_area_rect, 2)
        total_score_rect = pygame.Rect(info_panel_rect.left, info_panel_rect.bottom, info_panel_rect.width, 50)
        pygame.draw.rect(screen, (210, 210, 210), total_score_rect)
        pygame.draw.rect(screen, (180, 180, 180), total_score_rect, 2)
        pygame.draw.rect(screen, (220,220,220), info_panel_rect)
        pygame.draw.rect(screen, (180,180,180), info_panel_rect, 2)
        for x in range(bp_rect.left, bp_rect.right + 1, GRID_SIZE): pygame.draw.line(screen, GRID_LINE_COLOR, (x, bp_rect.top), (x, bp_rect.bottom))
        for y in range(bp_rect.top, bp_rect.bottom + 1, GRID_SIZE): pygame.draw.line(screen, GRID_LINE_COLOR, (bp_rect.left, y), (bp_rect.right, y))

        # 3. Draw the contents of the info panel (with scrolling).
        screen.set_clip(info_panel_rect) # Restricts drawing to within this panel.
        screen.blit(font_large.render("Backpack Contents", True, FONT_COLOR), (info_panel_rect.x+10, info_panel_rect.y+10-info_scroll_y))
        y_off = 45
        for item in placed_items.values():
            screen.blit(font_medium.render(f"- {item.name}", True, FONT_COLOR), (info_panel_rect.x+15, info_panel_rect.y+y_off-info_scroll_y)); y_off += 25
            elems = f"Elem: {', '.join(e.name for e in item.elements) or 'None'}"; types = f"Type: {', '.join(t.name for t in item.types) or 'None'}"
            screen.blit(font_small.render(elems, True, (60,60,60)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 20
            screen.blit(font_small.render(types, True, (60,60,60)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 25
            star_txt = f"Activated: A:{item.activated_stars[GridType.STAR_A]} B:{item.activated_stars[GridType.STAR_B]} C:{item.activated_stars[GridType.STAR_C]}"
            screen.blit(font_small.render(star_txt, True, (60,60,60)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 20
            if item.occupying_stars:
                screen.blit(font_small.render("Occupying:", True, (60,60,60)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 20
                for star_type, source_name in item.occupying_stars: screen.blit(font_small.render(f"  - {source_name}'s {star_type.name}", True, (80,80,80)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 20
            screen.blit(font_small.render(f"Base Score: {item.base_score}", True, (60,60,60)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 20
            for mod in item.score_modifiers: screen.blit(font_small.render(f"  {mod}", True, (20,100,20)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 20
            screen.blit(font_medium.render(f"Final Score: {item.final_score:.1f}", True, FONT_COLOR), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 25
            y_off += 15
        screen.set_clip(None) # Stop restricting the drawing area.
        
        # 4. Draw the total score display.
        total_score_text = f"Total Score: {total_score:.1f}"
        screen.blit(font_large.render(total_score_text, True, FONT_COLOR), (total_score_rect.x + 10, total_score_rect.centery - 16))

        # 5. Draw all item bodies (in backpack and shop).
        all_items = [(item, (BACKPACK_X+pos[0]*GRID_SIZE, BACKPACK_Y+pos[1]*GRID_SIZE)) for pos, item in placed_items.items()]
        for item in items_in_shop: item.rect.y=item.base_y-shop_scroll_y; all_items.append((item, item.rect.topleft))
        for item, pos in all_items:
            # Check if item is on screen before drawing.
            if shop_area_rect.colliderect(pygame.Rect(pos, item.body_image.get_size())) or info_panel_rect.x > pos[0]:
                screen.blit(item.body_image, pos)

        # 6. Draw stars ONLY for hovered items. This must be a separate loop.
        for item, pos in all_items:
            if item.is_mouse_over_body(mouse_pos, pos):
                is_in_shop = shop_area_rect.colliderect(pygame.Rect(pos, item.body_image.get_size()))
                if is_in_shop: screen.set_clip(shop_area_rect) # Clip stars to shop panel.
                item.draw_stars(screen, pos)
                if is_in_shop: screen.set_clip(None)

        # 7. Draw the currently dragged item ON TOP of everything else.
        if selected_item and selected_item.dragging:
            screen.blit(selected_item.body_image, selected_item.rect)
            selected_item.draw_stars(screen, selected_item.rect.topleft)
            # Also draw the invalid placement overlay if needed.
            gx, gy = round((selected_item.rect.left-BACKPACK_X)/GRID_SIZE), round((selected_item.rect.top-BACKPACK_Y)/GRID_SIZE)
            if not is_placement_valid(selected_item, gx, gy, placed_items):
                tint = pygame.Surface(selected_item.rect.size, pygame.SRCALPHA); tint.fill(INVALID_PLACEMENT_COLOR)
                screen.blit(tint, selected_item.rect.topleft)

        # 8. Draw the Calculate button.
        pygame.draw.rect(screen, (100, 200, 100), calc_button)
        screen.blit(font_medium.render("Calculate", True, FONT_COLOR), calc_button.inflate(-10,-10))
        
        # 9. Update the display.
        # This tells Pygame to show everything that has been drawn in this frame.
        pygame.display.flip()
        
        # 10. Control the frame rate.
        clock.tick(60) # Limits the game to a maximum of 60 frames per second.
    
    # --- Cleanup ---
    pygame.quit()
    sys.exit()

# =============================================================================
# --- SCRIPT EXECUTION ---
# =============================================================================
if __name__ == "__main__": 
    # This standard Python construct ensures that game_loop() is only called
    # when the script is executed directly (not when it's imported as a module).
    game_loop()

