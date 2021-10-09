import typing
from dataclasses import dataclass
from enum import Enum


class MethodCategory(Enum):
    OTHER = "0_other"
    GATHERING = "1_gathering"
    REFINING = "2_refining"
    CRAFTING = "3_crafting"

    def __lt__(self, other):
        return self.value < other.value


@dataclass
class MethodDefinition:
    category: MethodCategory
    name: str

    def __lt__(self, other):
        return self.category < other.category and self.name < other.name


class Method(Enum):
    # gathering
    MINING = MethodDefinition(MethodCategory.GATHERING, "mining")
    TRACKING_AND_SKINNING = MethodDefinition(MethodCategory.GATHERING, "tracking and skinning")
    FISHING = MethodDefinition(MethodCategory.GATHERING, "fishing")
    LOGGING = MethodDefinition(MethodCategory.GATHERING, "logging")
    HARVESTING = MethodDefinition(MethodCategory.GATHERING, "harvesting")
    # refining
    SMELTING = MethodDefinition(MethodCategory.REFINING, "smelting")
    STONECUTTING = MethodDefinition(MethodCategory.REFINING, "stonecutting")
    LEATHERWORKING = MethodDefinition(MethodCategory.REFINING, "leatherworking")
    WEAVING = MethodDefinition(MethodCategory.REFINING, "weaving")
    WOODWORKING = MethodDefinition(MethodCategory.REFINING, "woodworking")
    # crafting
    WEAPONSMITHING = MethodDefinition(MethodCategory.CRAFTING, "weaponsmithing")
    ARMORING = MethodDefinition(MethodCategory.CRAFTING, "armoring")
    ENGINEERING = MethodDefinition(MethodCategory.CRAFTING, "engineering")
    JEWELCRAFTING = MethodDefinition(MethodCategory.CRAFTING, "jewelcrafting")
    ARCANA = MethodDefinition(MethodCategory.CRAFTING, "arcana")
    COOKING = MethodDefinition(MethodCategory.CRAFTING, "cooking")
    FURNISHING = MethodDefinition(MethodCategory.CRAFTING, "furnishing")
    # others
    EXPLORING = MethodDefinition(MethodCategory.OTHER, "exploring")
    HUNTING = MethodDefinition(MethodCategory.OTHER, "hunting")
    UNKNOWN = MethodDefinition(MethodCategory.OTHER, "unknown")

    def __lt__(self, other):
        return self.value < other.value


@dataclass
class Ingredient:
    entry: 'typing.Any'
    units: int

    def components(self):
        """
        Creates a new recipe on the components required to obtain this ingredient.
        Ingredients with no further components return a list of themselves.

        i.e an ingredient of. "10 rugged leather" becomes "[40 coarse leather, 10 tannin]".
        :return:
        """
        if self.entry.recipe is None:
            return [self]
        return self.entry.recipe.multiplied(self.units)

    def __lt__(self, other):
        return self.entry < other.entry


