#!/usr/bin/env python3

import argparse
import pandas as pd
import numpy as np
import sys
from recipes import RecipeProcessor
from recipes import DailyMenuGenerator


def print_forecast(ingredients_list, recipe_processor):
    forecast = recipe_processor.predict_rating(ingredients_list)
    print("I. OUR FORECAST")
    print(f"You might find it tasty, but in our opinion, it is a {forecast} idea to have a dish with that list of ingredients.\n")

def print_nutrition_facts(ingredients_list, recipe_processor):
    print("II. NUTRITION FACTS")
    for ingredient in ingredients_list:
        nutrition_info = recipe_processor.get_nutrition(ingredient)
        if nutrition_info is not None:
            print(f"{ingredient.capitalize()}")
            for nutrient, value in nutrition_info.fillna(0).items():
                if value:
                    print(f"{nutrient} - {value}% of Daily Value")
        else:
            print(f"{ingredient.capitalize()} - No nutrition data available.")
        print("")

def print_similar_recipes(ingredients_list, recipe_processor, recipe_data, title_column):
    print("III. TOP-3 SIMILAR RECIPES:")
    ingredient_columns = recipe_data.columns
    recipe_vector = np.zeros(len(ingredient_columns))

    for ingredient in ingredients_list:
        if ingredient in recipe_data.columns:
            recipe_vector[recipe_data.columns.get_loc(ingredient)] = 1

    similar_recipes = recipe_processor.find_similar_recipes(recipe_vector, recipe_data, title_column)
    for _, row in similar_recipes.iterrows():
        print(f"- {row['title']}, rating: {row['rating']}, URL: {row['url']}")

def main():
    if len(sys.argv) < 2:
        print("Please provide a list of ingredients as input.")
        sys.exit(1)
    generator = DailyMenuGenerator(
        "data/similar_recipes.csv",
        "data/nutrition_facts.csv"
    )

    generator = DailyMenuGenerator(
    "data/similar_recipes.csv",
    "data/nutrition_facts.csv"
)

    menu = generator.generate_daily_menu()
    generator.print_menu(menu)
    
    parser = argparse.ArgumentParser(description="Find similar recipes and provide insights.")
    parser.add_argument("ingredients", nargs='+', help="List of ingredients to use in the recipe.")
    args = parser.parse_args()
    user_ingredients = [ingredient.replace(",", "").strip().lower() for ingredient in args.ingredients]

    data = pd.read_csv("data/epi_r.csv")
    ingredient_columns = pd.read_csv("data/ingredients.csv", header=None).iloc[:,0].to_list()
    ingredient_columns = [ingredient.strip() for ingredient in ingredient_columns]
    recipe_data = data[ingredient_columns]
    

    recipe_vector = np.zeros(len(ingredient_columns))

    for ingredient in user_ingredients:
        for i, ingredient_column in enumerate(ingredient_columns):
            if "/" in ingredient_column:
                ingredient_column_mult = ingredient_column.split("/")
                if ingredient in ingredient_column_mult:
                    recipe_vector[i] = 1
                    break
            else:
                if ingredient in ingredient_column:
                    recipe_vector[i] = 1
                    break
        else:
            sys.exit(f"Error: {ingredient} - ingredient not found")

    processor = RecipeProcessor()
    
    print_forecast(recipe_vector, processor)
    print_nutrition_facts(user_ingredients, processor)
    print_similar_recipes(user_ingredients, processor, recipe_data, data["title"])

if __name__ == "__main__":
    main()
