import pygame
import sys
import json
from enum import Enum
from typing import List, Optional, Dict, Tuple
import math

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
# --- QOL UPDATE: New Star Colors and Shapes ---
STAR_SHAPE_COLORS = {
    GridType.STAR_A: (255, 215, 0),   # Yellow
    GridType.STAR_B: (50, 205, 50),    # Green
    GridType.STAR_C: (148, 0, 211)     # Purple
}

# --- Item Class ---
class Item(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, name: str, rarity: Rarity,
                 item_class: ItemClass, elements: List[Element], types: List[ItemType],
                 shape_matrix: List[List[GridType]]):
        super().__init__()
        self.name = name
        self.rarity = rarity
        self.item_class = item_class
        self.elements = elements
        self.types = types
        self.shape_matrix = shape_matrix
        self.grid_width = len(shape_matrix[0]) if shape_matrix else 0
        self.grid_height = len(shape_matrix)
        
        self.body_image = self.create_body_surface()
        self.rect = self.body_image.get_rect(topleft=(x, y))
        self.dragging = False

    def create_body_surface(self):
        width_px = self.grid_width * GRID_SIZE
        height_px = self.grid_height * GRID_SIZE
        surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
        for r_idx, row in enumerate(self.shape_matrix):
            for c_idx, cell_type in enumerate(row):
                if cell_type == GridType.OCCUPIED:
                    x, y = c_idx * GRID_SIZE, r_idx * GRID_SIZE
                    pygame.draw.rect(surface, (200, 200, 200), (x, y, GRID_SIZE, GRID_SIZE))
                    pygame.draw.rect(surface, RARITY_BORDER_COLORS[self.rarity], (x, y, GRID_SIZE, GRID_SIZE), 2)
        return surface

    def draw_stars(self, screen, top_left_pos):
        """Draws the star shapes directly onto the screen."""
        for r_idx, row in enumerate(self.shape_matrix):
            for c_idx, cell_type in enumerate(row):
                if cell_type in STAR_SHAPE_COLORS:
                    center_x = top_left_pos[0] + c_idx * GRID_SIZE + GRID_SIZE // 2
                    center_y = top_left_pos[1] + r_idx * GRID_SIZE + GRID_SIZE // 2
                    color = STAR_SHAPE_COLORS[cell_type]
                    
                    if cell_type == GridType.STAR_A: # 5-pointed star
                        points = []
                        for i in range(5):
                            angle_rad = math.radians(18 + i * 72)
                            outer_x = center_x + (GRID_SIZE / 2) * math.cos(angle_rad)
                            outer_y = center_y + (GRID_SIZE / 2) * math.sin(angle_rad)
                            points.append((outer_x, outer_y))
                            
                            angle_rad = math.radians(54 + i * 72)
                            inner_x = center_x + (GRID_SIZE / 4) * math.cos(angle_rad)
                            inner_y = center_y + (GRID_SIZE / 4) * math.sin(angle_rad)
                            points.append((inner_x, inner_y))
                        pygame.draw.polygon(screen, color, points)

                    elif cell_type == GridType.STAR_B: # Diamond
                        radius = GRID_SIZE * 0.4
                        points = [
                            (center_x, center_y - radius), (center_x + radius, center_y),
                            (center_x, center_y + radius), (center_x - radius, center_y)
                        ]
                        pygame.draw.polygon(screen, color, points)

                    elif cell_type == GridType.STAR_C: # Triangle
                        height = GRID_SIZE * 0.7
                        points = [
                            (center_x, center_y - height / 2),
                            (center_x - height / 2, center_y + height / 2),
                            (center_x + height / 2, center_y + height / 2)
                        ]
                        pygame.draw.polygon(screen, color, points)

    def is_mouse_over_body(self, mouse_pos):
        """Checks if the mouse is over an OCCUPIED part of the item."""
        if self.rect.collidepoint(mouse_pos):
            rel_x = mouse_pos[0] - self.rect.x
            rel_y = mouse_pos[1] - self.rect.y
            grid_col = rel_x // GRID_SIZE
            grid_row = rel_y // GRID_SIZE
            if 0 <= grid_row < self.grid_height and 0 <= grid_col < self.grid_width:
                return self.shape_matrix[grid_row][grid_col] == GridType.OCCUPIED
        return False
        
    def rotate(self):
        transposed_matrix = list(zip(*self.shape_matrix))
        self.shape_matrix = [list(row)[::-1] for row in transposed_matrix]
        self.grid_height = len(self.shape_matrix)
        self.grid_width = len(self.shape_matrix[0])
        self.body_image = self.create_body_surface()