@dataclass
class Recipe:
    ingredients: list[Ingredient]

    def multiplied(self, multiplier):
        """
        Creates a new recipe where all ingredients' units have been multiplied by a given multiplier.
        :param multiplier:int
        :return:
        """
        ingredients_m = []
        for ingredient in self.ingredients:
            ingredients_m.append(Ingredient(ingredient.entry, ingredient.units * multiplier))
        return Recipe(ingredients_m)

    def components(self):
        """
        Creates a new recipe where all ingredients' entries have been replaced by their components and multiplier by their components' multipliers.

        i.e a recipe of. "10 Coarse Leather & 5 Rawhide" becomes "40 Rawhide & 5 Rawhide".
        :return:
        """
        components = []
        for ingredient in self.ingredients:
            if ingredient.entry.recipe is None:
                components.append(ingredient)
            else:
                for component_ingredient in ingredient.components().ingredients:
                    components.append(component_ingredient)
        return Recipe(components)

    @staticmethod
    def combined(recipes):
        """
        Merges multiple recipes together, i.e. a recipe of "40 Rawhide" and another recipe of "5 Rawhide" becomes "40 Rawhide & 5 Rawhide"
        :param recipes:list[Recipe]
        :return:
        """
        ingredients = []
        for recipe in recipes:
            for ingredient in recipe.ingredients:
                ingredients.append(ingredient)
        return Recipe(ingredients)

    def merged(self):
        """
        Creates a new recipe where ingredients of equal types are merged together, i.e. a recipe of "40 Rawhide & 5 Rawhide" becomes "45 Rawhide".
        :return:
        """
        sum_by_name = {}
        for ingredient in self.ingredients:
            existing_units = sum_by_name.get(ingredient.entry.name, 0)
            if ingredient.entry.merge:
                sum_by_name[ingredient.entry.name] = existing_units + ingredient.units
            else:
                sum_by_name[ingredient.entry.name] = existing_units if existing_units > ingredient.units else ingredient.units
        ingredient_list = []
        for (name, units) in sum_by_name.items():
            ingredient_list.append(Ingredient(Resource.lookup(name), units))
        return Recipe(ingredient_list)

    def sorted(self):
        """
        Creates a sorted recipe based on ingredients' resource's method category, method, and name.
        :return:
        """
        ingredients_sortable_iter = map(lambda ingredient: [
            ingredient.entry.method.value.category.value,
            ingredient.entry.method.value.name,
            ingredient.entry.name,
            ingredient
        ], self.ingredients)
        ingredients_sortable = list(ingredients_sortable_iter)
        ingredients_sortable.sort()
        ingredients = []
        for entry in ingredients_sortable:
            ingredients.append(entry[3])
        return Recipe(ingredients)

    def method_category_filtered(self, method_category):
        """
        Creates a recipe based on only ingredients whose resource's method category matches the given method category.
        :param method_category:MethodCategory
        :return:
        """
        ingredients = []
        for ingredient in self.ingredients:
            if ingredient.entry.method.value.category == method_category:
                ingredients.append(ingredient)
        return Recipe(ingredients)

    def markdown(self):
        """
        Formats table to a readable table as such;
        ```
        ### <method>
        - <units> <resource name>
        - <units> <resource name>

        ### <method>
        - <units> <resource name>
        ...
        ```
        :return:
        """
        output = []
        current_method = None
        for ingredient in self.ingredients:
            if ingredient.entry.method != current_method:
                if current_method is not None:
                    output.append("")
                current_method = ingredient.entry.method
                output.append(f"### {ingredient.entry.method.value.name}")
            output.append(f"- {ingredient.units: 4d} {ingredient.entry.name}")
        return "\n".join(output)

    @staticmethod
    def only(resource, units):
        """
        Creates a recipe with a single resource as its sole ingredient.

        :param resource:Resource
        :param units:int
        :return:
        """
        return Recipe([Ingredient(resource, units)])


@dataclass
class Resource:
    name: str
    method: Method
    recipe: Recipe
    merge: bool

    @staticmethod
    def define(name, method=Method.UNKNOWN, ingredients=None, merge=True):
        if method.value.category in [MethodCategory.REFINING, MethodCategory.CRAFTING] and ingredients is None:
            print(f"[WARN] Resource.define(name, method, ingredients) where ingredients is None and method = {method} for name = \"{name}\"")
        recipe = None if ingredients is None else Recipe(ingredients)
        resource_type = Resource(name, method, recipe, merge)
        RESOURCE_TYPES[name] = resource_type
        return resource_type

    @staticmethod
    def lookup(name):
        resource_type = RESOURCE_TYPES.get(name, None)
        if resource_type is not None:
            return resource_type
        print(f"[WARN] Unable to Resource.lookup(name) where name == \"{name}\", declaring a new resource;")
        print(f"[WARN] ```Resource.define(\"{name}\", Method.UNKNOWN)```.")
        return Resource.define(name)

    def __lt__(self, other):
        return self.method < other.method and self.name < other.name


RESOURCE_TYPES: dict[str, Resource] = {}

# -------------------------------- gathering ---------------------------------------------

# mining
STONE = Resource.define("stone", Method.MINING)
IRON_ORE = Resource.define("iron ore", Method.MINING)
OIL = Resource.define("oil", Method.MINING)
SILVER_ORE = Resource.define("silver ore", Method.MINING)
GOLD_ORE = Resource.define("gold ore", Method.MINING)
GLEAMING_LODESTONE = Resource.define("gleaming lodestone", Method.MINING)

