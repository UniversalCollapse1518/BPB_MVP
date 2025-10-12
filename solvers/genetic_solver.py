import random
from typing import Tuple, Dict, List, Optional
from collections import Counter

from solvers.base_solver import BaseSolver
from engine import Item

class GeneticSolver(BaseSolver):
    """
    Algorithm D: A Genetic Algorithm to find an optimal backpack layout.
    """
    def __init__(self, items: List[Item], backpack_cols: int, backpack_rows: int,
                 population_size: int = 80, generations: int = 150, mutation_rate: float = 0.12,
                 tournament_size: int = 7, elitism_count: int = 5, initial_layout: Optional[Dict] = None):
        super().__init__(items, backpack_cols, backpack_rows)
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.elitism_count = elitism_count
        self.item_manifest = Counter(item.name for item in self.items_to_place)
        self.initial_layout = initial_layout

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
                    key = (item.gx + item.get_body_offset()[1], item.gy + item.get_body_offset()[0])
                    layout[key] = item
                    break
        return layout

    def _tournament_selection(self, population: List[Tuple[Dict, float]]) -> Dict:
        tournament = random.sample(population, self.tournament_size)
        return max(tournament, key=lambda ind: ind[1])[0]

    def _crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        child_layout = {}
        parent1_items = [item.clone() for item in parent1.values()]
        random.shuffle(parent1_items)
        for item in parent1_items:
            if self._is_placement_valid(item, item.gx, item.gy, child_layout):
                key = (item.gx + item.get_body_offset()[1], item.gy + item.get_body_offset()[0])
                child_layout[key] = item
        child_manifest = Counter(item.name for item in child_layout.values())
        missing_manifest = self.item_manifest - child_manifest
        missing_items: List[Item] = []
        parent2_items = [item.clone() for item in parent2.values()]
        random.shuffle(parent2_items)
        for item in parent2_items:
            if missing_manifest[item.name] > 0:
                if self._is_placement_valid(item, item.gx, item.gy, child_layout):
                    key = (item.gx + item.get_body_offset()[1], item.gy + item.get_body_offset()[0])
                    child_layout[key] = item
                    missing_manifest[item.name] -= 1
                else: missing_items.append(item)
        for item in missing_items:
            if missing_manifest[item.name] > 0:
                for _ in range(20):
                    pos = self._get_random_valid_position(item)
                    if pos and self._is_placement_valid(item, pos[0], pos[1], child_layout):
                        item.gx, item.gy = pos
                        key = (item.gx + item.get_body_offset()[1], item.gy + item.get_body_offset()[0])
                        child_layout[key] = item
                        missing_manifest[item.name] -= 1
                        break
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
                    key = (item_to_mutate.gx + item_to_mutate.get_body_offset()[1], item_to_mutate.gy + item_to_mutate.get_body_offset()[0])
                    mutated_layout[key] = item_to_mutate
                    return mutated_layout

            elif action == 'move':
                pos = self._get_random_valid_position(item_to_mutate)
                if pos and self._is_placement_valid(item_to_mutate, pos[0], pos[1], mutated_layout):
                    item_to_mutate.gx, item_to_mutate.gy = pos
                    key = (item_to_mutate.gx + item_to_mutate.get_body_offset()[1], item_to_mutate.gy + item_to_mutate.get_body_offset()[0])
                    mutated_layout[key] = item_to_mutate
                    return mutated_layout

            # --- MODIFIED: Corrected validation logic for swap ---
            elif action == 'swap' and len(mutated_layout) > 0:
                other_item_key = random.choice(list(mutated_layout.keys()))
                other_item = mutated_layout[other_item_key]
                
                # Store original positions
                original_pos_mut = (item_to_mutate.gx, item_to_mutate.gy)
                original_pos_other = (other_item.gx, other_item.gy)

                # Perform the swap
                item_to_mutate.gx, item_to_mutate.gy = original_pos_other
                other_item.gx, other_item.gy = original_pos_mut
                
                # Create a layout of all *other* items for validation
                rest_of_layout = {k: v for k, v in mutated_layout.items() if k != other_item_key}

                # Check if both items are valid in their new spots against the rest of the layout
                if self._is_placement_valid(item_to_mutate, item_to_mutate.gx, item_to_mutate.gy, rest_of_layout) and \
                   self._is_placement_valid(other_item, other_item.gx, other_item.gy, rest_of_layout):
                    
                    # Final crucial check: do the swapped items overlap EACH OTHER?
                    # Temporarily add one item back to check the other against it.
                    rest_of_layout['temp_key_for_mutated'] = item_to_mutate
                    if self._is_placement_valid(other_item, other_item.gx, other_item.gy, rest_of_layout):
                        # Swap is fully valid, update the final layout and return
                        mutated_layout.pop(other_item_key)
                        key1 = (item_to_mutate.gx + item_to_mutate.get_body_offset()[1], item_to_mutate.gy + item_to_mutate.get_body_offset()[0])
                        key2 = (other_item.gx + other_item.get_body_offset()[1], other_item.gy + other_item.get_body_offset()[0])
                        mutated_layout[key1] = item_to_mutate
                        mutated_layout[key2] = other_item
                        return mutated_layout

                # If any check failed, revert the swap
                item_to_mutate.gx, item_to_mutate.gy = original_pos_mut
                other_item.gx, other_item.gy = original_pos_other


        # If mutation failed after all attempts, return the original layout
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
            scored_population = [(ind, self._calculate_score(ind)) for ind in population]
            scored_population.sort(key=lambda x: x[1], reverse=True)
            
            if scored_population[0][1] > best_score_overall:
                best_score_overall = scored_population[0][1]
                best_layout_overall = {key: item.clone() for key, item in scored_population[0][0].items()}
            
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

