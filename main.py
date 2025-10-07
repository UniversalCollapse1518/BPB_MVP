import pygame
import sys

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 50
GRID_COLOR = (200, 200, 200)
BG_COLOR = (255, 255, 255)
FONT_COLOR = (10, 10, 10)

# Backpack dimensions (e.g., 5x5 grid)
BACKPACK_COLS = 5
BACKPACK_ROWS = 5

# --- Item Class (UPDATED) ---
class Item(pygame.sprite.Sprite):
    """A class for a draggable item with stats."""
    def __init__(self, color, width, height, x, y, name="Item", damage=0, cooldown=0.0):
        super().__init__()
        self.color = color
        self.name = name
        self.damage = damage
        self.cooldown = cooldown
        
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.dragging = False

    def draw(self, screen):
        """Draws the item and its stats on the screen."""
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
    pygame.display.set_caption("Backpack Battles Simulator - MVP")
    clock = pygame.time.Clock()

    # --- Create Items (UPDATED with stats) ---
    all_sprites = pygame.sprite.Group()
    item1 = Item((255, 100, 100), GRID_SIZE, GRID_SIZE, 550, 50, name="Sword", damage=5, cooldown=1.8)
    item2 = Item((100, 100, 255), GRID_SIZE * 2, GRID_SIZE, 550, 150, name="Shield", damage=1, cooldown=2.0)
    all_sprites.add(item1, item2)
    
    selected_item = None

    # --- Backpack Grid ---
    backpack_rect = pygame.Rect(50, 50, BACKPACK_COLS * GRID_SIZE, BACKPACK_ROWS * GRID_SIZE)

    # --- Game Loop (No changes here, logic remains the same) ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    for item in all_sprites:
                        if item.rect.collidepoint(event.pos):
                            selected_item = item
                            selected_item.dragging = True
                            mouse_x, mouse_y = event.pos
                            offset_x = selected_item.rect.x - mouse_x
                            offset_y = selected_item.rect.y - mouse_y
                            break

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and selected_item: # Left click release
                    selected_item.dragging = False
                    # Snap to grid logic
                    if backpack_rect.colliderect(selected_item.rect):
                        grid_x = (selected_item.rect.centerx - backpack_rect.left) // GRID_SIZE
                        grid_y = (selected_item.rect.centery - backpack_rect.top) // GRID_SIZE
                        
                        # Clamp to backpack bounds
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
        
        # Draw backpack grid
        pygame.draw.rect(screen, (230, 230, 230), backpack_rect) # Backpack background
        for x in range(backpack_rect.left, backpack_rect.right, GRID_SIZE):
            for y in range(backpack_rect.top, backpack_rect.bottom, GRID_SIZE):
                rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(screen, GRID_COLOR, rect, 1)

        # Draw items
        for sprite in all_sprites:
            sprite.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()