# tracking and skinning
RAWHIDE = Resource.define("rawhide", Method.TRACKING_AND_SKINNING)
FEATHERS = Resource.define("feathers", Method.TRACKING_AND_SKINNING)
RED_MEAT = Resource.define("red meat", Method.TRACKING_AND_SKINNING)

# fishing
FISH_OIL = Resource.define("fish oil", Method.FISHING)

# logging
GREEN_WOOD = Resource.define("green wood", Method.LOGGING)
AGED_WOOD = Resource.define("aged wood", Method.LOGGING)

# harvesting
FIBERS = Resource.define("fibers", Method.HARVESTING)
BRIAR_BUDS = Resource.define("briar buds", Method.HARVESTING)
LIFEBLOOM_STEM = Resource.define("lifebloom stem", Method.HARVESTING)
SUNCREEPER_TENDRIL = Resource.define("suncreeper tendril", Method.HARVESTING)
LIFEBLOOM_FLOWER = Resource.define("lifebloom flower", Method.HARVESTING)
LIFE_MOTE = Resource.define("life mote", Method.HARVESTING)
PETALCAP = Resource.define("petalcap", Method.HARVESTING)
SPINECAP = Resource.define("spinecap", Method.HARVESTING)
WOODLOUSE_BAIT = Resource.define("woodlouse bait", Method.HARVESTING)
NIGHTCRAWLER_BAIT = Resource.define("nightcrawler bait", Method.HARVESTING)
POTATO = Resource.define("potato", Method.HARVESTING)
GARLIC = Resource.define("garlic", Method.HARVESTING)
NUTMEG = Resource.define("nutmeg", Method.HARVESTING)
PAPRIKA = Resource.define("paprika", Method.HARVESTING)
GINGER = Resource.define("ginger", Method.HARVESTING)
STRAWBERRY = Resource.define("strawberry", Method.HARVESTING)
ONION = Resource.define("onion", Method.HARVESTING)
CARROT = Resource.define("carrot", Method.HARVESTING)
CORN = Resource.define("corn", Method.HARVESTING)

# exploring
LYNX = Resource.define("lynx", Method.HUNTING, merge=False)
BOAR = Resource.define("boar", Method.HUNTING, merge=False)
GOAT = Resource.define("goat", Method.HUNTING, merge=False)
SHEEP = Resource.define("sheep", Method.HUNTING, merge=False)
ELK = Resource.define("elk", Method.HUNTING, merge=False)
TURKEY = Resource.define("turkey", Method.HUNTING, merge=False)
RABBITS = Resource.define("rabbits", Method.HUNTING, merge=False)
WOLVES = Resource.define("wolves", Method.HUNTING, merge=False)
TANNIN = Resource.define("tannin", Method.EXPLORING)
SANDPAPER = Resource.define("sandpaper", Method.EXPLORING)
CROSSWEAVE = Resource.define("crossweave", Method.EXPLORING)
SAND_FLUX = Resource.define("sand flux", Method.EXPLORING)
WATER = Resource.define("water", Method.EXPLORING)
MILK = Resource.define("milk", Method.EXPLORING)
HONEY = Resource.define("honey", Method.EXPLORING)
SUGAR = Resource.define("sugar", Method.EXPLORING)
FLINT = Resource.define("flint", Method.EXPLORING)

# -------------------------------- refining ----------------------------------------------

# smelting
CHARCOAL = Resource.define("charcoal", Method.SMELTING, [Ingredient(GREEN_WOOD, 2)])
IRON_INGOT = Resource.define("iron ingot", Method.SMELTING, [Ingredient(IRON_ORE, 4)])
STEEL_INGOT = Resource.define("steel ingot", Method.SMELTING, [Ingredient(IRON_INGOT, 3), Ingredient(SAND_FLUX, 1), Ingredient(CHARCOAL, 2)])
SILVER_INGOT = Resource.define("silver ingot", Method.SMELTING, [Ingredient(SILVER_ORE, 4)])
GOLD_INGOT = Resource.define("gold ingot", Method.SMELTING, [Ingredient(GOLD_ORE, 5), Ingredient(SILVER_INGOT, 2), Ingredient(SAND_FLUX, 1)])

