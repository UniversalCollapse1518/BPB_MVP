import pygame
import sys
import json
import copy
import os
import importlib.util
import inspect
from typing import List, Dict, Tuple, Type
from tkinter import filedialog
import tkinter as tk
from datetime import datetime

from definitions import GridType, Rarity, ItemClass, Element, ItemType
from engine import Item, CalculationEngine
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from solvers.base_solver import BaseSolver

root = tk.Tk()
root.withdraw()

# --- MODIFIED: Final adjusted panel widths ---
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 768
GRID_SIZE = 40
BACKPACK_COLS, BACKPACK_ROWS = 9, 7
BACKPACK_X, BACKPACK_Y = 50, 50
PANEL_START_X = BACKPACK_X + (BACKPACK_COLS * GRID_SIZE) + 50
PANEL_Y = 50
PANEL_HEIGHT = 630
SHOP_WIDTH = 300
INFO_PANEL_WIDTH = 420  # Reduced width
NEUTRAL_PANEL_WIDTH = 380 # Increased width
SHOP_X = PANEL_START_X
INFO_PANEL_X = SHOP_X + SHOP_WIDTH + 20
NEUTRAL_PANEL_X = INFO_PANEL_X + INFO_PANEL_WIDTH + 20

BG_COLOR = (255, 255, 255)
FONT_COLOR = (10, 10, 10)
GRID_LINE_COLOR = (200, 200, 200)
INVALID_PLACEMENT_COLOR = (255, 0, 0, 100)
RARITY_BORDER_COLORS = { Rarity.COMMON: (150, 150, 150), Rarity.RARE: (0, 100, 255), Rarity.EPIC: (138, 43, 226), Rarity.LEGENDARY: (255, 165, 0), Rarity.GODLY: (255, 215, 0), Rarity.UNIQUE: (255, 20, 147) }
STAR_SHAPE_COLORS = { GridType.STAR_A: (255, 215, 0), GridType.STAR_B: (50, 205, 50), GridType.STAR_C: (148, 0, 211) }

