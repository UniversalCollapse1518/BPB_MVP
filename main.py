import pygame
import sys
import json
from enum import Enum
from typing import List, Optional, Dict, Tuple

# --- Constants ---
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
GRID_SIZE = 40
BG_COLOR = (255, 255, 255)
FONT_COLOR = (10, 10, 10)
GRID_LINE_COLOR = (200, 200, 200)
INVALID_PLACEMENT_COLOR = (255, 0, 0, 100)

# Backpack dimensions
BACKPACK_COLS = 9
BACKPACK_ROWS = 7
BACKPACK_X, BACKPACK_Y = 50, 50

# Shop dimensions
SHOP_X, SHOP_Y = 600, 50
SHOP_WIDTH, SHOP_HEIGHT = 250, 400

# --- Enums for Item Properties ---

class GridType(Enum):
    EMPTY = 0
    OCCUPIED = 1
    STAR_A = 2
    STAR_B = 3
    STAR_C = 4

class Rarity(Enum):
    COMMON = "Common"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"
    GODLY = "Godly"
    UNIQUE = "Unique"

class ItemClass(Enum):
    NEUTRAL = "Neutral"
    RANGER = "Ranger"
    REAPER = "Reaper"
    BERSERKER = "Berserker"
    PYROMANCER = "Pyromancer"
    MAGE = "Mage"
    ADVENTURER = "Adventurer"

class Element(Enum):
    MELEE = "Melee"
    RANGED = "Ranged"
    MAGIC = "Magic"

class ItemType(Enum):
    WEAPON = "Weapon"
    SHIELD = "Shield"
    PET = "Pet"

# --- Rarity and Star Colors ---
RARITY_BORDER_COLORS = {
    Rarity.COMMON: (150, 150, 150), Rarity.RARE: (0, 100, 255),
    Rarity.EPIC: (138, 43, 226), Rarity.LEGENDARY: (255, 165, 0),
    Rarity.GODLY: (255, 215, 0), Rarity.UNIQUE: (255, 20, 147)
}
STAR_COLORS = {
    GridType.STAR_A: (255, 223, 89, 100), GridType.STAR_B: (173, 216, 230, 100),
    GridType.STAR_C: (255, 182, 193, 100)
}