# stonecutting
STONE_BLOCK = Resource.define("stone block", Method.STONECUTTING, [Ingredient(STONE, 4)])
STONE_BRICK = Resource.define("stone brick", Method.STONECUTTING, [Ingredient(STONE_BLOCK, 4), Ingredient(SANDPAPER, 1)])

# leatherworking
COARSE_LEATHER = Resource.define("coarse leather", Method.LEATHERWORKING, [Ingredient(RAWHIDE, 4)])
RUGGED_LEATHER = Resource.define("rugged leather", Method.LEATHERWORKING, [Ingredient(TANNIN, 1), Ingredient(COARSE_LEATHER, 4)])

# weaving
LINEN = Resource.define("linen", Method.WEAVING, [Ingredient(FIBERS, 4)])
SATEEN = Resource.define("sateen", Method.WEAVING, [Ingredient(LINEN, 4), Ingredient(CROSSWEAVE, 1)])

# woodworking
TIMBER = Resource.define("timber", Method.WOODWORKING, [Ingredient(GREEN_WOOD, 4)])
LUMBER = Resource.define("lumber", Method.WOODWORKING, [Ingredient(AGED_WOOD, 4), Ingredient(TIMBER, 2)])

# -------------------------------- crafting ----------------------------------------------

# weaponsmithing
Resource.define("bruising crude iron armaments", Method.WEAPONSMITHING, [Ingredient(IRON_ORE, 20), Ingredient(GREEN_WOOD, 20), Ingredient(RAWHIDE, 10)])
Resource.define("crushing crude iron armaments", Method.WEAPONSMITHING, [Ingredient(IRON_ORE, 20), Ingredient(GREEN_WOOD, 15), Ingredient(RAWHIDE, 15)])
Resource.define("bulwark crude iron armaments", Method.WEAPONSMITHING, [Ingredient(IRON_ORE, 15), Ingredient(GREEN_WOOD, 3), Ingredient(RAWHIDE, 12)])
Resource.define("ransacking crude iron armaments", Method.WEAPONSMITHING, [Ingredient(IRON_ORE, 10), Ingredient(GREEN_WOOD, 20), Ingredient(RAWHIDE, 20)])
Resource.define("impaling crude iron armaments", Method.WEAPONSMITHING, [Ingredient(IRON_ORE, 8), Ingredient(GREEN_WOOD, 14), Ingredient(RAWHIDE, 8)])
Resource.define("reaving crude iron armaments", Method.WEAPONSMITHING, [Ingredient(IRON_ORE, 50), Ingredient(GREEN_WOOD, 15), Ingredient(RAWHIDE, 25)])
Resource.define("gashing crude iron armaments", Method.WEAPONSMITHING, [Ingredient(IRON_ORE, 30), Ingredient(GREEN_WOOD, 30), Ingredient(RAWHIDE, 30)])

Resource.define("cleaving crude iron armaments", Method.WEAPONSMITHING, [Ingredient(IRON_ORE, 15), Ingredient(GREEN_WOOD, 20), Ingredient(RAWHIDE, 25)])
Resource.define("gashing iron armaments", Method.WEAPONSMITHING, [Ingredient(IRON_INGOT, 20), Ingredient(TIMBER, 15), Ingredient(COARSE_LEATHER, 5)])
Resource.define("ransacking iron armaments", Method.WEAPONSMITHING, [Ingredient(IRON_INGOT, 12), Ingredient(TIMBER, 16), Ingredient(COARSE_LEATHER, 12)])
# armoring
Resource.define("hardened crude iron armor", Method.ARMORING, [Ingredient(IRON_ORE, 20), Ingredient(RAWHIDE, 15), Ingredient(FIBERS, 15)])
Resource.define("impenetrable crude iron armor", Method.ARMORING, [Ingredient(IRON_ORE, 12), Ingredient(RAWHIDE, 12), Ingredient(FIBERS, 26)])
Resource.define("toughened crude iron armor", Method.ARMORING, [Ingredient(IRON_ORE, 9), Ingredient(RAWHIDE, 9), Ingredient(FIBERS, 12)])
Resource.define("rugged crude iron armor", Method.ARMORING, [Ingredient(IRON_ORE, 14), Ingredient(RAWHIDE, 6), Ingredient(FIBERS, 10)])
Resource.define("stout crude iron armor", Method.ARMORING, [Ingredient(IRON_ORE, 7), Ingredient(RAWHIDE, 15), Ingredient(FIBERS, 8)])
Resource.define("unyielding crude iron armor", Method.ARMORING, [Ingredient(IRON_ORE, 20), Ingredient(RAWHIDE, 10), Ingredient(FIBERS, 20)])

