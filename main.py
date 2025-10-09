import pygame
import sys
import json
from enum import Enum
from typing import List, Optional, Dict, Tuple
import math
from datetime import datetime
import copy

from definitions import GridType, Rarity, ItemClass, Element, ItemType

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
GRID_SIZE = 40
BACKPACK_COLS, BACKPACK_ROWS = 9, 7
BACKPACK_X, BACKPACK_Y = 50, 50
PANEL_START_X = BACKPACK_X + (BACKPACK_COLS * GRID_SIZE) + 50
PANEL_Y = 50
PANEL_HEIGHT = 550
INFO_PANEL_X, INFO_PANEL_WIDTH = PANEL_START_X, 350
SHOP_X, SHOP_WIDTH = INFO_PANEL_X + INFO_PANEL_WIDTH + 20, 200

BG_COLOR = (255, 255, 255)
FONT_COLOR = (10, 10, 10)
GRID_LINE_COLOR = (200, 200, 200)
INVALID_PLACEMENT_COLOR = (255, 0, 0, 100)

RARITY_BORDER_COLORS = {
    Rarity.COMMON: (150, 150, 150), Rarity.RARE: (0, 100, 255), Rarity.EPIC: (138, 43, 226),
    Rarity.LEGENDARY: (255, 165, 0), Rarity.GODLY: (255, 215, 0), Rarity.UNIQUE: (255, 20, 147)
}
STAR_SHAPE_COLORS = {
    GridType.STAR_A: (255, 215, 0), GridType.STAR_B: (50, 205, 50), GridType.STAR_C: (148, 0, 211)
}

