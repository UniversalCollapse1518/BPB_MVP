import gymnasium as gym
import numpy as np
from gymnasium import spaces
from typing import List, Dict, Tuple, Optional

from engine import Item, CalculationEngine, GridType

class BackpackEnv(gym.Env):
    """
    An advanced Gymnasium environment with Action Masking and a sophisticated
    reward function that includes a "Possibility Reduction Penalty" to teach
    the agent to preserve future options.
    """

    def __init__(self, items: List[Item], backpack_cols: int, backpack_rows: int):
        super(BackpackEnv, self).__init__()

        self.backpack_cols = backpack_cols
        self.backpack_rows = backpack_rows
        self.all_items = items
        self.engine = CalculationEngine()
        self.penalty_factor = 20.0  # Tunable parameter for the reduction penalty

        self.num_actions = self.backpack_cols * self.backpack_rows * 4
        self.action_space = spaces.Discrete(self.num_actions)

        self.observation_space = spaces.Box(
            low=0, high=1, shape=(3, self.backpack_rows, self.backpack_cols),
            dtype=np.float32
        )

        self.items_to_place: List[Item] = []
        self.current_item_index = 0
        self.placed_items: Dict[Tuple[int, int], Item] = {}

    def _action_to_coords(self, action: int) -> Tuple[int, int, int]:
        rot_size = self.backpack_rows * self.backpack_cols
        rot = action // rot_size
        y = (action % rot_size) // self.backpack_cols
        x = action % self.backpack_cols
        return x, y, rot

    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None) -> Tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        self.items_to_place = [item.clone() for item in self.all_items]
        np.random.shuffle(self.items_to_place)
        self.current_item_index = 0
        self.placed_items = {}
        observation = self._get_obs()
        info = {"action_mask": self.action_masks()}
        return observation, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        score_before, _ = self._calculate_score(self.placed_items)
        
        # --- Possibility Reduction: Calculate options for the *next* item ---
        valid_moves_before = 0
        if self.current_item_index + 1 < len(self.items_to_place):
            next_item = self.items_to_place[self.current_item_index + 1]
            valid_moves_before = self._count_valid_placements(next_item)

        # Place the current item
        x, y, rotation_idx = self._action_to_coords(action)
        current_item = self.items_to_place[self.current_item_index].clone()
        for _ in range(rotation_idx):
            current_item.rotate()
        current_item.gx, current_item.gy = x, y
        offset_c, offset_r = current_item.get_body_offset()
        key = (x + offset_c, y + offset_r)
        self.placed_items[key] = current_item
        self.current_item_index += 1

        # Calculate Synergy Delta reward
        score_after, _ = self._calculate_score(self.placed_items)
        synergy_delta = (score_after - score_before) - current_item.base_score
        reward = synergy_delta

        # --- Possibility Reduction: Calculate penalty ---
        valid_moves_after = 0
        if self.current_item_index < len(self.items_to_place):
            next_item = self.items_to_place[self.current_item_index]
            valid_moves_after = self._count_valid_placements(next_item)

            if valid_moves_before > 0:
                if valid_moves_after == 0:
                    # Catastrophic move, terminate with a large penalty
                    reward = -100.0
                    terminated = True
                else:
                    # Calculate non-linear penalty for reducing options
                    reduction_ratio = 1.0 - (valid_moves_after / valid_moves_before)
                    penalty = self.penalty_factor * (reduction_ratio ** 2)
                    reward -= penalty
        
        terminated = self.current_item_index >= len(self.items_to_place)
        observation = self._get_obs()
        info = {"action_mask": self.action_masks()} if not terminated else {}
        
        return observation, reward, terminated, False, info

    def action_masks(self) -> np.ndarray:
        return self._get_action_mask()

    def _get_action_mask(self) -> np.ndarray:
        if self.current_item_index >= len(self.items_to_place):
            return np.zeros(self.num_actions, dtype=bool)

        mask = np.zeros(self.num_actions, dtype=bool)
        current_item = self.items_to_place[self.current_item_index]
        return self._calculate_mask_for_item(current_item)

    def _count_valid_placements(self, item: Item) -> int:
        """Counts the total number of valid placements for a given item."""
        mask = self._calculate_mask_for_item(item)
        return np.sum(mask)

    def _calculate_mask_for_item(self, item: Item) -> np.ndarray:
        """Helper function to generate an action mask for a specific item."""
        mask = np.zeros(self.num_actions, dtype=bool)
        for rot in range(4):
            item_rotated = item.clone()
            for _ in range(rot):
                item_rotated.rotate()
            
            for y in range(self.backpack_rows):
                for x in range(self.backpack_cols):
                    if self._is_placement_valid(item_rotated, x, y):
                        action_index = (rot * self.backpack_rows * self.backpack_cols) + (y * self.backpack_cols) + x
                        mask[action_index] = True
        return mask

    def _get_obs(self) -> np.ndarray:
        occupancy_grid = np.zeros((self.backpack_rows, self.backpack_cols), dtype=np.float32)
        hotspot_grid = np.zeros((self.backpack_rows, self.backpack_cols), dtype=np.float32)
        for item in self.placed_items.values():
            for r, row in enumerate(item.shape_matrix):
                for c, cell in enumerate(row):
                    ax, ay = item.gx + c, item.gy + r
                    if 0 <= ay < self.backpack_rows and 0 <= ax < self.backpack_cols:
                        if cell == GridType.OCCUPIED:
                            occupancy_grid[ay][ax] = 1.0
                        elif cell.name.startswith("STAR"):
                            hotspot_grid[ay][ax] = 1.0
        hotspot_grid[occupancy_grid == 1.0] = 0.0
        item_grid = np.zeros((self.backpack_rows, self.backpack_cols), dtype=np.float32)
        if self.current_item_index < len(self.items_to_place):
            item_to_place = self.items_to_place[self.current_item_index]
            start_row = (self.backpack_rows - item_to_place.grid_height) // 2
            start_col = (self.backpack_cols - item_to_place.grid_width) // 2
            for r, row in enumerate(item_to_place.shape_matrix):
                for c, cell in enumerate(row):
                    if cell == GridType.OCCUPIED:
                        if 0 <= start_row + r < self.backpack_rows and 0 <= start_col + c < self.backpack_cols:
                            item_grid[start_row + r][start_col + c] = 1.0
        return np.stack([occupancy_grid, item_grid, hotspot_grid])

    def _is_placement_valid(self, item_to_place: Item, gx: int, gy: int) -> bool:
        for r, row in enumerate(item_to_place.shape_matrix):
            for c, cell in enumerate(row):
                if cell == GridType.OCCUPIED:
                    ax, ay = gx + c, gy + r
                    if not (0 <= ax < self.backpack_cols and 0 <= ay < self.backpack_rows):
                        return False
                    for p_item in self.placed_items.values():
                        for pr, p_row in enumerate(p_item.shape_matrix):
                            for pc, p_cell in enumerate(p_row):
                                if p_cell == GridType.OCCUPIED and (p_item.gx + pc, p_item.gy + pr) == (ax, ay):
                                    return False
        return True

    def _calculate_score(self, layout: Dict) -> Tuple[float, List]:
        if not layout: return 0.0, []
        calc_layout = {key: item.clone() for key, item in layout.items()}
        self.engine.run(calc_layout, self.backpack_cols, self.backpack_rows)
        item_scores = sum(item.final_score for item in calc_layout.values())
        total_score = item_scores + self.engine.neutral_pool_total
        return total_score, self.engine.interaction_map

    def render(self, mode='human'):
        grid = [["." for _ in range(self.backpack_cols)] for _ in range(self.backpack_rows)]
        for i, item in enumerate(self.placed_items.values()):
            char = str(i)
            for r, row in enumerate(item.shape_matrix):
                for c, cell in enumerate(row):
                    if cell == GridType.OCCUPIED:
                        if 0 <= item.gy + r < self.backpack_rows and 0 <= item.gx + c < self.backpack_cols:
                            grid[item.gy + r][item.gx + c] = char
        print("-" * self.backpack_cols * 2)
        for row in grid:
            print(" ".join(row))
        if self.current_item_index < len(self.items_to_place):
            print(f"Next item: {self.items_to_place[self.current_item_index].name}")
        else:
            print("All items placed.")
        print("-" * self.backpack_cols * 2)

    def close(self):
        pass