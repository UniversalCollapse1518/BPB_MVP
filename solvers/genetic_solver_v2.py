import random
import math
from typing import Tuple, Dict, List, Optional
from collections import Counter

from solvers.base_solver import BaseSolver
from engine import Item, GridType

class GeneticSolverV2(BaseSolver):
    """
    Algorithm E: A high-speed Genetic Algorithm.
    Uses a fast "Parent Swap" crossover and a "Randomized Spiral Scan"
    for centrally-biased, non-deterministic placement.
    """
    def __init__(self, items: List[Item], backpack_cols: int, backpack_rows: int,
                 population_size: int = 80, generations: int = 150, mutation_rate: float = 0.15,
                 tournament_size: int = 7, elitism_count: int = 5, initial_layout: Optional[Dict] = None):
        super().__init__(items, backpack_cols, backpack_rows)
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.elitism_count = elitism_count
        self.item_manifest = Counter(item.name for item in self.items_to_place)
        self.initial_layout = initial_layout
        # Pre-calculate the spiral search path once for efficiency
        self.search_path = self._get_center_out_path()

    def _get_center_out_path(self) -> List[Tuple[int, int]]:
        """Creates a list of all grid coordinates, sorted by distance from the center."""
        center_x = (self.backpack_cols - 1) / 2.0
        center_y = (self.backpack_rows - 1) / 2.0
        
        all_coords = [(x, y) for x in range(self.backpack_cols) for y in range(self.backpack_rows)]
        
        # Sort coordinates by their Euclidean distance to the center
        all_coords.sort(key=lambda coord: math.dist((coord[0], coord[1]), (center_x, center_y)))
        
        return all_coords

    def _create_random_individual(self) -> Dict:
        layout = {}
        items_to_place = [item.clone() for item in self.items_to_place]
        random.shuffle(items_to_place)
        for item in items_to_place:
            for _ in range(20):
                for _ in range(random.randint(0, 3)): item.rotate()
                pos = self._get_random_valid_position(item)
                if pos and self._is_placement_valid(item, pos[0], pos[1], layout):
                    item.gx, item.gy = pos
                    offset_c, offset_r = item.get_body_offset()
                    key = (item.gx + offset_c, item.gy + offset_r)
                    layout[key] = item
                    break
        return layout

    def _tournament_selection(self, population: List[Tuple[Dict, float, List]]) -> Dict:
        tournament = random.sample(population, self.tournament_size)
        best = max(tournament, key=lambda ind: ind[1])
        return best[0]

    def _crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        if not parent1: return {k: v.clone() for k, v in parent2.items()}
        if not parent2: return {k: v.clone() for k, v in parent1.items()}

        child_layout = {key: item.clone() for key, item in parent1.items()}
        
        parent2_items = list(parent2.values())
        random.shuffle(parent2_items)
        subset_size = max(1, len(self.items_to_place) // 4)
        invaders = parent2_items[:subset_size]
        
        invader_counts = Counter(item.name for item in invaders)
        
        keys_to_remove = []
        for key, item in child_layout.items():
            if invader_counts.get(item.name, 0) > 0:
                keys_to_remove.append(key)
                invader_counts[item.name] -= 1
        
        for key in keys_to_remove:
            del child_layout[key]

        for item in invaders:
            placed = False
            item_copy = item.clone()
            for _ in range(4): # Try all rotations
                item_copy.rotate()
                occupied_cells = [(c, r) for r, row in enumerate(item_copy.shape_matrix) for c, cell in enumerate(row) if cell == GridType.OCCUPIED]
                if not occupied_cells: continue
                
                # Use the pre-calculated center-out search path
                for spot_x, spot_y in self.search_path:
                    # Try to align each part of the item's body with the target spot
                    for handle_c, handle_r in occupied_cells:
                        gx, gy = spot_x - handle_c, spot_y - handle_r
                        if self._is_placement_valid(item_copy, gx, gy, child_layout):
                            item_copy.gx, item_copy.gy = gx, gy
                            offset_c, offset_r = item_copy.get_body_offset()
                            key = (gx + offset_c, gy + offset_r)
                            child_layout[key] = item_copy
                            placed = True
                            break
                    if placed: break
                if placed: break
        
        return child_layout

    def _mutate(self, layout: Dict) -> Dict:
        if not layout or random.random() > self.mutation_rate: return layout
        mutated_layout = {key: item.clone() for key, item in layout.items()}
        item_keys = list(mutated_layout.keys())
        if not item_keys: return layout
        item_to_mutate_key = random.choice(item_keys)
        item_to_mutate = mutated_layout.pop(item_to_mutate_key)
        
        for _ in range(10):
            action = random.choice(['move', 'rotate', 'swap'])
            
            if action == 'rotate':
                item_to_mutate.rotate()
                if self._is_placement_valid(item_to_mutate, item_to_mutate.gx, item_to_mutate.gy, mutated_layout):
                    offset_c, offset_r = item_to_mutate.get_body_offset()
                    key = (item_to_mutate.gx + offset_c, item_to_mutate.gy + offset_r)
                    mutated_layout[key] = item_to_mutate
                    return mutated_layout

            elif action == 'move':
                pos = self._get_random_valid_position(item_to_mutate)
                if pos and self._is_placement_valid(item_to_mutate, pos[0], pos[1], mutated_layout):
                    item_to_mutate.gx, item_to_mutate.gy = pos
                    offset_c, offset_r = item_to_mutate.get_body_offset()
                    key = (item_to_mutate.gx + offset_c, item_to_mutate.gy + offset_r)
                    mutated_layout[key] = item_to_mutate
                    return mutated_layout

            elif action == 'swap' and len(mutated_layout) > 0:
                other_item_key = random.choice(list(mutated_layout.keys()))
                other_item = mutated_layout[other_item_key]
                
                original_pos_mut = (item_to_mutate.gx, item_to_mutate.gy)
                original_pos_other = (other_item.gx, other_item.gy)

                item_to_mutate.gx, item_to_mutate.gy = original_pos_other
                other_item.gx, other_item.gy = original_pos_mut
                
                rest_of_layout = {k: v for k, v in mutated_layout.items() if k != other_item_key}

                if self._is_placement_valid(item_to_mutate, item_to_mutate.gx, item_to_mutate.gy, rest_of_layout) and \
                   self._is_placement_valid(other_item, other_item.gx, other_item.gy, rest_of_layout):
                    
                    rest_of_layout['temp_key_for_mutated'] = item_to_mutate
                    if self._is_placement_valid(other_item, other_item.gx, other_item.gy, rest_of_layout):
                        mutated_layout.pop(other_item_key)
                        offset_c1, offset_r1 = item_to_mutate.get_body_offset()
                        offset_c2, offset_r2 = other_item.get_body_offset()
                        key1 = (item_to_mutate.gx + offset_c1, item_to_mutate.gy + offset_r1)
                        key2 = (other_item.gx + offset_c2, other_item.gy + offset_r2)
                        mutated_layout[key1] = item_to_mutate
                        mutated_layout[key2] = other_item
                        return mutated_layout

                item_to_mutate.gx, item_to_mutate.gy = original_pos_mut
                other_item.gx, other_item.gy = original_pos_other

        mutated_layout[item_to_mutate_key] = item_to_mutate
        return mutated_layout

    def solve(self) -> Tuple[Dict, float]:
        population = [self._create_random_individual() for _ in range(self.population_size - 1)]
        if self.initial_layout:
            cloned_initial = {key: item.clone() for key, item in self.initial_layout.items()}
            population.append(cloned_initial)
        else:
            population.append(self._create_random_individual())

        best_layout_overall = {}
        best_score_overall = -1.0

        for gen in range(self.generations):
            scored_population = []
            for ind in population:
                score, i_map = self._calculate_score(ind)
                scored_population.append((ind, score, i_map))

            scored_population.sort(key=lambda x: x[1], reverse=True)
            
            current_best_layout, current_best_score, _ = scored_population[0]
            if current_best_score > best_score_overall:
                best_score_overall = current_best_score
                best_layout_overall = {key: item.clone() for key, item in current_best_layout.items()}
            
            print(f"Generation {gen+1}/{self.generations} - Best Score: {best_score_overall:.2f}")

            next_population = []
            for i in range(self.elitism_count):
                next_population.append(scored_population[i][0])
            
            while len(next_population) < self.population_size:
                parent1 = self._tournament_selection(scored_population)
                parent2 = self._tournament_selection(scored_population)
                
                child = self._crossover(parent1, parent2)
                child = self._mutate(child)
                next_population.append(child)
            
            population = next_population

        return best_layout_overall, best_score_overall