from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional
import copy
import random

from engine import Item, CalculationEngine
from definitions import GridType

class BaseSolver(ABC):
    # ... (__init__ and other methods are unchanged) ...
    def __init__(self, items: List[Item], backpack_cols: int, backpack_rows: int):
        self.items_to_place = [item.clone() for item in items]
        self.backpack_cols = backpack_cols
        self.backpack_rows = backpack_rows
        self.engine = CalculationEngine()

    @abstractmethod
    def solve(self) -> Tuple[Dict, float]:
        """
        The main method to run the solving algorithm.
        This must be implemented by all child classes.
        Returns:
            A tuple containing:
            - The best layout found (a dictionary of placed items).
            - The best score achieved.
        """
        pass

    def _get_random_valid_position(self, item: Item) -> Optional[Tuple[int, int]]:
        # ... (unchanged) ...
        body_bounds = item.get_body_bounds()
        if not body_bounds:
            return None # Cannot place an item with no body

        min_r, min_c, max_r, max_c = body_bounds
        body_width = max_c - min_c + 1
        body_height = max_r - min_r + 1
        
        if body_width > self.backpack_cols or body_height > self.backpack_rows:
            return None 

        gx_min = -min_c
        gx_max = self.backpack_cols - (max_c + 1)
        gy_min = -min_r
        gy_max = self.backpack_rows - (max_r + 1)
        
        if gx_min > gx_max or gy_min > gy_max:
             return None

        gx = random.randint(gx_min, gx_max)
        gy = random.randint(gy_min, gy_max)

        return (gx, gy)

    def _is_placement_valid(self, item_to_place: Item, gx: int, gy: int, placed_items: Dict) -> bool:
        # ... (unchanged) ...
        occupied_cells = set()
        for p_item in placed_items.values():
            px, py = p_item.gx, p_item.gy
            for r, row in enumerate(p_item.shape_matrix):
                for c, cell in enumerate(row):
                    if cell == GridType.OCCUPIED:
                        occupied_cells.add((px + c, py + r))
        
        for r, row in enumerate(item_to_place.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED:
                    ax, ay = gx + c, gy + r
                    if not(0 <= ax < self.backpack_cols and 0 <= ay < self.backpack_rows):
                        return False
                    if (ax, ay) in occupied_cells:
                        return False
        return True

    def _calculate_score(self, layout: Dict) -> Tuple[float, List[Tuple[str, str]]]:
        """
        A helper utility to calculate the score and get the interaction map.
        Returns a tuple of (total_score, interaction_map).
        """
        if not layout:
            return 0.0, []
        calc_layout = {key: item.clone() for key, item in layout.items()}
        self.engine.run(calc_layout, self.backpack_cols, self.backpack_rows)
        item_scores = sum(item.final_score for item in calc_layout.values())
        total_score = item_scores + self.engine.neutral_pool_total
        return total_score, self.engine.interaction_map