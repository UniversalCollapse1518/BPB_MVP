import pygame
import sys
from enum import Enum
from typing import List, Optional

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 50
GRID_COLOR = (200, 200, 200)
BG_COLOR = (255, 255, 255)
FONT_COLOR = (10, 10, 10)

# Backpack dimensions (UPDATED)
BACKPACK_COLS = 9
BACKPACK_ROWS = 7

# --- Enums for Item Properties ---

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

# --- Rarity Colors for Display ---
RARITY_COLORS = {
    Rarity.COMMON: (220, 220, 220), # A lighter grey for the fill
    Rarity.RARE: (135, 206, 250), # A lighter blue
    Rarity.EPIC: (221, 160, 221), # A lighter purple
    Rarity.LEGENDARY: (255, 218, 185), # A lighter orange
    Rarity.GODLY: (255, 250, 205), # A lighter yellow
    Rarity.UNIQUE: (255, 182, 193)  # A lighter pink
}

# --- Rarity Border Colors for Display ---
RARITY_BORDER_COLORS = {
    Rarity.COMMON: (150, 150, 150),
    Rarity.RARE: (0, 100, 255),
    Rarity.EPIC: (138, 43, 226),
    Rarity.LEGENDARY: (255, 165, 0),
    Rarity.GODLY: (255, 215, 0),
    Rarity.UNIQUE: (255, 20, 147)
}


# --- Item Class (UPDATED) ---
class Item(pygame.sprite.Sprite):
    """A class for a draggable item with detailed properties."""
    def __init__(self, width, height, x, y, name: str,
                 rarity: Rarity, item_class: ItemClass,
                 elements: Optional[List[Element]] = None,
                 types: Optional[List[ItemType]] = None,
                 damage: int = 0, cooldown: float = 0.0):
        super().__init__()
        
        # Core Properties
        self.name = name
        self.rarity = rarity
        self.item_class = item_class
        self.elements = elements or []
        self.types = types or []
        
        # Stats
        self.damage = damage
        self.cooldown = cooldown
        
        # Pygame properties
        self.color = RARITY_COLORS[self.rarity] # Color is now based on rarity
        self.image = pygame.Surface([width, height])
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.dragging = False

    def draw(self, screen):
        """Draws the item and its stats on the screen."""
        # Draw rarity border
        pygame.draw.rect(screen, RARITY_BORDER_COLORS[self.rarity], self.rect, 5)
        
        # Draw the item block
        screen.blit(self.image, self.rect)
        
        # Setup font
        font = pygame.font.SysFont(None, 24)
        
        # Draw the name
        name_text = font.render(self.name, True, FONT_COLOR)
        name_rect = name_text.get_rect(center=(self.rect.centerx, self.rect.centery - 10))
        screen.blit(name_text, name_rect)

        # Draw the stats
        stats_text = font.render(f"Dmg: {self.damage}", True, FONT_COLOR)
        stats_rect = stats_text.get_rect(center=(self.rect.centerx, self.rect.centery + 10))
        screen.blit(stats_text, stats_rect)


# --- Main Game Function ---
def game_loop():
    """Main function to run the backpack simulator."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Backpack Battles Simulator - Properties")
    clock = pygame.time.Clock()

    # --- Create Items (UPDATED, no color argument) ---
    all_sprites = pygame.sprite.Group()
    
    sword = Item(
        GRID_SIZE, GRID_SIZE, 550, 50, 
        name="Sword",
        rarity=Rarity.COMMON,
        item_class=ItemClass.NEUTRAL,
        elements=[Element.MELEE],
        types=[ItemType.WEAPON],
        damage=5, cooldown=1.8
    )
    
    shield = Item(
        GRID_SIZE * 2, GRID_SIZE, 550, 150, 
        name="Shield",
        rarity=Rarity.RARE,
        item_class=ItemClass.NEUTRAL,
        elements=[],
        types=[ItemType.SHIELD],
        damage=1, cooldown=2.0
    )
    
    all_sprites.add(sword, shield)
    
    selected_item = None

    # --- Backpack Grid ---
    backpack_rect = pygame.Rect(50, 50, BACKPACK_COLS * GRID_SIZE, BACKPACK_ROWS * GRID_SIZE)

    # --- Game Loop (Logic remains the same) ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for item in all_sprites:
                        if item.rect.collidepoint(event.pos):
                            selected_item = item
                            selected_item.dragging = True
                            mouse_x, mouse_y = event.pos
                            offset_x = selected_item.rect.x - mouse_x
                            offset_y = selected_item.rect.y - mouse_y
                            break

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and selected_item:
                    selected_item.dragging = False
                    if backpack_rect.colliderect(selected_item.rect):
                        grid_x = (selected_item.rect.centerx - backpack_rect.left) // GRID_SIZE
                        grid_y = (selected_item.rect.centery - backpack_rect.top) // GRID_SIZE
                        
                        grid_x = max(0, min(grid_x, BACKPACK_COLS - (selected_item.rect.width // GRID_SIZE)))
                        grid_y = max(0, min(grid_y, BACKPACK_ROWS - (selected_item.rect.height // GRID_SIZE)))
                        
                        selected_item.rect.left = backpack_rect.left + grid_x * GRID_SIZE
                        selected_item.rect.top = backpack_rect.top + grid_y * GRID_SIZE
                    
                    selected_item = None

            elif event.type == pygame.MOUSEMOTION:
                if selected_item and selected_item.dragging:
                    mouse_x, mouse_y = event.pos
                    selected_item.rect.x = mouse_x + offset_x
                    selected_item.rect.y = mouse_y + offset_y

        # --- Drawing ---
        screen.fill(BG_COLOR)
        
        pygame.draw.rect(screen, (230, 230, 230), backpack_rect)
        for x in range(backpack_rect.left, backpack_rect.right, GRID_SIZE):
            for y in range(backpack_rect.top, backpack_rect.bottom, GRID_SIZE):
                rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(screen, GRID_COLOR, rect, 1)

        for sprite in all_sprites:
            sprite.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()

