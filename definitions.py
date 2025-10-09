from enum import Enum

# --- Enums for Item Properties ---
# By placing these in a separate file, both main.py and editor.py can import and use them
# without duplicating code. This is a standard practice for larger projects.

class GridType(Enum): 
    EMPTY = 0
    OCCUPIED = 1
    STAR_A = 2
    STAR_B = 3
    STAR_C = 4

class Rarity(Enum): 
    COMMON = "Common"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"
    GODLY = "Godly"
    UNIQUE = "Unique"

class ItemClass(Enum): 
    NEUTRAL = "Neutral"
    RANGER = "Ranger"
    REAPER = "Reaper"
    BERSERKER = "Berserker"
    PYROMANCER = "Pyromancer"
    MAGE = "Mage"
    ADVENTURER = "Adventurer"

class Element(Enum):
    MELEE = "Melee"
    RANGED = "Ranged"
    EFFECT = "Effect"
    NATURE = "Nature"
    MAGIC = "Magic"
    HOLY = "Holy"
    DARK = "Dark"
    VAMPIRIC = "Vampiric"
    FIRE = "Fire"
    ICE = "Ice"
    TREASURE = "Treasure"
    MUSICAL = "Musical"

class ItemType(Enum):
    WEAPON = "Weapon"
    SHIELD = "Shield"
    ACCESSORY = "Accessory"
    POTION = "Potion"
    SPELL = "Spell"
    FOOD = "Food"
    BOOK = "Book"
    PET = "Pet"
    HELMET = "Helmet"
