import os
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker

from solvers.base_solver import BaseSolver
from BackpackEnv import BackpackEnv 

class RLSolver(BaseSolver):
    """
    A solver that uses a pre-trained, action-masked Reinforcement Learning 
    model to guarantee a valid and complete item placement.
    """
    def __init__(self, items, backpack_cols, backpack_rows, initial_layout=None):
        super().__init__(items, backpack_cols, backpack_rows)
        
        self.model_path = "ppo_maskable_backpack_solver.zip"
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Trained model not found at '{self.model_path}'. "
                "Please run train.py with the action masking environment."
            )
        
        self.model = MaskablePPO.load(self.model_path)
        print("Maskable RL model loaded successfully.")

    def solve(self):
        print("Running Maskable RL Solver...")
        
        # 1. Create and wrap the environment
        env = BackpackEnv(
            items=self.items_to_place, 
            backpack_cols=self.backpack_cols, 
            backpack_rows=self.backpack_rows
        )
        env = ActionMasker(env, lambda env: env.action_masks())
        
        obs, info = env.reset()
        terminated = False
        
        # 2. Loop until all items are placed
        while not terminated:
            action_masks = env.action_masks()
            action, _states = self.model.predict(obs, action_masks=action_masks, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            
        # --- FIX: Access the 'placed_items' from the unwrapped environment ---
        unwrapped_env = env.unwrapped
        # --- END FIX ---

        # 3. Extract and visualize the final layout
        final_layout = {}
        for key, data_item in unwrapped_env.placed_items.items():
            visual_item = data_item.clone(visuals=True)
            final_layout[key] = visual_item
        
        final_score, _ = self._calculate_score(final_layout)
        
        return final_layout, final_score