Resource.define("hardened iron armor", Method.ARMORING, [Ingredient(IRON_INGOT, 10), Ingredient(COARSE_LEATHER, 5), Ingredient(LINEN, 10)])
Resource.define("impenetrable iron armor", Method.ARMORING, [Ingredient(IRON_INGOT, 13), Ingredient(COARSE_LEATHER, 13), Ingredient(LINEN, 14)])
Resource.define("toughened iron armor", Method.ARMORING, [Ingredient(IRON_INGOT, 10), Ingredient(COARSE_LEATHER, 5), Ingredient(LINEN, 5)])
Resource.define("rugged iron armor", Method.ARMORING, [Ingredient(IRON_INGOT, 5), Ingredient(COARSE_LEATHER, 5), Ingredient(LINEN, 10)])
Resource.define("stout iron armor", Method.ARMORING, [Ingredient(IRON_INGOT, 5), Ingredient(COARSE_LEATHER, 10), Ingredient(LINEN, 5)])
Resource.define("unyielding iron armor", Method.ARMORING, [Ingredient(IRON_INGOT, 10), Ingredient(COARSE_LEATHER, 10), Ingredient(LINEN, 5)])

# engineering
pass

# jewelcrafting
pass

# arcana
Resource.define("weak mana potion", Method.ARCANA, [Ingredient(BRIAR_BUDS, 1), Ingredient(WATER, 1)])
Resource.define("common health potion", Method.ARCANA, [Ingredient(LIFEBLOOM_STEM, 1), Ingredient(WATER, 1)])
Resource.define("common mana potion", Method.ARCANA, [Ingredient(SUNCREEPER_TENDRIL, 1), Ingredient(WATER, 1)])
Resource.define("common regeneration potion", Method.ARCANA, [Ingredient(LIFEBLOOM_STEM, 1), Ingredient(LIFE_MOTE, 1), Ingredient(WATER, 1)])
Resource.define("strong health potion", Method.ARCANA, [Ingredient(GLEAMING_LODESTONE, 1), Ingredient(PETALCAP, 1), Ingredient(WATER, 1)])
Resource.define("strong regeneration potion", Method.ARCANA, [Ingredient(GLEAMING_LODESTONE, 1), Ingredient(SPINECAP, 1), Ingredient(WATER, 1)])
Resource.define("powerful regeneration potion", Method.ARCANA, [Ingredient(LIFE_MOTE, 1), Ingredient(LIFEBLOOM_FLOWER, 1), Ingredient(WATER, 1)])

# cooking
Resource.define("light ration", Method.COOKING, [Ingredient(MILK, 1)])
Resource.define("energizing light ration", Method.COOKING, [Ingredient(MILK, 1)])
Resource.define("travel ration", Method.COOKING, [Ingredient(MILK, 1), Ingredient(HONEY, 1)])
Resource.define("energizing travel ration", Method.COOKING, [Ingredient(MILK, 1), Ingredient(HONEY, 1)])
Resource.define("yoghurt provisions", Method.COOKING, [Ingredient(STRAWBERRY, 8), Ingredient(MILK, 8), Ingredient(SUGAR, 8)])
Resource.define("spice provisions", Method.COOKING, [Ingredient(NUTMEG, 8), Ingredient(PAPRIKA, 8), Ingredient(GINGER, 8)])
Resource.define("garlic meat meat", Method.COOKING, [Ingredient(RED_MEAT, 5), Ingredient(POTATO, 5), Ingredient(GARLIC, 5)])
Resource.define("vegetable supplies", Method.COOKING, [Ingredient(ONION, 12), Ingredient(CORN, 12), Ingredient(CARROT, 12)])

# furnishing
pass
