from enum import Enum

# --- Enums for Item Properties ---
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
    MELEE = "Melee"; RANGED = "Ranged"; EFFECT = "Effect"; NATURE = "Nature"
    MAGIC = "Magic"; HOLY = "Holy"; DARK = "Dark"; VAMPIRIC = "Vampiric"
    FIRE = "Fire"; ICE = "Ice"; TREASURE = "Treasure"; MUSICAL = "Musical"

class ItemType(Enum):
    WEAPON = "Weapon"; SHIELD = "Shield"; ACCESSORY = "Accessory"; POTION = "Potion"
    SPELL = "Spell"; FOOD = "Food"; BOOK = "Book"; PET = "Pet"; HELMET = "Helmet"
    ARMOR = "Armor"; GEMSTONE = "Gemstone"; SKILL = "Skill"

# --- Lists for Editor Dropdowns ---
EFFECT_TYPES = [
    "ADD_SCORE_TO_SELF", "ADD_SCORE_TO_TARGET",
    "MULTIPLY_SCORE_OF_SELF", "MULTIPLY_SCORE_OF_TARGET",
    "ADD_ELEMENT_TO_TARGET"
]

CONDITION_TYPES = [
    "requires_name",
    "requires_type",
    "requires_element",
    "requires_cooldown",
    "requires_start_of_battle",
    "requires_empty",
    "must_be_different"
]