# --- Data Loading Function ---
def load_items_from_file(filepath: str) -> List[Item]:
    shop_items = []
    try:
        with open(filepath, 'r') as f: data = json.load(f)
        y_offset = 0
        for item_data in data.values():
            rarity = Rarity[item_data['rarity']]
            item_class = ItemClass[item_data['item_class']]
            elements = [Element[e] for e in item_data.get('elements', [])]
            types = [ItemType[t] for t in item_data.get('types', [])]
            shape_matrix = [[GridType(cell) for cell in row] for row in item_data['shape_matrix']]
            item = Item(SHOP_X + 10, SHOP_Y + 10 + y_offset, item_data['name'], rarity, item_class, elements, types, shape_matrix)
            shop_items.append(item)
            y_offset += item.rect.height + 10
    except Exception as e: print(f"Error loading items: {e}")
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
                if not (0 <= abs_x < BACKPACK_COLS and 0 <= abs_y < BACKPACK_ROWS): return False
                if (abs_x, abs_y) in occupied_cells: return False
    return True

# --- Main Game Function ---
def game_loop():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Backpack Battles - QoL v2")
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
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3 and selected_item and selected_item.dragging:
                    rel_x = mouse_pos[0] - selected_item.rect.x
                    rel_y = mouse_pos[1] - selected_item.rect.y
                    pivot_col, pivot_row = rel_x // GRID_SIZE, rel_y // GRID_SIZE
                    old_grid_height = selected_item.grid_height
                    selected_item.rotate() 
                    new_pivot_col = old_grid_height - 1 - pivot_row
                    new_pivot_row = pivot_col
                    new_pivot_px_offset_x = new_pivot_col * GRID_SIZE
                    new_pivot_px_offset_y = new_pivot_row * GRID_SIZE
                    new_rect = selected_item.body_image.get_rect()
                    new_rect.x = mouse_pos[0] - new_pivot_px_offset_x
                    new_rect.y = mouse_pos[1] - new_pivot_px_offset_y
                    selected_item.rect = new_rect
                    offset_x, offset_y = selected_item.rect.x - mouse_pos[0], selected_item.rect.y - mouse_pos[1]
                elif event.button == 1:
                    clicked_on_item = False
                    for pos, item in list(placed_items.items()):
                        item.rect.topleft = (BACKPACK_X + pos[0] * GRID_SIZE, BACKPACK_Y + pos[1] * GRID_SIZE)
                        if item.rect.collidepoint(mouse_pos):
                            selected_item = item
                            selected_item.dragging = True
                            offset_x, offset_y = selected_item.rect.x - mouse_pos[0], selected_item.rect.y - mouse_pos[1]
                            del placed_items[pos]
                            clicked_on_item = True
                            break
                    if not clicked_on_item:
                        for item_template in items_in_shop:
                            if item_template.rect.collidepoint(mouse_pos):
                                selected_item = Item(item_template.rect.x, item_template.rect.y, item_template.name, 
                                                     item_template.rarity, item_template.item_class, item_template.elements,
                                                     item_template.types, item_template.shape_matrix)
                                selected_item.dragging = True
                                offset_x, offset_y = selected_item.rect.x - mouse_pos[0], selected_item.rect.y - mouse_pos[1]
                                break
                    if calc_button.collidepoint(mouse_pos): print("--- Calculating Interactions ---")
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

        # --- DRAWING PASS 1: Item Bodies ---
        for (grid_x, grid_y), item in placed_items.items():
            item.rect.topleft = (BACKPACK_X + grid_x * GRID_SIZE, BACKPACK_Y + grid_y * GRID_SIZE)
            screen.blit(item.body_image, item.rect)
        for item in items_in_shop:
            screen.blit(item.body_image, item.rect)

        # --- DRAWING PASS 2: Item Stars (for hover effects) ---
        for (grid_x, grid_y), item in placed_items.items():
            if item.is_mouse_over_body(mouse_pos):
                item.draw_stars(screen, item.rect.topleft)
        for item in items_in_shop:
            if item.is_mouse_over_body(mouse_pos):
                item.draw_stars(screen, item.rect.topleft)
        
        # --- DRAWING PASS 3: Dragged Item ---
        if selected_item and selected_item.dragging:
            screen.blit(selected_item.body_image, selected_item.rect)
            selected_item.draw_stars(screen, selected_item.rect.topleft) # Always show stars when dragging
            
            grid_x, grid_y = round((selected_item.rect.left - BACKPACK_X)/GRID_SIZE), round((selected_item.rect.top - BACKPACK_Y)/GRID_SIZE)
            if not is_placement_valid(selected_item, grid_x, grid_y, placed_items):
                tint_surface = pygame.Surface(selected_item.rect.size, pygame.SRCALPHA)
                tint_surface.fill(INVALID_PLACEMENT_COLOR)
                screen.blit(tint_surface, selected_item.rect.topleft)

        pygame.draw.rect(screen, (100, 200, 100), calc_button)
        btn_text = font.render("Calculate", True, FONT_COLOR)
        screen.blit(btn_text, btn_text.get_rect(center=calc_button.center))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()