def save_layout(placed_items: Dict):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    default_filename = f"layout_{timestamp}.json"
    filepath = filedialog.asksaveasfilename(initialfile=default_filename, defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")], title="Save Backpack Layout")
    if not filepath: return
    layout_data = []
    for item in placed_items.values():
        layout_data.append({"name": item.name, "gx": item.gx, "gy": item.gy, "shape_matrix": [[c.value for c in r] for r in item.shape_matrix]})
    with open(filepath, 'w') as f: json.dump(layout_data, f, indent=2)
    print(f"Layout saved to {filepath}")

def load_layout(full_item_data: Dict) -> Dict:
    filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")], title="Load Backpack Layout")
    if not filepath: return {}
    new_placed_items = {}
    try:
        with open(filepath, 'r') as f: layout_data = json.load(f)
        for item_info in layout_data:
            item_name = item_info["name"]
            base_item_data = next((data for data in full_item_data.values() if data['name'] == item_name), None)
            if base_item_data:
                item = Item(0, 0, item_name, Rarity[base_item_data['rarity']], ItemClass[base_item_data['item_class']], [Element[e] for e in base_item_data.get('elements', [])], [ItemType[t] for t in base_item_data.get('types', [])], [[GridType(c) for c in r] for r in item_info['shape_matrix']], base_item_data.get('base_score', 0), base_item_data.get('star_effects', {}), base_item_data.get('has_cooldown', False), base_item_data.get('is_start_of_battle', False), base_item_data.get('passive_effects', []))
                item.gx, item.gy = item_info["gx"], item_info["gy"]
                key = (item.gx + item.get_body_offset()[1], item.gy + item.get_body_offset()[0])
                new_placed_items[key] = item
    except Exception as e:
        print(f"Error loading layout: {e}")
        return {}
    print(f"Layout loaded from {filepath}")
    return new_placed_items

def load_items_from_file(filepath: str) -> List[Item]:
    items = []
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        x_margin, y_margin = 10, 10
        current_x = SHOP_X + x_margin
        current_y = PANEL_Y + y_margin
        max_row_height = 0

        sorted_item_data = sorted(data.values(), key=lambda x: x['name'])

        for item_data in sorted_item_data:
            item = Item(0, 0, item_data['name'], Rarity[item_data['rarity']],
                        ItemClass[item_data['item_class']], [Element[e] for e in item_data.get('elements', [])],
                        [ItemType[t] for t in item_data.get('types', [])], [[GridType(c) for c in r] for r in item_data['shape_matrix']],
                        item_data.get('base_score', 0), item_data.get('star_effects', {}),
                        item_data.get('has_cooldown', False), item_data.get('is_start_of_battle', False),
                        item_data.get('passive_effects', []))
            
            body_bounds = item.get_body_bounds()
            if not body_bounds: continue

            min_r, min_c, max_r, max_c = body_bounds
            body_width_px = (max_c - min_c + 1) * GRID_SIZE
            body_height_px = (max_r - min_r + 1) * GRID_SIZE

            if current_x + body_width_px > SHOP_X + SHOP_WIDTH - x_margin:
                current_y += max_row_height + y_margin
                current_x = SHOP_X + x_margin
                max_row_height = 0
            
            item.rect.topleft = (current_x - (min_c * GRID_SIZE), current_y - (min_r * GRID_SIZE))
            item.base_y = item.rect.y

            items.append(item)
            
            current_x += body_width_px + x_margin
            max_row_height = max(max_row_height, body_height_px)

    except Exception as e:
        print(f"Error loading items: {e}")
    return items

def discover_solvers() -> Dict[str, Type[BaseSolver]]:
    solvers = {}
    solver_dir = 'solvers'
    def format_name(name): return name.replace('Solver', '')
    for filename in os.listdir(solver_dir):
        if filename.endswith('.py') and filename != 'base_solver.py':
            module_name = f"{solver_dir}.{filename[:-3]}"
            spec = importlib.util.spec_from_file_location(module_name, os.path.join(solver_dir, filename))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseSolver) and obj is not BaseSolver: solvers[format_name(name)] = obj
    return solvers

