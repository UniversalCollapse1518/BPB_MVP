import json
import torch
import torch.nn as nn
from gymnasium import spaces
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
# --- FIX: Import the correct, maskable CnnPolicy ---
from sb3_contrib.ppo_mask.policies import CnnPolicy

from BackpackEnv import BackpackEnv
from engine import Item
from definitions import Rarity, ItemClass, Element, ItemType, GridType

class CustomCNN(BaseFeaturesExtractor):
    def __init__(self, observation_space: spaces.Box, features_dim: int = 64):
        super().__init__(observation_space, features_dim)
        n_input_channels = observation_space.shape[0]
        self.cnn = nn.Sequential(
            nn.Conv2d(n_input_channels, 16, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Flatten(),
        )
        with torch.no_grad():
            n_flatten = self.cnn(
                torch.as_tensor(observation_space.sample()[None]).float()
            ).shape[1]
        self.linear = nn.Sequential(nn.Linear(n_flatten, features_dim), nn.ReLU())

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        return self.linear(self.cnn(observations))

BACKPACK_COLS = 9
BACKPACK_ROWS = 7
TRAINING_TIMESTEPS = 1_000_000
MODEL_SAVE_PATH = "ppo_maskable_backpack_solver"

def load_all_items_from_json(filepath: str) -> list[Item]:
    items = []
    with open(filepath, 'r') as f:
        data = json.load(f)
    for item_data in data.values():
        item = Item(
            x=0, y=0, name=item_data['name'], rarity=Rarity[item_data['rarity']],
            item_class=ItemClass[item_data['item_class']],
            elements=[Element[e] for e in item_data.get('elements', [])],
            types=[ItemType[t] for t in item_data.get('types', [])],
            shape_matrix=[[GridType(c) for c in r] for r in item_data['shape_matrix']],
            base_score=item_data.get('base_score', 0), star_effects=item_data.get('star_effects', {}),
            has_cooldown=item_data.get('has_cooldown', False), is_start_of_battle=item_data.get('is_start_of_battle', False),
            passive_effects=item_data.get('passive_effects', []), visuals=False
        )
        items.append(item)
    return items

if __name__ == '__main__':
    items_to_learn_with = load_all_items_from_json('items.json')
    env = BackpackEnv(items=items_to_learn_with, backpack_cols=BACKPACK_COLS, backpack_rows=BACKPACK_ROWS)
    env = ActionMasker(env, lambda env: env.action_masks())
    print("Maskable environment created successfully.")

    policy_kwargs = dict(
        features_extractor_class=CustomCNN,
        features_extractor_kwargs=dict(features_dim=128),
    )

    # --- FIX: Use the imported CnnPolicy class, not the string ---
    model = MaskablePPO(
        CnnPolicy, # <-- Use the class directly
        env,
        policy_kwargs=policy_kwargs,
        verbose=1,
        device="cuda",
        tensorboard_log="./ppo_maskable_backpack_tensorboard/"
    )

    print(f"Starting training on {torch.cuda.get_device_name(0)} with MaskablePPO policy...")
    
    model.learn(total_timesteps=TRAINING_TIMESTEPS, progress_bar=True)

    model.save(MODEL_SAVE_PATH)
    print(f"Training complete! Model saved to '{MODEL_SAVE_PATH}.zip'")