class Item(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, name: str, rarity: Rarity,
                 item_class: ItemClass, elements: List[Element], types: List[ItemType],
                 shape_matrix: List[List[GridType]], base_score: int, star_effects: dict):
        super().__init__()
        self.name = name
        self.rarity = rarity
        self.item_class = item_class
        self.elements = elements
        self.types = types
        self.shape_matrix = shape_matrix
        self.base_score = base_score
        self.star_effects = star_effects

        self.grid_width = len(shape_matrix[0]) if shape_matrix else 0
        self.grid_height = len(shape_matrix)
        self.body_image = self.create_body_surface()
        self.rect = self.body_image.get_rect(topleft=(x, y))
        self.base_y = y
        self.dragging = False

        self.gx = -1
        self.gy = -1

        self.final_score = 0
        self.score_modifiers = []
        self.activated_stars = {GridType.STAR_A: 0, GridType.STAR_B: 0, GridType.STAR_C: 0}
        self.occupying_stars = []

    def get_body_offset(self) -> Tuple[int, int]:
        for r, row in enumerate(self.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED:
                    return (c, r)
        return (0, 0)

    def create_body_surface(self) -> pygame.Surface:
        width_px, height_px = self.grid_width * GRID_SIZE, self.grid_height * GRID_SIZE
        surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
        occupied_coords = [(c, r) for r, row in enumerate(self.shape_matrix) for c, cell in enumerate(row) if cell == GridType.OCCUPIED]
        if occupied_coords:
            for c, r in occupied_coords:
                pygame.draw.rect(surface, (200, 200, 200), (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE))
                pygame.draw.rect(surface, RARITY_BORDER_COLORS[self.rarity], (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE), 2)
            min_c, max_c = min(c for c,r in occupied_coords), max(c for c,r in occupied_coords)
            min_r, max_r = min(r for c,r in occupied_coords), max(r for c,r in occupied_coords)
            center_x, center_y = (min_c + max_c + 1) * GRID_SIZE / 2, (min_r + max_r + 1) * GRID_SIZE / 2
            font = pygame.font.SysFont(None, 20)
            name_text = (self.name[:4] + '..') if len(self.name) > 6 else self.name
            text_surf = font.render(name_text, True, FONT_COLOR)
            surface.blit(text_surf, text_surf.get_rect(center=(center_x, center_y)))
        return surface

    def draw_stars(self, screen: pygame.Surface, top_left_pos: Tuple[int, int]):
        for r, row in enumerate(self.shape_matrix):
            for c, cell in enumerate(row):
                if cell in STAR_SHAPE_COLORS:
                    cx, cy = top_left_pos[0] + c*GRID_SIZE + GRID_SIZE//2, top_left_pos[1] + r*GRID_SIZE + GRID_SIZE//2
                    color = STAR_SHAPE_COLORS[cell]
                    if cell == GridType.STAR_A:
                        pts = [(cx + (GRID_SIZE/2 if a==18 else GRID_SIZE/4)*math.cos(math.radians(a+i*72)), cy + (GRID_SIZE/2 if a==18 else GRID_SIZE/4)*math.sin(math.radians(a+i*72))) for i in range(5) for a in [18,54]]
                        pygame.draw.polygon(screen, color, pts)
                    elif cell == GridType.STAR_B: pygame.draw.polygon(screen, color, [(cx,cy-GRID_SIZE*0.4),(cx+GRID_SIZE*0.4,cy),(cx,cy+GRID_SIZE*0.4),(cx-GRID_SIZE*0.4,cy)])
                    elif cell == GridType.STAR_C: pygame.draw.polygon(screen, color, [(cx,cy-GRID_SIZE*0.35),(cx-GRID_SIZE*0.35,cy+GRID_SIZE*0.35),(cx+GRID_SIZE*0.35,cy+GRID_SIZE*0.35)])

    def is_mouse_over_body(self, mouse_pos: Tuple[int, int], current_pos: Tuple[int, int]) -> bool:
        for r, row in enumerate(self.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED and pygame.Rect(current_pos[0]+c*GRID_SIZE, current_pos[1]+r*GRID_SIZE, GRID_SIZE, GRID_SIZE).collidepoint(mouse_pos):
                    return True
        return False
        
    def rotate(self):
        self.shape_matrix = [list(row)[::-1] for row in zip(*self.shape_matrix)]
        self.grid_height, self.grid_width = len(self.shape_matrix), len(self.shape_matrix[0])
        self.body_image = self.create_body_surface()

class CalculationEngine:
    def _check_condition(self, condition_data: dict, source_item: Item, target_item: Optional[Item]) -> bool:
        if condition_data.get("requires_empty", False): return target_item is None
        if target_item is None: return False
        if "requires_element" in condition_data and Element[condition_data["requires_element"]] not in target_item.elements: return False
        if "requires_type" in condition_data and ItemType[condition_data["requires_type"]] not in target_item.types: return False
        if condition_data.get("must_be_different", False) and source_item.name == target_item.name: return False
        return True

    def _get_effect_value(self, effect_data: dict, source_item: Item) -> float:
        value_data = effect_data.get("value", 0)
        if isinstance(value_data, (int, float)): return value_data
        final_value = value_data.get("base", 0.0)
        if "dynamic_bonus" in value_data:
            bonus_data = value_data["dynamic_bonus"]
            per_star_type = GridType[bonus_data["per_activated_star"]]
            num_activated = source_item.activated_stars.get(per_star_type, 0)
            final_value += num_activated * bonus_data.get("add", 0)
        return final_value

    def run(self, placed_items: Dict[Tuple[int, int], Item]):
        occupancy_grid: List[List[Optional[Item]]] = [[None for _ in range(BACKPACK_COLS)] for _ in range(BACKPACK_ROWS)]
        for item in placed_items.values():
            item.final_score, item.score_modifiers, item.occupying_stars = item.base_score, [], []
            item.activated_stars = {GridType.STAR_A: 0, GridType.STAR_B: 0, GridType.STAR_C: 0}
        
        for item in placed_items.values():
            gx, gy = item.gx, item.gy
            for r, row in enumerate(item.shape_matrix):
                for c, cell in enumerate(row):
                    if cell == GridType.OCCUPIED and 0 <= gy+r < BACKPACK_ROWS and 0 <= gx+c < BACKPACK_COLS:
                        occupancy_grid[gy+r][gx+c] = item

        for source_item in placed_items.values():
            gx, gy = source_item.gx, source_item.gy
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

        all_effects = []
        for source_item in placed_items.values():
            gx, gy = source_item.gx, source_item.gy
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
        
        for effect_type in ["ADD_SCORE_TO_SELF", "ADD_SCORE_TO_TARGET"]:
            for eff in all_effects:
                if eff["effect"] == effect_type:
                    if eff["effect"] == "ADD_SCORE_TO_SELF": eff["source"].final_score += eff["value"]; eff["source"].score_modifiers.append(f"+{eff['value']:.1f} (self)")
                    elif eff["target"]: eff["target"].final_score += eff["value"]; eff["target"].score_modifiers.append(f"+{eff['value']:.1f} from {eff['source'].name}")
        for effect_type in ["MULTIPLY_SCORE_OF_SELF", "MULTIPLY_SCORE_OF_TARGET"]:
            for eff in all_effects:
                if eff["effect"] == effect_type:
                    if eff["effect"] == "MULTIPLY_SCORE_OF_SELF": eff["source"].final_score *= eff["value"]; eff["source"].score_modifiers.append(f"x{eff['value']:.2f} (self)")
                    elif eff["target"]: eff["target"].final_score *= eff["value"]; eff["target"].score_modifiers.append(f"x{eff['value']:.2f} from {eff['source'].name}")

def load_items_from_file(filepath: str) -> List[Item]:
    items = []
    try:
        with open(filepath, 'r') as f: data = json.load(f)
        y_offset = 0
        for item_data in data.values():
            item = Item(SHOP_X+10, PANEL_Y+10+y_offset, item_data['name'], Rarity[item_data['rarity']], 
                        ItemClass[item_data['item_class']], [Element[e] for e in item_data.get('elements', [])], 
                        [ItemType[t] for t in item_data.get('types', [])], [[GridType(c) for c in r] for r in item_data['shape_matrix']],
                        item_data.get('base_score', 0), item_data.get('star_effects', {}))
            items.append(item)
            y_offset += item.rect.height + 10
    except Exception as e: print(f"Error loading items: {e}")
    return items

def is_placement_valid(item: Item, gx: int, gy: int, items_dict: Dict[Tuple[int, int], Item]) -> bool:
    occupied_cells = set()
    for p_item in items_dict.values():
        px, py = p_item.gx, p_item.gy
        for r, row in enumerate(p_item.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED:
                    occupied_cells.add((px + c, py + r))
    for r, row in enumerate(item.shape_matrix):
        for c, cell in enumerate(row):
            if cell == GridType.OCCUPIED:
                ax, ay = gx + c, gy + r
                if not(0<=ax<BACKPACK_COLS and 0<=ay<BACKPACK_ROWS): return False
                if(ax,ay) in occupied_cells: return False
    return True

def log_event(event_name: str, placed_items: Dict[Tuple[int, int], Item]):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    placed_items_repr = {pos: item.name for pos, item in placed_items.items()}
    print(f"[{timestamp}] - {event_name} - {placed_items_repr}")

def game_loop():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Backpack Battles - Final Scoring Engine")
    clock = pygame.time.Clock()

    items_in_shop = load_items_from_file('items.json')
    placed_items = {}
    selected_item = None
    engine = CalculationEngine()
    
    font_large, font_medium, font_small = pygame.font.SysFont(None, 32), pygame.font.SysFont(None, 24), pygame.font.SysFont(None, 20)
    calc_button = pygame.Rect(PANEL_START_X, 660, INFO_PANEL_WIDTH + SHOP_WIDTH + 20, 30)
    shop_area_rect, info_panel_rect = pygame.Rect(SHOP_X, PANEL_Y, SHOP_WIDTH, PANEL_HEIGHT), pygame.Rect(INFO_PANEL_X, PANEL_Y, INFO_PANEL_WIDTH, PANEL_HEIGHT)
    
    shop_scroll_y, info_scroll_y = 0, 0
    total_shop_height = sum(item.rect.height + 10 for item in items_in_shop) if items_in_shop else 0
    total_score = 0
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                log_event(f"MOUSEBUTTONDOWN_{event.button}", placed_items)

                if event.button == 4:
                    if shop_area_rect.collidepoint(mouse_pos): shop_scroll_y = max(0, shop_scroll_y - 20)
                    if info_panel_rect.collidepoint(mouse_pos): info_scroll_y = max(0, info_scroll_y - 20)
                elif event.button == 5:
                    if shop_area_rect.collidepoint(mouse_pos):
                        shop_scroll_y = min(max(0, total_shop_height - shop_area_rect.height), shop_scroll_y + 20)
                    if info_panel_rect.collidepoint(mouse_pos):
                        info_h = 50 + sum(160 + len(i.score_modifiers)*20 + len(i.occupying_stars)*20 for i in placed_items.values())
                        info_scroll_y = min(max(0, info_h - info_panel_rect.height), info_scroll_y + 20)
                elif event.button == 3 and selected_item and selected_item.dragging:
                    rx, ry = mouse_pos[0]-selected_item.rect.x, mouse_pos[1]-selected_item.rect.y
                    pc, pr = rx // GRID_SIZE, ry // GRID_SIZE; ogh = selected_item.grid_height
                    selected_item.rotate(); npc, npr = ogh-1-pr, pc
                    npx, npy = npc*GRID_SIZE, npr*GRID_SIZE
                    nr = selected_item.body_image.get_rect(x=mouse_pos[0]-npx, y=mouse_pos[1]-npy)
                    selected_item.rect, offset_x, offset_y = nr, nr.x-mouse_pos[0], nr.y-mouse_pos[1]
                elif event.button == 1:
                    item_to_pick_info = None
                    for key, item in reversed(list(placed_items.items())): 
                        item_pos_on_screen = (BACKPACK_X + item.gx * GRID_SIZE, BACKPACK_Y + item.gy * GRID_SIZE)
                        if item.is_mouse_over_body(mouse_pos, item_pos_on_screen):
                            item_to_pick_info = (key, item)
                            break 
                    if item_to_pick_info:
                        key, item = item_to_pick_info
                        selected_item = item
                        item_pos_on_screen = (BACKPACK_X + item.gx * GRID_SIZE, BACKPACK_Y + item.gy * GRID_SIZE)
                        offset_x = item_pos_on_screen[0] - mouse_pos[0]
                        offset_y = item_pos_on_screen[1] - mouse_pos[1]
                        selected_item.dragging = True
                        selected_item.rect.topleft = item_pos_on_screen
                        del placed_items[key]
                    else:
                        for item_t in items_in_shop:
                            if item_t.is_mouse_over_body(mouse_pos, item_t.rect.topleft):
                                selected_item = Item(item_t.rect.x, item_t.rect.y, item_t.name, item_t.rarity, item_t.item_class, item_t.elements, item_t.types, copy.deepcopy(item_t.shape_matrix), item_t.base_score, item_t.star_effects)
                                selected_item.dragging = True; offset_x, offset_y = item_t.rect.x-mouse_pos[0], item_t.rect.y-mouse_pos[1]; break
                    if calc_button.collidepoint(mouse_pos): 
                        engine.run(placed_items)
                        total_score = sum(item.final_score for item in placed_items.values())
            
            elif event.type == pygame.MOUSEBUTTONUP:
                log_event("MOUSEBUTTONUP", placed_items)
                if event.button == 1 and selected_item:
                    selected_item.dragging = False
                    
                    gx = round((selected_item.rect.left - BACKPACK_X) / GRID_SIZE)
                    gy = round((selected_item.rect.top - BACKPACK_Y) / GRID_SIZE)
                    
                    if is_placement_valid(selected_item, gx, gy, placed_items):
                        offset_c, offset_r = selected_item.get_body_offset()
                        unique_key = (gx + offset_c, gy + offset_r)

                        selected_item.gx = gx
                        selected_item.gy = gy

                        placed_items[unique_key] = selected_item
                    
                    selected_item = None

            elif event.type == pygame.MOUSEMOTION:
                if selected_item and selected_item.dragging:
                    selected_item.rect.x, selected_item.rect.y = mouse_pos[0]+offset_x, mouse_pos[1]+offset_y
        
        screen.fill(BG_COLOR)
        bp_rect = pygame.Rect(BACKPACK_X, BACKPACK_Y, BACKPACK_COLS*GRID_SIZE, BACKPACK_ROWS*GRID_SIZE)
        pygame.draw.rect(screen, (230,230,230), bp_rect); pygame.draw.rect(screen, (240,240,240), shop_area_rect, 2); 
        total_score_rect = pygame.Rect(info_panel_rect.left, info_panel_rect.bottom, info_panel_rect.width, 50)
        pygame.draw.rect(screen, (210, 210, 210), total_score_rect)
        pygame.draw.rect(screen, (180, 180, 180), total_score_rect, 2)
        pygame.draw.rect(screen, (220,220,220), info_panel_rect); pygame.draw.rect(screen, (180,180,180), info_panel_rect, 2)

        for x in range(bp_rect.left, bp_rect.right + 1, GRID_SIZE): pygame.draw.line(screen, GRID_LINE_COLOR, (x, bp_rect.top), (x, bp_rect.bottom))
        for y in range(bp_rect.top, bp_rect.bottom + 1, GRID_SIZE): pygame.draw.line(screen, GRID_LINE_COLOR, (bp_rect.left, y), (bp_rect.right, y))

        screen.set_clip(info_panel_rect)
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
        screen.set_clip(None)
        
        total_score_text = f"Total Score: {total_score:.1f}"
        screen.blit(font_large.render(total_score_text, True, FONT_COLOR), (total_score_rect.x + 10, total_score_rect.centery - 16))

        all_items = [(item, (BACKPACK_X + item.gx * GRID_SIZE, BACKPACK_Y + item.gy * GRID_SIZE)) for item in placed_items.values()]
        for item in items_in_shop: item.rect.y=item.base_y-shop_scroll_y; all_items.append((item, item.rect.topleft))
        for item, pos in all_items:
            if shop_area_rect.colliderect(pygame.Rect(pos, item.body_image.get_size())) or info_panel_rect.x > pos[0]: screen.blit(item.body_image, pos)
        for item, pos in all_items:
            if item.is_mouse_over_body(mouse_pos, pos):
                is_in_shop = shop_area_rect.colliderect(pygame.Rect(pos, item.body_image.get_size()))
                if is_in_shop: screen.set_clip(shop_area_rect)
                item.draw_stars(screen, pos)
                if is_in_shop: screen.set_clip(None)

        if selected_item and selected_item.dragging:
            screen.blit(selected_item.body_image, selected_item.rect)
            selected_item.draw_stars(screen, selected_item.rect.topleft)
            gx = round((selected_item.rect.left - BACKPACK_X) / GRID_SIZE)
            gy = round((selected_item.rect.top - BACKPACK_Y) / GRID_SIZE)
            if not is_placement_valid(selected_item, gx, gy, placed_items):
                tint = pygame.Surface(selected_item.rect.size, pygame.SRCALPHA); tint.fill(INVALID_PLACEMENT_COLOR)
                screen.blit(tint, selected_item.rect.topleft)

        pygame.draw.rect(screen, (100, 200, 100), calc_button)
        screen.blit(font_medium.render("Calculate", True, FONT_COLOR), calc_button.inflate(-10,-10))

        debug_y_offset = bp_rect.bottom + 10
        mouse_pos_text = f"Mouse Position: {mouse_pos}"
        screen.blit(font_small.render(mouse_pos_text, True, FONT_COLOR), (bp_rect.left, debug_y_offset)); debug_y_offset += 20
        dragging_item_text = f"Dragging: {selected_item.name if selected_item else 'None'}"
        screen.blit(font_small.render(dragging_item_text, True, FONT_COLOR), (bp_rect.left, debug_y_offset)); debug_y_offset += 20
        screen.blit(font_small.render("Placed Items:", True, FONT_COLOR), (bp_rect.left, debug_y_offset)); debug_y_offset += 20
        if placed_items:
            item_strings = [f"{pos}: '{item.name}'" for pos, item in placed_items.items()]
            for i in range(0, len(item_strings), 2):
                line_text = item_strings[i]
                if i + 1 < len(item_strings): line_text += f",   {item_strings[i+1]}"
                screen.blit(font_small.render(line_text, True, FONT_COLOR), (bp_rect.left + 15, debug_y_offset)); debug_y_offset += 20
        else:
            screen.blit(font_small.render("  None", True, FONT_COLOR), (bp_rect.left + 15, debug_y_offset)); debug_y_offset += 20

        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__": 
    game_loop()