def is_placement_valid(item: Item, gx: int, gy: int, items_dict: Dict[Tuple[int, int], Item]) -> bool:
    occupied_cells = set()
    for p_item in items_dict.values():
        px, py = p_item.gx, p_item.gy
        for r, row in enumerate(p_item.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED: occupied_cells.add((px + c, py + r))
    for r, row in enumerate(item.shape_matrix):
        for c, cell in enumerate(row):
            if cell == GridType.OCCUPIED:
                ax, ay = gx + c, gy + r
                if not(0<=ax<BACKPACK_COLS and 0<=ay<BACKPACK_ROWS): return False
                if(ax,ay) in occupied_cells: return False
    return True

def game_loop():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Backpack Battles - Final Scoring Engine")
    clock = pygame.time.Clock()

    with open('items.json', 'r') as f:
        full_item_definitions = json.load(f)
    items_in_shop = load_items_from_file('items.json')

    placed_items = {}
    selected_item = None
    engine = CalculationEngine()
    
    available_solvers = discover_solvers()
    solver_names = list(available_solvers.keys())
    selected_solver_name = solver_names[0] if solver_names else "No Solvers Found"
    
    font_large = pygame.font.SysFont('verdana', 34)
    font_medium = pygame.font.SysFont('verdana', 26)
    font_small = pygame.font.SysFont('verdana', 21)
    font_button = pygame.font.SysFont('verdana', 18)

    dropdown_y = BACKPACK_Y + (BACKPACK_ROWS * GRID_SIZE) + 20
    dropdown_width = 220
    dropdown_rect = pygame.Rect(BACKPACK_X, dropdown_y, dropdown_width, 40)
    run_solver_button = pygame.Rect(dropdown_rect.right + 10, dropdown_y, 130, 40)
    dropdown_open = False

    save_load_y = run_solver_button.bottom + 10
    save_button = pygame.Rect(BACKPACK_X, save_load_y, 175, 40)
    load_button = pygame.Rect(save_button.right + 10, save_load_y, 175, 40)

    shop_area_rect = pygame.Rect(SHOP_X, PANEL_Y, SHOP_WIDTH, PANEL_HEIGHT)
    info_panel_rect = pygame.Rect(INFO_PANEL_X, PANEL_Y, INFO_PANEL_WIDTH, PANEL_HEIGHT)
    neutral_panel_rect = pygame.Rect(NEUTRAL_PANEL_X, PANEL_Y, NEUTRAL_PANEL_WIDTH, PANEL_HEIGHT)
    
    total_score_rect = pygame.Rect(PANEL_START_X, info_panel_rect.bottom + 5, SCREEN_WIDTH - PANEL_START_X - 30, 45)
    calc_button = pygame.Rect(PANEL_START_X, total_score_rect.bottom + 5, 150, 40)
    calc_text_surf = font_medium.render("Calculate", True, FONT_COLOR)

    shop_scroll_y, info_scroll_y, neutral_scroll_y = 0, 0, 0
    
    total_shop_height = 0
    if items_in_shop:
        max_y = 0
        for item in items_in_shop:
            if item.rect:
                body_bounds = item.get_body_bounds()
                if body_bounds:
                    min_r, _, max_r, _ = body_bounds
                    item_bottom = item.rect.y + (max_r * GRID_SIZE) + GRID_SIZE
                    max_y = max(max_y, item_bottom)
        total_shop_height = max_y - (PANEL_Y + 10)

    total_score = 0
    info_content_height = 0

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4: # Scroll Up
                    if shop_area_rect.collidepoint(mouse_pos): shop_scroll_y = max(0, shop_scroll_y - 20)
                    if info_panel_rect.collidepoint(mouse_pos): info_scroll_y = max(0, info_scroll_y - 20)
                    if neutral_panel_rect.collidepoint(mouse_pos): neutral_scroll_y = max(0, neutral_scroll_y - 20)
                elif event.button == 5: # Scroll Down
                    if shop_area_rect.collidepoint(mouse_pos):
                        shop_scroll_y = min(max(0, total_shop_height - shop_area_rect.height), shop_scroll_y + 20)
                    if info_panel_rect.collidepoint(mouse_pos):
                        info_scroll_y = min(max(0, info_content_height - info_panel_rect.height), info_scroll_y + 20)
                    if neutral_panel_rect.collidepoint(mouse_pos):
                        neutral_h = 55 + len(engine.neutral_pool_modifiers) * 25
                        neutral_scroll_y = min(max(0, neutral_h - neutral_panel_rect.height), neutral_scroll_y + 20)
                elif event.button == 3 and selected_item and selected_item.dragging:
                    rx, ry = mouse_pos[0]-selected_item.rect.x, mouse_pos[1]-selected_item.rect.y
                    pc, pr = rx // GRID_SIZE, ry // GRID_SIZE; ogh = selected_item.grid_height
                    selected_item.rotate(); npc, npr = ogh-1-pr, pc
                    npx, npy = npc*GRID_SIZE, npr*GRID_SIZE
                    nr = selected_item.body_image.get_rect(x=mouse_pos[0]-npx, y=mouse_pos[1]-npy)
                    selected_item.rect, offset_x, offset_y = nr, nr.x-mouse_pos[0], nr.y-mouse_pos[1]
                elif event.button == 1:
                    if save_button.collidepoint(mouse_pos):
                        save_layout(placed_items)
                        dropdown_open = False
                    elif load_button.collidepoint(mouse_pos):
                        placed_items = load_layout(full_item_definitions)
                        engine.run(placed_items, BACKPACK_COLS, BACKPACK_ROWS)
                        total_score = sum(item.final_score for item in placed_items.values()) + engine.neutral_pool_total
                        dropdown_open = False
                    elif dropdown_rect.collidepoint(mouse_pos):
                        dropdown_open = not dropdown_open
                    elif dropdown_open:
                        for i, name in enumerate(solver_names):
                            option_rect = pygame.Rect(dropdown_rect.left, dropdown_rect.bottom + i * 30, dropdown_rect.width, 30)
                            if option_rect.collidepoint(mouse_pos):
                                selected_solver_name = name
                                dropdown_open = False
                                break
                        else:
                           dropdown_open = False
                    elif run_solver_button.collidepoint(mouse_pos) and selected_solver_name in available_solvers:
                        items_in_backpack = list(placed_items.values())
                        if not items_in_backpack:
                            print("Solver Error: No items in the backpack to solve for.")
                        else:
                            SolverClass = available_solvers[selected_solver_name]
                            solver_instance = SolverClass(items_in_backpack, BACKPACK_COLS, BACKPACK_ROWS, initial_layout=placed_items)
                            print(f"Running {selected_solver_name} Solver...")
                            best_layout, best_score = solver_instance.solve()
                            placed_items = best_layout
                            engine.run(placed_items, BACKPACK_COLS, BACKPACK_ROWS)
                            total_score = sum(item.final_score for item in placed_items.values()) + engine.neutral_pool_total
                        dropdown_open = False
                    else:
                        dropdown_open = False
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
                            offset_x, offset_y = item_pos_on_screen[0] - mouse_pos[0], item_pos_on_screen[1] - mouse_pos[1]
                            selected_item.dragging, selected_item.rect.topleft = True, item_pos_on_screen
                            del placed_items[key]
                        else:
                            for item_t in items_in_shop:
                                if item_t.is_mouse_over_body(mouse_pos, item_t.rect.topleft):
                                    selected_item = Item(item_t.rect.x, item_t.rect.y, item_t.name, item_t.rarity, item_t.item_class, item_t.elements, item_t.types, copy.deepcopy(item_t.shape_matrix), item_t.base_score, item_t.star_effects, item_t.has_cooldown, item_t.is_start_of_battle, item_t.passive_effects)
                                    selected_item.dragging, offset_x, offset_y = True, item_t.rect.x - mouse_pos[0], item_t.rect.y - mouse_pos[1]
                                    break
                        if calc_button.collidepoint(mouse_pos):
                            engine.run(placed_items, BACKPACK_COLS, BACKPACK_ROWS)
                            total_score = sum(item.final_score for item in placed_items.values()) + engine.neutral_pool_total

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and selected_item:
                    selected_item.dragging = False
                    gx = round((selected_item.rect.left - BACKPACK_X) / GRID_SIZE)
                    gy = round((selected_item.rect.top - BACKPACK_Y) / GRID_SIZE)
                    if is_placement_valid(selected_item, gx, gy, placed_items):
                        offset_c, offset_r = selected_item.get_body_offset()
                        unique_key = (gx + offset_c, gy + offset_r)
                        selected_item.gx, selected_item.gy = gx, gy
                        placed_items[unique_key] = selected_item
                    selected_item = None

            elif event.type == pygame.MOUSEMOTION:
                if selected_item and selected_item.dragging:
                    selected_item.rect.x, selected_item.rect.y = mouse_pos[0]+offset_x, mouse_pos[1]+offset_y

        screen.fill(BG_COLOR)
        bp_rect = pygame.Rect(BACKPACK_X, BACKPACK_Y, BACKPACK_COLS*GRID_SIZE, BACKPACK_ROWS*GRID_SIZE)
        pygame.draw.rect(screen, (230,230,230), bp_rect); pygame.draw.rect(screen, (240,240,240), shop_area_rect, 2);
        pygame.draw.rect(screen, (210, 210, 210), total_score_rect); pygame.draw.rect(screen, (180, 180, 180), total_score_rect, 2)
        pygame.draw.rect(screen, (220,220,220), info_panel_rect); pygame.draw.rect(screen, (180,180,180), info_panel_rect, 2)
        pygame.draw.rect(screen, (225,225,215), neutral_panel_rect); pygame.draw.rect(screen, (180,180,170), neutral_panel_rect, 2)

        for x in range(bp_rect.left, bp_rect.right + 1, GRID_SIZE): pygame.draw.line(screen, GRID_LINE_COLOR, (x, bp_rect.top), (x, bp_rect.bottom))
        for y in range(bp_rect.top, bp_rect.bottom + 1, GRID_SIZE): pygame.draw.line(screen, GRID_LINE_COLOR, (bp_rect.left, y), (bp_rect.right, y))

        current_info_height = 55
        for item in placed_items.values():
            current_info_height += (30 + 25 * 3)
            if item.occupying_stars: current_info_height += 25 + len(item.occupying_stars) * 25
            current_info_height += 25 + len(item.score_modifiers) * 25
            current_info_height += 30 + 15
        info_content_height = current_info_height

        screen.set_clip(info_panel_rect)
        screen.blit(font_large.render("Backpack Contents", True, FONT_COLOR), (info_panel_rect.x+10, info_panel_rect.y+10-info_scroll_y))
        y_off = 55
        for item in placed_items.values():
            screen.blit(font_medium.render(f"- {item.name}", True, FONT_COLOR), (info_panel_rect.x+15, info_panel_rect.y+y_off-info_scroll_y)); y_off += 30
            elems = f"Elem: {', '.join(e.name for e in item.elements) or 'None'}"; types = f"Type: {', '.join(t.name for t in item.types) or 'None'}"
            screen.blit(font_small.render(elems, True, (60,60,60)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 25
            screen.blit(font_small.render(types, True, (60,60,60)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 25
            star_txt = f"Activated: A:{item.activated_stars[GridType.STAR_A]} B:{item.activated_stars[GridType.STAR_B]} C:{item.activated_stars[GridType.STAR_C]}"
            screen.blit(font_small.render(star_txt, True, (60,60,60)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 25
            if item.occupying_stars:
                screen.blit(font_small.render("Occupying:", True, (60,60,60)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 25
                for star_type, source_name in item.occupying_stars: screen.blit(font_small.render(f"  - {source_name}'s {star_type.name}", True, (80,80,80)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 25
            screen.blit(font_small.render(f"Base Score: {item.base_score}", True, (60,60,60)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 25
            for mod in item.score_modifiers: screen.blit(font_small.render(f"  {mod}", True, (20,100,20)), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 25
            screen.blit(font_medium.render(f"Final Score: {item.final_score:.1f}", True, FONT_COLOR), (info_panel_rect.x+25, info_panel_rect.y+y_off-info_scroll_y)); y_off += 30
            y_off += 15
        screen.set_clip(None)
        
        screen.set_clip(neutral_panel_rect)
        screen.blit(font_large.render("Neutral Pool", True, FONT_COLOR), (neutral_panel_rect.x + 10, neutral_panel_rect.y + 10 - neutral_scroll_y))
        screen.blit(font_medium.render(f"Total: {engine.neutral_pool_total:.1f}", True, FONT_COLOR), (neutral_panel_rect.x + 15, neutral_panel_rect.y + 55 - neutral_scroll_y))
        y_off_neutral = 90
        for mod in engine.neutral_pool_modifiers:
            screen.blit(font_small.render(mod, True, (100, 20, 20)), (neutral_panel_rect.x + 25, neutral_panel_rect.y + y_off_neutral - neutral_scroll_y)); y_off_neutral += 25
        screen.set_clip(None)


        total_score_surf = font_large.render(f"Total Score: {total_score:.1f}", True, FONT_COLOR)
        screen.blit(total_score_surf, total_score_surf.get_rect(center=total_score_rect.center))

        all_items = [(item, (BACKPACK_X + item.gx * GRID_SIZE, BACKPACK_Y + item.gy * GRID_SIZE)) for item in placed_items.values()]
        for item in items_in_shop: item.rect.y=item.base_y-shop_scroll_y; all_items.append((item, item.rect.topleft))
        
        hovered_item_to_draw_stars = None
        
        for item, pos in all_items:
            if item.is_mouse_over_body(mouse_pos, pos):
                hovered_item_to_draw_stars = (item, pos)

            if pos[0] < SHOP_X:
                screen.blit(item.body_image, pos)
            elif shop_area_rect.colliderect(pygame.Rect(pos, item.body_image.get_size())):
                screen.set_clip(shop_area_rect)
                screen.blit(item.body_image, pos)
                screen.set_clip(None)

        if selected_item and selected_item.dragging:
            screen.blit(selected_item.body_image, selected_item.rect)
            selected_item.draw_stars(screen, selected_item.rect.topleft)
            
            gx = round((selected_item.rect.left - BACKPACK_X) / GRID_SIZE)
            gy = round((selected_item.rect.top - BACKPACK_Y) / GRID_SIZE)
            if not is_placement_valid(selected_item, gx, gy, placed_items):
                tint = pygame.Surface(selected_item.rect.size, pygame.SRCALPHA); tint.fill(INVALID_PLACEMENT_COLOR)
                screen.blit(tint, selected_item.rect.topleft)

        pygame.draw.rect(screen, (100, 200, 100), calc_button)
        screen.blit(calc_text_surf, calc_text_surf.get_rect(center=calc_button.center))

        pygame.draw.rect(screen, (220, 220, 220), dropdown_rect); pygame.draw.rect(screen, (180, 180, 180), dropdown_rect, 2)
        dropdown_text = font_button.render(f"Solver: {selected_solver_name} ▼", True, FONT_COLOR)
        screen.blit(dropdown_text, dropdown_text.get_rect(center=dropdown_rect.center))
        
        run_text = font_button.render("Run Solver", True, FONT_COLOR)
        pygame.draw.rect(screen, (180, 180, 220), run_solver_button)
        screen.blit(run_text, run_text.get_rect(center=run_solver_button.center))

        pygame.draw.rect(screen, (200, 200, 180), save_button)
        save_text = font_button.render("Save Layout", True, FONT_COLOR)
        screen.blit(save_text, save_text.get_rect(center=save_button.center))

        pygame.draw.rect(screen, (180, 200, 200), load_button)
        load_text = font_button.render("Load Layout", True, FONT_COLOR)
        screen.blit(load_text, load_text.get_rect(center=load_button.center))

        debug_y_offset = dropdown_rect.bottom + 40
        mouse_pos_text = f"Mouse Position: {mouse_pos}"
        screen.blit(font_small.render(mouse_pos_text, True, FONT_COLOR), (bp_rect.left, debug_y_offset)); debug_y_offset += 25
        dragging_item_text = f"Dragging: {selected_item.name if selected_item else 'None'}"
        screen.blit(font_small.render(dragging_item_text, True, FONT_COLOR), (bp_rect.left, debug_y_offset)); debug_y_offset += 25
        screen.blit(font_small.render("Placed Items:", True, FONT_COLOR), (bp_rect.left, debug_y_offset)); debug_y_offset += 25
        if placed_items:
            item_strings = [f"{item.name} @ ({item.gx},{item.gy})" for item in placed_items.values()]
            for i in range(0, len(item_strings), 2):
                line_text = item_strings[i]
                if i + 1 < len(item_strings): line_text += f",   {item_strings[i+1]}"
                screen.blit(font_small.render(line_text, True, FONT_COLOR), (bp_rect.left + 15, debug_y_offset)); debug_y_offset += 25
        else:
            screen.blit(font_small.render("  None", True, FONT_COLOR), (bp_rect.left + 15, debug_y_offset)); debug_y_offset += 25
            
        if hovered_item_to_draw_stars and not selected_item:
            item, pos = hovered_item_to_draw_stars
            item.draw_stars(screen, pos)

        if dropdown_open:
            for i, name in enumerate(solver_names):
                option_rect = pygame.Rect(dropdown_rect.left, dropdown_rect.bottom + i * 30, dropdown_rect.width, 30)
                pygame.draw.rect(screen, (240, 240, 240), option_rect); pygame.draw.rect(screen, (180, 180, 180), option_rect, 1)
                option_text = font_button.render(name, True, FONT_COLOR)
                screen.blit(option_text, (option_rect.x + 10, option_text.get_height() // 2 + option_rect.y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()

