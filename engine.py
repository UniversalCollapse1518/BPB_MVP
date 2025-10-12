import pygame
from typing import List, Optional, Dict, Tuple, Any
import math
import copy
from definitions import GridType, Rarity, ItemClass, Element, ItemType

class Item(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, name: str, rarity: Rarity,
                 item_class: ItemClass, elements: List[Element], types: List[ItemType],
                 shape_matrix: List[List[GridType]], base_score: int, star_effects: dict,
                 has_cooldown: bool = False, is_start_of_battle: bool = False, passive_effects: List[dict] = None):
        super().__init__()
        self.name = name
        self.rarity = rarity
        self.item_class = item_class
        self.elements = elements
        self.types = types
        self.shape_matrix = shape_matrix
        self.base_score = base_score
        self.star_effects = star_effects
        self.has_cooldown = has_cooldown
        self.is_start_of_battle = is_start_of_battle
        self.passive_effects = passive_effects if passive_effects is not None else []

        self.grid_width = len(shape_matrix[0]) if shape_matrix else 0
        self.grid_height = len(shape_matrix)
        
        from main import GRID_SIZE, RARITY_BORDER_COLORS, FONT_COLOR
        self.body_image = self.create_body_surface(GRID_SIZE, RARITY_BORDER_COLORS, FONT_COLOR)
        self.rect = self.body_image.get_rect(topleft=(x, y))

        self.base_y = y
        self.dragging = False

        self.gx = -1
        self.gy = -1
        
        self.final_score = 0
        self.score_modifiers = []
        self.activated_stars = {GridType.STAR_A: 0, GridType.STAR_B: 0, GridType.STAR_C: 0}
        self.occupying_stars = []
        self.temporary_elements = []
        
        self._body_bounds = None

    def clone(self):
        new_item = Item(
            x=self.rect.x if self.rect else 0, y=self.rect.y if self.rect else 0, 
            name=self.name, rarity=self.rarity, item_class=self.item_class,
            elements=list(self.elements), types=list(self.types), shape_matrix=copy.deepcopy(self.shape_matrix),
            base_score=self.base_score, star_effects=copy.deepcopy(self.star_effects), has_cooldown=self.has_cooldown,
            is_start_of_battle=self.is_start_of_battle, passive_effects=copy.deepcopy(self.passive_effects)
        )
        new_item.gx, new_item.gy = self.gx, self.gy
        return new_item

    def get_body_bounds(self) -> Optional[Tuple[int, int, int, int]]:
        if self._body_bounds: return self._body_bounds
        min_r, max_r, min_c, max_c = self.grid_height, -1, self.grid_width, -1
        found_body = False
        for r, row in enumerate(self.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED:
                    found_body = True
                    min_r, max_r, min_c, max_c = min(min_r, r), max(max_r, r), min(min_c, c), max(max_c, c)
        if found_body: self._body_bounds = (min_r, min_c, max_r, max_c); return self._body_bounds
        return None

    def get_body_offset(self) -> Tuple[int, int]:
        bounds = self.get_body_bounds()
        return (bounds[1], bounds[0]) if bounds else (0, 0)
    
    def create_body_surface(self, grid_size, rarity_colors, font_color):
        width_px, height_px = self.grid_width * grid_size, self.grid_height * grid_size
        surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
        occupied_coords = [(c, r) for r, row in enumerate(self.shape_matrix) for c, cell in enumerate(row) if cell == GridType.OCCUPIED]
        if occupied_coords:
            for c, r in occupied_coords:
                pygame.draw.rect(surface, (200, 200, 200), (c * grid_size, r * grid_size, grid_size, grid_size))
                pygame.draw.rect(surface, rarity_colors[self.rarity], (c * grid_size, r * grid_size, grid_size, grid_size), 2)
            min_c, max_c = min(c for c,r in occupied_coords), max(c for c,r in occupied_coords)
            min_r, max_r = min(r for c,r in occupied_coords), max(r for c,r in occupied_coords)
            center_x, center_y = (min_c + max_c + 1) * grid_size / 2, (min_r + max_r + 1) * grid_size / 2
            font = pygame.font.SysFont(None, 20)
            name_text = (self.name[:4] + '..') if len(self.name) > 6 else self.name
            text_surf = font.render(name_text, True, font_color)
            surface.blit(text_surf, text_surf.get_rect(center=(center_x, center_y)))
        return surface

    def draw_stars(self, screen: pygame.Surface, top_left_pos: Tuple[int, int]):
        from main import GRID_SIZE, STAR_SHAPE_COLORS
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
        from main import GRID_SIZE
        for r, row in enumerate(self.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED and self.rect and pygame.Rect(current_pos[0]+c*GRID_SIZE, current_pos[1]+r*GRID_SIZE, GRID_SIZE, GRID_SIZE).collidepoint(mouse_pos):
                    return True
        return False
        
    def rotate(self):
        self.shape_matrix = [list(row)[::-1] for row in zip(*self.shape_matrix)]
        self.grid_height, self.grid_width = len(self.shape_matrix), len(self.shape_matrix[0])
        from main import GRID_SIZE, RARITY_BORDER_COLORS, FONT_COLOR
        self.body_image = self.create_body_surface(GRID_SIZE, RARITY_BORDER_COLORS, FONT_COLOR)
        # Recreate the rect to get the new dimensions
        self.rect = self.body_image.get_rect()
        self._body_bounds = None


class CalculationEngine:
    def __init__(self):
        # --- NEW: Attributes for the neutral score pool ---
        self.neutral_pool_modifiers = []
        self.neutral_pool_total = 0.0

    def _check_condition(self, condition_data: dict, source_item: Item, target_item: Optional[Item], condition_logic: str = "AND") -> bool:
        # ... (function is unchanged) ...
        if not condition_data: return True
        check_results = []
        if "requires_empty" in condition_data:
            if condition_data["requires_empty"]: check_results.append(target_item is None)
        if target_item is not None:
            if "requires_element" in condition_data:
                reqs = condition_data["requires_element"]
                if not isinstance(reqs, list): reqs = [reqs]
                target_elems = set(target_item.elements + target_item.temporary_elements)
                check_results.append(any(Element[req.upper()] in target_elems for req in reqs))
            if "requires_type" in condition_data:
                reqs = condition_data["requires_type"]
                if not isinstance(reqs, list): reqs = [reqs]
                check_results.append(any(ItemType[req.upper()] in target_item.types for req in reqs))
            if "requires_name" in condition_data:
                reqs = condition_data["requires_name"]
                if not isinstance(reqs, list): reqs = [reqs]
                check_results.append(target_item.name in reqs)
            if "must_be_different" in condition_data:
                if condition_data["must_be_different"]: check_results.append(source_item.name != target_item.name)
            if "requires_cooldown" in condition_data:
                if condition_data["requires_cooldown"]: check_results.append(getattr(target_item, 'has_cooldown', False))
            if "requires_start_of_battle" in condition_data:
                if condition_data["requires_start_of_battle"]: check_results.append(getattr(target_item, 'is_start_of_battle', False))
        else:
            for key in condition_data:
                if key != "requires_empty": check_results.append(False)
        if not check_results: return True
        return any(check_results) if condition_logic == "OR" else all(check_results)

    def _get_effect_value(self, effect_data: dict, source_item: Item) -> Any:
        # ... (function is unchanged) ...
        value_data = effect_data.get("value", 0)
        if not isinstance(value_data, dict): return value_data
        final_value = value_data.get("base", 0.0)
        if "dynamic_bonus" in value_data:
            bonus_data = value_data["dynamic_bonus"]
            per_star_type = GridType[bonus_data["per_activated_star"]]
            num_activated = source_item.activated_stars.get(per_star_type, 0)
            final_value += num_activated * bonus_data.get("add", 0)
        return final_value
        
    def run(self, placed_items: Dict[Any, Item], backpack_cols: int, backpack_rows: int):
        # --- NEW: Reset neutral pool on each run ---
        self.neutral_pool_modifiers.clear()
        self.neutral_pool_total = 0.0

        occupancy_grid: List[List[Optional[Item]]] = [[None for _ in range(backpack_cols)] for _ in range(backpack_rows)]
        for item in placed_items.values():
            item.final_score = item.base_score
            item.score_modifiers, item.occupying_stars, item.temporary_elements = [], [], []
            item.activated_stars = {GridType.STAR_A: 0, GridType.STAR_B: 0, GridType.STAR_C: 0}
        
        for item in placed_items.values():
            gx, gy = item.gx, item.gy
            for r, row in enumerate(item.shape_matrix):
                for c, cell in enumerate(row):
                    if cell == GridType.OCCUPIED and 0 <= gy+r < backpack_rows and 0 <= gx+c < backpack_cols:
                        occupancy_grid[gy+r][gx+c] = item
        # ... (element adding and star activation loops are unchanged) ...
        for source_item in placed_items.values():
            gx, gy = source_item.gx, source_item.gy
            for r, row in enumerate(source_item.shape_matrix):
                for c, cell_type in enumerate(row):
                    if cell_type.name.startswith("STAR"):
                        base_star_name = cell_type.name
                        for star_key in source_item.star_effects:
                            if star_key.startswith(base_star_name):
                                effects, logic = (source_item.star_effects.get(star_key, []), "AND")
                                if not isinstance(effects, list): effects = [effects]
                                abs_x, abs_y = gx + c, gy + r
                                target_item = occupancy_grid[abs_y][abs_x] if 0 <= abs_y < backpack_rows and 0 <= abs_x < backpack_cols else None
                                for effect_data in effects:
                                    logic = effect_data.get("condition_logic", "AND")
                                    if effect_data.get("effect") == "ADD_ELEMENT_TO_TARGET" and self._check_condition(effect_data.get("condition", {}), source_item, target_item, logic):
                                        if target_item:
                                            try:
                                                element_to_add = Element[effect_data["value"].upper()]
                                                if element_to_add not in target_item.temporary_elements: target_item.temporary_elements.append(element_to_add)
                                            except (KeyError, AttributeError): print(f"Warning: Invalid element '{effect_data['value']}' for ADD_ELEMENT_TO_TARGET in {source_item.name}")
                                        break
        for source_item in placed_items.values():
            gx, gy = source_item.gx, source_item.gy
            triggered_by = {GridType.STAR_A: set(), GridType.STAR_B: set(), GridType.STAR_C: set()}
            for r, row in enumerate(source_item.shape_matrix):
                for c, cell_type in enumerate(row):
                    if cell_type in triggered_by:
                        abs_x, abs_y = gx + c, gy + r
                        if not(0 <= abs_x < backpack_cols and 0 <= abs_y < backpack_rows): continue
                        base_star_name = cell_type.name
                        for star_key in source_item.star_effects:
                            if star_key.startswith(base_star_name):
                                effects = source_item.star_effects.get(star_key, [])
                                if not isinstance(effects, list): effects = [effects]
                                target_item = occupancy_grid[abs_y][abs_x]
                                for effect_data in effects:
                                    logic = effect_data.get("condition_logic", "AND")
                                    if self._check_condition(effect_data.get("condition", {}), source_item, target_item, logic):
                                        if target_item is None or target_item not in triggered_by.get(cell_type, set()):
                                            source_item.activated_stars[cell_type] += 1
                                            if target_item:
                                                if cell_type not in triggered_by: triggered_by[cell_type] = set()
                                                target_item.occupying_stars.append((cell_type, source_item.name))
                                                triggered_by[cell_type].add(target_item)
                                        break

        all_effects = []
        for source_item in placed_items.values():
            for effect_data in source_item.passive_effects:
                logic = effect_data.get("condition_logic", "AND")
                for target_item in placed_items.values():
                    if self._check_condition(effect_data.get("condition", {}), source_item, target_item, logic):
                        value = self._get_effect_value(effect_data, source_item)
                        reason = f"Passive from {target_item.name}"
                        all_effects.append({"source": source_item, "target": target_item, "effect": effect_data["effect"], "value": value, "reason": reason})

            triggered_targets = {GridType.STAR_A: set(), GridType.STAR_B: set(), GridType.STAR_C: set()}
            gx, gy = source_item.gx, source_item.gy
            for r, row in enumerate(source_item.shape_matrix):
                for c, cell_type in enumerate(row):
                    if cell_type in triggered_targets:
                        abs_x, abs_y = gx + c, gy + r
                        if not(0 <= abs_x < backpack_cols and 0 <= abs_y < backpack_rows): continue
                        target_item = occupancy_grid[abs_y][abs_x]
                        is_duplicate = False
                        if target_item is not None:
                            if target_item in triggered_targets[cell_type]: is_duplicate = True
                        if is_duplicate: continue
                        base_star_name = cell_type.name
                        effect_applied_for_this_cell = False
                        for star_key in source_item.star_effects:
                            if star_key.startswith(base_star_name):
                                effects = source_item.star_effects[star_key]
                                if not isinstance(effects, list): effects = [effects]
                                for effect_data in effects:
                                    logic = effect_data.get("condition_logic", "AND")
                                    if self._check_condition(effect_data.get("condition", {}), source_item, target_item, logic):
                                        if "effect" in effect_data: # All score effects fall in here
                                            value = self._get_effect_value(effect_data, source_item)
                                            reason = f"Star {cell_type.name.split('_')[1]}"
                                            all_effects.append({"source": source_item, "target": target_item, "effect": effect_data["effect"], "value": value, "reason": reason})
                                        if target_item is not None:
                                            triggered_targets[cell_type].add(target_item)
                                        effect_applied_for_this_cell = True
                                        break
                                if effect_applied_for_this_cell: break
        
        # --- NEW: Loop to process neutral pool effects ---
        for eff in all_effects:
            if eff["effect"] == "ADD_TO_NEUTRAL_POOL":
                try:
                    numeric_value = float(eff["value"])
                    reason_text = f"from {eff['source'].name}'s {eff['reason']}"
                    self.neutral_pool_total += numeric_value
                    self.neutral_pool_modifiers.append(f"+{numeric_value:.1f} ({reason_text})")
                except (ValueError, TypeError):
                    continue

        for effect_type in ["ADD_SCORE_TO_SELF", "ADD_SCORE_TO_TARGET"]:
            for eff in all_effects:
                if eff["effect"] == effect_type:
                    try:
                        numeric_value = float(eff["value"])
                        if eff["effect"] == "ADD_SCORE_TO_SELF":
                            reason_text = eff.get("reason", "self")
                            eff["source"].final_score += numeric_value
                            eff["source"].score_modifiers.append(f"+{numeric_value:.1f} ({reason_text})")
                        elif eff["target"]:
                            eff["target"].final_score += numeric_value
                            eff["target"].score_modifiers.append(f"+{numeric_value:.1f} from {eff['source'].name}")
                    except (ValueError, TypeError): continue
        
        for effect_type in ["MULTIPLY_SCORE_OF_SELF", "MULTIPLY_SCORE_OF_TARGET"]:
            for eff in all_effects:
                if eff["effect"] == effect_type:
                    try:
                        numeric_value = float(eff["value"])
                        if eff["effect"] == "MULTIPLY_SCORE_OF_SELF":
                            reason_text = eff.get("reason", "self")
                            eff["source"].final_score *= numeric_value
                            eff["source"].score_modifiers.append(f"x{numeric_value:.2f} ({reason_text})")
                        elif eff["target"]:
                            eff["target"].final_score *= numeric_value
                            eff["target"].score_modifiers.append(f"x{numeric_value:.2f} from {eff['source'].name}")
                    except (ValueError, TypeError): continue
