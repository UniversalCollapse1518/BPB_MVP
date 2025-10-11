# In solvers/random_solver.py

import random
from typing import Tuple, Dict

from solvers.base_solver import BaseSolver

class RandomSolver(BaseSolver):
    """
    Algorithm A: A simple solver that tries a fixed number of random placements.
    """
    def __init__(self, items, backpack_cols, backpack_rows, iterations=1000):
        super().__init__(items, backpack_cols, backpack_rows)
        self.iterations = iterations

    def solve(self) -> Tuple[Dict, float]:
        best_layout = {}
        best_score = 0.0

        for i in range(self.iterations):
            if i % 100 == 0:
                print(f"Solver Iteration: {i}/{self.iterations}")

            current_layout = {}
            
            items_for_this_iteration = [item.clone() for item in self.items_to_place]
            random.shuffle(items_for_this_iteration)

            for item in items_for_this_iteration:
                placed = False
                for _ in range(20): 
                    for _ in range(random.randint(0, 3)):
                        item.rotate()

                    # --- MODIFIED: Use the new helper method from BaseSolver ---
                    position = self._get_random_valid_position(item)
                    if position is None:
                        continue # This rotation doesn't fit, try another

                    gx, gy = position
                    
                    if self._is_placement_valid(item, gx, gy, current_layout):
                        item.gx, item.gy = gx, gy
                        # Use a unique key for the dictionary
                        body_bounds = item.get_body_bounds()
                        key = (gx + body_bounds[1], gy + body_bounds[0]) if body_bounds else (gx, gy)
                        current_layout[key] = item 
                        placed = True
                        break
            
            current_score = self._calculate_score(current_layout)

            if current_score > best_score:
                best_score = current_score
                best_layout = {key: item.clone() for key, item in current_layout.items()}
        
        print(f"Solver finished. Best score found: {best_score}")
        return best_layout, best_score