# --- Item Class (UPDATED) ---
class Item(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, name: str, rarity: Rarity,
                 item_class: ItemClass, elements: List[Element], types: List[ItemType],
                 shape_matrix: List[List[GridType]]):
        super().__init__()
        # Core properties from JSON
        self.name = name
        self.rarity = rarity
        self.item_class = item_class
        self.elements = elements
        self.types = types
        self.shape_matrix = shape_matrix
        
        # Derived properties
        self.grid_width = len(shape_matrix[0]) if shape_matrix else 0
        self.grid_height = len(shape_matrix)
        
        # Pygame state
        self.update_surfaces()
        self.rect = self.image_with_stars.get_rect(topleft=(x, y))
        self.dragging = False

    def update_surfaces(self):
        self.image_with_stars = self.create_item_surface(show_stars=True)
        self.image_without_stars = self.create_item_surface(show_stars=False)
        self.image = self.image_with_stars

    def create_item_surface(self, show_stars: bool):
        width_px = self.grid_width * GRID_SIZE
        height_px = self.grid_height * GRID_SIZE
        surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
        for r_idx, row in enumerate(self.shape_matrix):
            for c_idx, cell_type in enumerate(row):
                x, y = c_idx * GRID_SIZE, r_idx * GRID_SIZE
                if cell_type == GridType.OCCUPIED:
                    pygame.draw.rect(surface, (200, 200, 200), (x, y, GRID_SIZE, GRID_SIZE))
                    pygame.draw.rect(surface, RARITY_BORDER_COLORS[self.rarity], (x, y, GRID_SIZE, GRID_SIZE), 2)
                elif show_stars and cell_type in STAR_COLORS:
                    star_surface = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
                    star_surface.fill(STAR_COLORS[cell_type])
                    surface.blit(star_surface, (x, y))
                    pygame.draw.circle(surface, (255,255,255), (x + GRID_SIZE//2, y + GRID_SIZE//2), 5)
        return surface

    def rotate(self):
        """Rotates the item data. Does NOT handle repositioning."""
        transposed_matrix = list(zip(*self.shape_matrix))
        self.shape_matrix = [list(row)[::-1] for row in transposed_matrix]
        self.grid_height = len(self.shape_matrix)
        self.grid_width = len(self.shape_matrix[0])
        self.update_surfaces()
        # Note: self.rect size is now stale. The new rect is based on the new image size.
        # The main loop is responsible for creating and positioning the new rect.

# --- Data Loading Function (UPDATED) ---
def load_items_from_file(filepath: str) -> List[Item]:
    shop_items = []
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        y_offset = 0
        for item_key, item_data in data.items():
            rarity = Rarity[item_data['rarity']]
            item_class = ItemClass[item_data['item_class']]
            elements = [Element[e] for e in item_data.get('elements', [])]
            types = [ItemType[t] for t in item_data.get('types', [])]
            shape_matrix = [[GridType(cell) for cell in row] for row in item_data['shape_matrix']]
            
            item_x, item_y = SHOP_X + 10, SHOP_Y + 10 + y_offset
            
            item = Item(item_x, item_y, item_data['name'], rarity, item_class, elements, types, shape_matrix)
            shop_items.append(item)
            y_offset += item.rect.height + 10
    except Exception as e:
        print(f"Error loading items: {e}")
    return shop_items

# --- Helper Function for Collision ---
def is_placement_valid(item_to_place: Item, grid_x: int, grid_y: int, placed_items: Dict[Tuple[int, int], Item]) -> bool:
    occupied_cells = set()
    for (px, py), p_item in placed_items.items():
        for r_idx, row in enumerate(p_item.shape_matrix):
            for c_idx, cell_type in enumerate(row):
                if cell_type == GridType.OCCUPIED:
                    occupied_cells.add((px + c_idx, py + r_idx))

    for r_idx, row in enumerate(item_to_place.shape_matrix):
        for c_idx, cell_type in enumerate(row):
            if cell_type == GridType.OCCUPIED:
                abs_x, abs_y = grid_x + c_idx, grid_y + r_idx
                if not (0 <= abs_x < BACKPACK_COLS and 0 <= abs_y < BACKPACK_ROWS):
                    return False
                if (abs_x, abs_y) in occupied_cells:
                    return False
    return True

# --- Main Game Function ---
def game_loop():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Backpack Battles - Data Driven")
    clock = pygame.time.Clock()

    items_in_shop = load_items_from_file('items.json')
    placed_items = {}
    selected_item = None
    
    font = pygame.font.SysFont(None, 30)
    calc_button = pygame.Rect(600, 500, 200, 50)
    shop_area_rect = pygame.Rect(SHOP_X, SHOP_Y, SHOP_WIDTH, SHOP_HEIGHT)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3 and selected_item and selected_item.dragging:
                    # --- ROTATION LOGIC (REWORKED) ---
                    # 1. Find the grid cell on the item the mouse is over (the pivot)
                    rel_x = mouse_pos[0] - selected_item.rect.x
                    rel_y = mouse_pos[1] - selected_item.rect.y
                    pivot_col = max(0, min(rel_x // GRID_SIZE, selected_item.grid_width - 1))
                    pivot_row = max(0, min(rel_y // GRID_SIZE, selected_item.grid_height - 1))

                    # 2. Store old width to calculate new pivot position
                    old_grid_width = selected_item.grid_width

                    # 3. Rotate item data (matrix, surfaces, dimensions)
                    selected_item.rotate() 

                    # 4. Calculate where the pivot cell has moved to in the new matrix
                    new_pivot_col = pivot_row
                    new_pivot_row = old_grid_width - 1 - pivot_col
                    
                    # 5. Calculate the pixel offset from the new rect's top-left to the pivot cell's top-left
                    new_pivot_pixel_offset_x = new_pivot_col * GRID_SIZE
                    new_pivot_pixel_offset_y = new_pivot_row * GRID_SIZE

                    # 6. Create the new rect and position it so the pivot is under the mouse
                    new_rect = selected_item.image.get_rect()
                    new_rect.x = mouse_pos[0] - new_pivot_pixel_offset_x
                    new_rect.y = mouse_pos[1] - new_pivot_pixel_offset_y
                    selected_item.rect = new_rect

                    # 7. Recalculate the main drag offset for smooth motion
                    offset_x = selected_item.rect.x - mouse_pos[0]
                    offset_y = selected_item.rect.y - mouse_pos[1]

                elif event.button == 1:
                    clicked_on_item = False
                    # Pick up from backpack
                    for pos, item in list(placed_items.items()):
                        item_rect = item.image.get_rect(topleft=(BACKPACK_X + pos[0] * GRID_SIZE, BACKPACK_Y + pos[1] * GRID_SIZE))
                        if item_rect.collidepoint(mouse_pos):
                            selected_item = item
                            selected_item.dragging = True
                            selected_item.rect.topleft = item_rect.topleft
                            offset_x, offset_y = selected_item.rect.x - mouse_pos[0], selected_item.rect.y - mouse_pos[1]
                            del placed_items[pos]
                            clicked_on_item = True
                            break
                    # Pick from shop
                    if not clicked_on_item:
                        for item_template in items_in_shop:
                            if item_template.rect.collidepoint(mouse_pos):
                                selected_item = Item(item_template.rect.x, item_template.rect.y, item_template.name, 
                                                     item_template.rarity, item_template.item_class, item_template.elements,
                                                     item_template.types, item_template.shape_matrix)
                                selected_item.dragging = True
                                offset_x, offset_y = selected_item.rect.x - mouse_pos[0], selected_item.rect.y - mouse_pos[1]
                                break
                    if calc_button.collidepoint(mouse_pos):
                        print("--- Calculating Interactions (Not Implemented Yet) ---")

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and selected_item:
                    selected_item.dragging = False
                    grid_x = round((selected_item.rect.left - BACKPACK_X) / GRID_SIZE)
                    grid_y = round((selected_item.rect.top - BACKPACK_Y) / GRID_SIZE)
                    if is_placement_valid(selected_item, grid_x, grid_y, placed_items):
                        placed_items[(grid_x, grid_y)] = selected_item
                    selected_item = None
            elif event.type == pygame.MOUSEMOTION:
                if selected_item and selected_item.dragging:
                    selected_item.rect.x = mouse_pos[0] + offset_x
                    selected_item.rect.y = mouse_pos[1] + offset_y
        
        # --- Drawing ---
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, (230, 230, 230), pygame.Rect(BACKPACK_X, BACKPACK_Y, BACKPACK_COLS * GRID_SIZE, BACKPACK_ROWS * GRID_SIZE))
        pygame.draw.rect(screen, (240, 240, 240), shop_area_rect, 2)
        for x in range(BACKPACK_X, BACKPACK_X + BACKPACK_COLS * GRID_SIZE + 1, GRID_SIZE):
            pygame.draw.line(screen, GRID_LINE_COLOR, (x, BACKPACK_Y), (x, BACKPACK_Y + BACKPACK_ROWS * GRID_SIZE))
        for y in range(BACKPACK_Y, BACKPACK_Y + BACKPACK_ROWS * GRID_SIZE + 1, GRID_SIZE):
            pygame.draw.line(screen, GRID_LINE_COLOR, (BACKPACK_X, y), (BACKPACK_X + BACKPACK_COLS * GRID_SIZE, y))

        for (grid_x, grid_y), item in placed_items.items():
            item_pos = (BACKPACK_X + grid_x * GRID_SIZE, BACKPACK_Y + grid_y * GRID_SIZE)
            item_rect = item.image.get_rect(topleft=item_pos)
            image_to_draw = item.image_with_stars if item_rect.collidepoint(mouse_pos) else item.image_without_stars
            screen.blit(image_to_draw, item_pos)
            
        for item in items_in_shop:
            image_to_draw = item.image_with_stars if item.rect.collidepoint(mouse_pos) else item.image_without_stars
            screen.blit(image_to_draw, item.rect)
        
        if selected_item and selected_item.dragging:
            grid_x, grid_y = round((selected_item.rect.left - BACKPACK_X)/GRID_SIZE), round((selected_item.rect.top - BACKPACK_Y)/GRID_SIZE)
            image_to_draw = selected_item.image_with_stars
            if not is_placement_valid(selected_item, grid_x, grid_y, placed_items):
                tint_surface = image_to_draw.copy()
                tint_surface.fill(INVALID_PLACEMENT_COLOR, special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(tint_surface, selected_item.rect.topleft)
            else:
                screen.blit(image_to_draw, selected_item.rect)

        pygame.draw.rect(screen, (100, 200, 100), calc_button)
        btn_text = font.render("Calculate", True, FONT_COLOR)
        screen.blit(btn_text, btn_text.get_rect(center=calc_button.center))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()
