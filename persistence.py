from recipes import *
import yaml

BOARDS_FILE_PATH = "boards.yml"


def load_all():
    """
    Loads a mapping of names to NewWorldRecipe containing a combined list of all final ingredients required for missions.
    :return:
    """
    recipes_by_town = {}
    with open(BOARDS_FILE_PATH) as boards_file:
        boards = yaml.load(boards_file, Loader=yaml.FullLoader)
        for board in boards:
            board_name = board["name"]
            recipes = []
            for board_recipe in board["recipes"]:
                recipe_resource_text = board_recipe["resource"]
                recipe_units = int(board_recipe["units"])
                recipe_resource = Resource.lookup(recipe_resource_text)
                recipe = Recipe.only(recipe_resource, recipe_units)
                recipes.append(recipe)
            recipes_by_town[board_name] = Recipe.combined(recipes)
    return recipes_by_town


def load(town):
    """
    Loads a NewWorldRecipe containing a combined list of all final ingredients required for missions.
    :param town:
    :return:
    """
    mapping = load_all()
    mapping.get(town, Recipe([]))


def save_all(recipes_by_town):
    """
    Saves a mapping of names to NewWorldRecipe containing a combined list of all final ingredients required for missions.
    :param recipes_by_town:
    :return:
    """
    data = []
    for (town, recipe) in recipes_by_town.items():
        data_recipes = []
        for ingredient in recipe.ingredients:
            data_recipes.append({
                "resource": ingredient.entry.name,
                "units": ingredient.units
            })
        data.append({
            "name": town,
            "recipes": data_recipes
        })
    text = yaml.dump(data)
    with open(BOARDS_FILE_PATH, "w") as boards_file:
        boards_file.write(text)


def save(town, recipe):
    """
    Saves a town's NewWorldRecipe containing a combined list of all final ingredients required for missions.
    :param town:
    :param recipe:
    :return:
    """
    mapping = load_all()
    mapping[town] = recipe
    save_all(mapping)
