import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import jaccard_score

class RecipeProcessor:
    def __init__(self):
        self.model = joblib.load("data/best_classification_model.pkl")
        self.similar_recipes = pd.read_csv("data/similar_recipes.csv")

    def predict_rating(self, ingredient_vector):
        ingredient_vector = np.array(ingredient_vector).reshape(1, -1)
        
        predicted_class = self.model.predict(ingredient_vector)[0]
        
        if predicted_class == 0:
            return "bad"
        elif predicted_class == 1:
            return "so-so"
        else:
            return "great"  

    def get_nutrition(self, ingredient):
        nutrition_data = pd.read_csv("data/nutrition_facts.csv", index_col=0)  
        if ingredient in nutrition_data.index:
            return nutrition_data.loc[ingredient]
        return None

    def find_similar_recipes(self, recipe_vector, recipe_data, title_column):
    

        similarity = []
        for _, row in recipe_data.iterrows():
            similarity.append(jaccard_score(recipe_vector, row.values, average='binary'))
        df = recipe_data.copy()
        df["similarity"] = similarity

        top_recipes = df.sort_values(by='similarity', ascending=False).head(3)
        return self.similar_recipes[self.similar_recipes["title"].isin(title_column[top_recipes.index])]

   
class DailyMenuGenerator:

    def __init__(self, recipes_csv, nutrition_csv):
        self.recipes = pd.read_csv(recipes_csv)
        self.nutrition = pd.read_csv(nutrition_csv)

        # auto-detect columns
        self.title_col = self._find_col(["title", "name"])
        self.rating_col = self._find_col(["rating"])
        self.url_col = self._find_col(["url", "link"])
        self.ingredients_col = self._find_col(["ingredient", "ingredients", "ing"])

        self.recipes[self.ingredients_col] = self.recipes[self.ingredients_col].astype(str).str.lower()

    def _find_col(self, keys):
        for c in self.recipes.columns:
            for k in keys:
                if k in c.lower():
                    return c
        raise ValueError("Column not found: " + str(keys))

    # ------------------ MEAL DETECTION ------------------

    def _detect_meal_type(self, ingredients_text):
        t = ingredients_text.lower()

        if any(x in t for x in ["egg", "banana", "oat", "milk", "honey", "bread", "muffin"]):
            return "breakfast"

        if any(x in t for x in ["rice", "salad", "chicken", "tomato", "lettuce", "pasta"]):
            return "lunch"

        return "dinner"

    # ------------------ MAIN GENERATOR ------------------

    def generate_daily_menu(self):

        self.recipes["meal_type"] = self.recipes[self.ingredients_col].apply(self._detect_meal_type)

        breakfasts = self.recipes[self.recipes["meal_type"] == "breakfast"]
        lunches = self.recipes[self.recipes["meal_type"] == "lunch"]
        dinners = self.recipes[self.recipes["meal_type"] == "dinner"]

        # fallback if any group empty
        if breakfasts.empty:
            breakfasts = self.recipes.sample(5)
        if lunches.empty:
            lunches = self.recipes.sample(5)
        if dinners.empty:
            dinners = self.recipes.sample(5)

        b = breakfasts.sort_values(self.rating_col, ascending=False).iloc[0]
        l = lunches.sort_values(self.rating_col, ascending=False).iloc[0]
        d = dinners.sort_values(self.rating_col, ascending=False).iloc[0]

        return (b, l, d)


   
    # ------------------ MAIN MENU GENERATOR ------------------

    # def generate_daily_menu(self, trials=500):
        best_menu = None
        best_score = 0

        breakfasts = self._filter_meals("breakfast")
        lunches = self._filter_meals("lunch")
        dinners = self._filter_meals("dinner")

        if breakfasts.empty or lunches.empty or dinners.empty:
            return None

        for _ in range(trials):
            b = breakfasts.sample(1).iloc[0]
            l = lunches.sample(1).iloc[0]
            d = dinners.sample(1).iloc[0]

            nutrients = self._calculate_nutrients([b, l, d])

            if self._valid_menu(nutrients):
                score = b[self.rating_col] + l[self.rating_col] + d[self.rating_col]
                if score > best_score:
                    best_score = score
                    best_menu = (b, l, d, nutrients)

        return best_menu if best_menu else (b, l, d, nutrients)


    # ------------------ MEAL FILTER ------------------

    def _filter_meals(self, meal_type):

        keywords = {
            "breakfast": ["egg", "omelet", "muffin", "toast", "banana", "oat",
                           "berry","blackberry","blueberry","cherry","cranberry","fig",
        "grape","grapefruit","guava","honey","honeydew","jam or jelly",
        "maple syrup","melon","orange","orange juice","peach","pear",
        "pineapple","plum","pomegranate","pomegranate juice","raisin",
        "raspberry","strawberry","watermelon",
        "egg","egg nog","butter","buttermilk","cream cheese","cottage cheese",
        "ricotta","feta","oat","oatmeal","rye","wheat/gluten-free","sourdough",
        "flat bread","tortillas","coffee","vanilla","cinnamon","nutmeg"],
            "lunch": ["salad", "rice", "chicken", "pasta", "tofu","arugula","asparagus","avocado","beet","bell pepper","bok choy",
        "broccoli", "rabe","brussel sprout","cabbage","carrot",
        "cauliflower","celery","chickpea","cucumber","eggplant","endive",
        "green bean","green onion/scallion","jerusalem artichoke","kale",
        "lettuce","lima bean","mushroom","okra","olive","onion","parsley",
        "parsnip","pea","pepper","radicchio","radish","rutabaga","spinach",
        "squash","sweet potato/yam","tomatillo","tomato","turnip","vegetable",
        "watercress","zucchini","tofu","hummus","lentil","quinoa","rice",
        "wild rice","orzo"],
            "dinner": ["beef", "fish", "soup", "steak", "roast","beef"," rib","beef shank","beef tenderloin","ground beef",
        "lamb","lamb chop","lamb shank","ground lamb","pork","pork chop",
        "pork rib","pork tenderloin","veal","venison","rabbit","quail",
        "sausage","salmon","sardine","shrimp","scallop","snapper","squid",
        "swordfish","tilapia","cod","fish","lobster","mussel","oyster",
        "octopus","crab","shellfish","potato","pumpkin","root vegetable",
        "yuca","plantain","soy sauce","sesame oil","vinegar","marinade",
        "mustard","salsa","curry"]
        }

        return self.recipes[
            self.recipes[self.ingredients_col]
            .apply(lambda x: any(k in x for k in keywords[meal_type]))
        ]

    # ------------------ NUTRITION ------------------

    def _calculate_nutrients(self, meals):
        totals = {}

        for meal in meals:
            for ing in meal[self.ingredients_col].split(","):
                ing = ing.strip().lower()

                row = self.nutrition[
                    self.nutrition[self.nut_ing_col]
                    .str.contains(ing, regex=False)
                ]

                if not row.empty:
                    for col in self.nutrition.columns[1:]:
                        totals[col] = totals.get(col, 0) + row.iloc[0][col]

        return totals


    # ------------------ VALIDATION ------------------

    def _valid_menu(self, nutrients):
        return all(v <= 120 for v in nutrients.values())

    # ------------------ PRINT ------------------

    def print_menu(self, menu):

        meals = ["BREAKFAST", "LUNCH", "DINNER"]

        for name, recipe in zip(meals, menu):

            print(name)
            print("-" * 25)

            print(f"{recipe[self.title_col]} (rating: {recipe[self.rating_col]})")

            print("Ingredients:")
            for ing in recipe[self.ingredients_col].split(","):
                print("-", ing.strip())

            print("URL:", recipe[self.url_col])
            print()


    