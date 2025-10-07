import pygame
import sys
from enum import Enum, auto
from typing import List, Optional

# --- Constants ---
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
GRID_SIZE = 40 # Made grid smaller to fit larger backpack
BG_COLOR = (255, 255, 255)
FONT_COLOR = (10, 10, 10)
GRID_LINE_COLOR = (200, 200, 200)

# Backpack dimensions
BACKPACK_COLS = 9
BACKPACK_ROWS = 7
BACKPACK_X, BACKPACK_Y = 50, 50

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
    # ... (rest of rarities)

# ... (other enums like ItemClass, Element, ItemType) ...
# For brevity, they are omitted here but should be kept in your code

# --- Rarity and Star Colors ---
RARITY_BORDER_COLORS = { Rarity.COMMON: (150, 150, 150), Rarity.RARE: (0, 100, 255) }
STAR_COLORS = {
    GridType.STAR_A: (255, 223, 89, 150), # Gold with alpha
    GridType.STAR_B: (173, 216, 230, 150), # Light Blue with alpha
    GridType.STAR_C: (255, 182, 193, 150)  # Light Pink with alpha
}

# --- Item Class (HEAVILY UPDATED) ---
class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, name: str, rarity: Rarity, 
                 shape_matrix: List[List[GridType]],
                 # Other properties like item_class, etc. can be added back here
                 damage: int = 0):
        super().__init__()
        
        # Core Properties
        self.name = name
        self.rarity = rarity
        self.shape_matrix = shape_matrix
        self.damage = damage
        
        # Determine the item's size in grid units from the matrix
        self.grid_width = len(shape_matrix[0])
        self.grid_height = len(shape_matrix)
        
        # Pygame properties
        self.image = self.create_item_surface()
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.dragging = False

    def create_item_surface(self):
        """Creates the visual surface for the item based on its shape matrix."""
        width_px = self.grid_width * GRID_SIZE
        height_px = self.grid_height * GRID_SIZE
        surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA) # Use SRCALPHA for transparency

        for r_idx, row in enumerate(self.shape_matrix):
            for c_idx, cell_type in enumerate(row):
                x, y = c_idx * GRID_SIZE, r_idx * GRID_SIZE
                
                if cell_type == GridType.OCCUPIED:
                    # Draw the physical part of the item
                    pygame.draw.rect(surface, (200, 200, 200), (x, y, GRID_SIZE, GRID_SIZE))
                    pygame.draw.rect(surface, RARITY_BORDER_COLORS[self.rarity], (x, y, GRID_SIZE, GRID_SIZE), 2)
                
                elif cell_type in STAR_COLORS:
                    # Draw a transparent overlay for stars
                    star_surface = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
                    star_surface.fill(STAR_COLORS[cell_type])
                    surface.blit(star_surface, (x, y))
                    # Draw a symbol (e.g., a circle) to make it clearer
                    pygame.draw.circle(surface, (255,255,255), (x + GRID_SIZE//2, y + GRID_SIZE//2), 5)

        return surface

    def draw_at_grid(self, screen, grid_x, grid_y):
        """Draws the item's surface at a specific grid coordinate on the screen."""
        screen_x = BACKPACK_X + grid_x * GRID_SIZE
        screen_y = BACKPACK_Y + grid_y * GRID_SIZE
        screen.blit(self.image, (screen_x, screen_y))
        
# --- Main Game Function ---
def game_loop():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Backpack Battles - Matrix System")
    clock = pygame.time.Clock()

    # --- Define Item Shapes ---
    # Centered in a 3x3 matrix for simplicity, can be expanded to 9x7
    sword_shape = [
        [GridType.EMPTY, GridType.STAR_A, GridType.EMPTY],
        [GridType.EMPTY, GridType.OCCUPIED, GridType.EMPTY],
        [GridType.EMPTY, GridType.EMPTY, GridType.EMPTY],
    ]
    
    shield_shape = [
        [GridType.EMPTY,   GridType.STAR_B,  GridType.STAR_B,  GridType.EMPTY],
        [GridType.OCCUPIED, GridType.OCCUPIED, GridType.OCCUPIED, GridType.STAR_A],
    ]

    # --- Create Items ---
    items_in_shop = [
        Item(600, 50, "Sword", Rarity.COMMON, sword_shape, damage=5),
        Item(600, 200, "Shield", Rarity.RARE, shield_shape, damage=1)
    ]
    
    placed_items = {} # Use a dict to store items and their grid position: {(x,y): item}
    selected_item = None # This will be the CLONE of a shop item that is being dragged
    
    # --- UI Elements ---
    font = pygame.font.SysFont(None, 30)
    calc_button = pygame.Rect(600, 500, 200, 50)


    # --- Game Loop ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked_on_item = False
                    # Priority 1: Pick up an item from the backpack
                    # Use list() to create a copy, allowing us to modify the dictionary while iterating
                    for pos, item in list(placed_items.items()):
                        item_rect_on_grid = pygame.Rect(
                            BACKPACK_X + pos[0] * GRID_SIZE,
                            BACKPACK_Y + pos[1] * GRID_SIZE,
                            item.rect.width,
                            item.rect.height
                        )
                        if item_rect_on_grid.collidepoint(event.pos):
                            selected_item = item
                            selected_item.dragging = True
                            # Move the item's own rect to its current screen position before calculating offset
                            selected_item.rect.topleft = item_rect_on_grid.topleft
                            mouse_x, mouse_y = event.pos
                            offset_x = selected_item.rect.x - mouse_x
                            offset_y = selected_item.rect.y - mouse_y
                            del placed_items[pos] # Remove from backpack to "pick it up"
                            clicked_on_item = True
                            break # Item found, stop searching
                    
                    # Priority 2: If nothing was picked from backpack, pick from shop
                    if not clicked_on_item:
                        for item_template in items_in_shop:
                            if item_template.rect.collidepoint(event.pos):
                                # Create a clone of the item to drag
                                selected_item = Item(
                                    item_template.rect.x, item_template.rect.y, item_template.name, 
                                    item_template.rarity, item_template.shape_matrix, item_template.damage
                                )
                                selected_item.dragging = True
                                mouse_x, mouse_y = event.pos
                                offset_x = selected_item.rect.x - mouse_x
                                offset_y = selected_item.rect.y - mouse_y
                                break
                            
                    # Check for button click
                    if calc_button.collidepoint(event.pos):
                        print("--- Calculating Interactions ---")
                        for pos, item in placed_items.items():
                            print(f"Placed {item.name} at {pos}")

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and selected_item:
                    selected_item.dragging = False
                    
                    # Snap to backpack grid based on the item's top-left corner
                    # Using round() snaps to the NEAREST cell, which feels more natural
                    grid_x = round((selected_item.rect.left - BACKPACK_X) / GRID_SIZE)
                    grid_y = round((selected_item.rect.top - BACKPACK_Y) / GRID_SIZE)

                    # Check if placement is valid (within bounds)
                    if 0 <= grid_x < BACKPACK_COLS and 0 <= grid_y < BACKPACK_ROWS:
                        placed_items[(grid_x, grid_y)] = selected_item
                    
                    # The dragged item is now either placed or discarded, so we clear the reference
                    selected_item = None
                    
            elif event.type == pygame.MOUSEMOTION:
                if selected_item and selected_item.dragging:
                    mouse_x, mouse_y = event.pos
                    selected_item.rect.x = mouse_x + offset_x
                    selected_item.rect.y = mouse_y + offset_y

        # --- Drawing ---
        screen.fill(BG_COLOR)
        
        # Draw Backpack
        backpack_rect = pygame.Rect(BACKPACK_X, BACKPACK_Y, BACKPACK_COLS * GRID_SIZE, BACKPACK_ROWS * GRID_SIZE)
        pygame.draw.rect(screen, (230, 230, 230), backpack_rect)
        for x in range(BACKPACK_X, backpack_rect.right, GRID_SIZE):
            pygame.draw.line(screen, GRID_LINE_COLOR, (x, BACKPACK_Y), (x, backpack_rect.bottom))
        for y in range(BACKPACK_Y, backpack_rect.bottom, GRID_SIZE):
            pygame.draw.line(screen, GRID_LINE_COLOR, (BACKPACK_X, y), (backpack_rect.right, y))

        # Draw placed items
        for (grid_x, grid_y), item in placed_items.items():
            item.draw_at_grid(screen, grid_x, grid_y)
            
        # Draw shop items (they never move)
        for item in items_in_shop:
            screen.blit(item.image, item.rect)
        
        # Draw the selected item clone while it's being dragged
        if selected_item and selected_item.dragging:
            screen.blit(selected_item.image, selected_item.rect)

        # Draw Button
        pygame.draw.rect(screen, (100, 200, 100), calc_button)
        btn_text = font.render("Calculate", True, FONT_COLOR)
        screen.blit(btn_text, btn_text.get_rect(center=calc_button.center))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()