from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re


# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
    name: str


@dataclass
class RequiredItem:
    name: str
    quantity: int


@dataclass
class Recipe(CookbookEntry):
    required_items: List[RequiredItem]


@dataclass
class Ingredient(CookbookEntry):
    cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = {}


# Task 1 helper (don't touch)
@app.route("/parse", methods=["POST"])
def parse():
    data = request.get_json()
    recipe_name = data.get("input", "")
    parsed_name = parse_handwriting(recipe_name)
    if parsed_name is None:
        return "Invalid recipe name", 400
    return jsonify({"msg": parsed_name}), 200


# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that
def parse_handwriting(recipeName: str) -> Union[str | None]:
    if len(recipeName) == 0:
        return None

    parsedRecipeName = ""

    # loop through and only add alphabets/whitespaces to new string
    for char in recipeName:
        if char.isalpha() or char == " ":
            parsedRecipeName += char
        if char == "_" or char == "-":  # replace '_' and '-' with " "
            parsedRecipeName += " "

    final = ""

    # capitalise each word in new string
    for word in parsedRecipeName.split():
        final += word.capitalize() + " "

    final = final.strip()  # remove leading/trailing whitespaces

    if len(final) == 0:
        return None

    return final


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route("/entry", methods=["POST"])
def create_entry():
    entry = request.get_json()

    entry_type = entry["type"]
    name = entry["name"]

    # error handling
    if entry_type not in ["recipe", "ingredient"]:
        return "'type' can only be recipe or ingredient", 400

    if entry_type == "ingredient" and entry["cookTime"] < 0:
        return "cookTime can only be greater than or equal to 0", 400

    if name in cookbook:
        return "entry names must be unique", 400

    if entry_type == "recipe":
        required_items = entry["requiredItems"]

        seen_item_names = []
        for item in required_items:
            if item["name"] in seen_item_names:
                return "item already exists", 400

            seen_item_names.append(item["name"])

    cookbook[name] = entry

    return "", 200


# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route("/summary", methods=["GET"])
def summary():
    name = request.args.get("name")

    # error checking
    if name not in cookbook:
        return "recipe with the corresponding name not found", 400

    if cookbook[name]["type"] != "recipe":
        return "name is not a recipe name", 400

    ingredients = get_ingredients(name, 1)
    if ingredients is None:
        return "recipe contains recipes/ingredients not in cookbook", 400

    total_time = 0
    res = {}

    # sum quantities of ingredients
    for ingredient_name, quantity in ingredients:
        if ingredient_name in res:
            res[ingredient_name] += quantity
        else:
            res[ingredient_name] = quantity

    # calculate total cook time for the recipe
    for ingredient_name, quantity in res.items():
        total_time += cookbook[ingredient_name]["cookTime"] * quantity

    answer = {
        "name": name,
        "cookTime": total_time,
        "ingredients": [
            {
                "name": n, 
                "quantity": qty
            } 
            for n, qty in res.items() # build ingredients list
        ], 
    }

    return answer, 200


# helper function to recursively get ingredients
def get_ingredients(name: str, quantity: int):
    # base case - item does not exist
    if name not in cookbook:
        return None

    entry = cookbook[name]
    
    # base case - reached leaf node (base ingredient for recipe)
    if entry["type"] == "ingredient":
        return [(name, quantity)]

    results = []

    for item in entry["requiredItems"]:
        item_name = item["name"]
        item_quantity = item["quantity"] * quantity

        # recurse on requiredItems
        child = get_ingredients(item_name, item_quantity)
        if child is None:
            return None

        results.extend(child)

    return results


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=8080)
