import json
import random
from datasets import load_dataset
import os

def main():
    print("Loading Recipe dataset...")
    try:
        ds = load_dataset("corbt/all-recipes", split="train")
    except Exception as e:
        print(f"Failed to load: {e}")
        return
    
    print(f"Dataset loaded. Total recipes: {len(ds)}")
    
    indices = random.sample(range(len(ds)), 1000)
    
    recipes_to_save = []
    for idx, i in enumerate(indices):
        row = ds[i]
        
        title = row.get("name", f"Recipe {idx}")
        ingredients = row.get("ingredients", [])
        instructions = row.get("steps", [])
        
        recipe = {
            "title": title.title(),
            "cuisine": "Any",
            "diet_type": "non-vegetarian",
            "dietary_tags": [],
            "ingredients": [ing.strip() for ing in ingredients if ing.strip()],
            "instructions": [ins.strip() for ins in instructions if ins.strip()],
            "cook_time": str(row.get("minutes", "30")) + " minutes",
            "difficulty": "medium",
            "servings": 4
        }
        recipes_to_save.append(recipe)
        
    out_path = "/Users/ayushgupta/Desktop/multimodal_recipe_generator/sample_recipes.json"
    print(f"Saving {len(recipes_to_save)} recipes to {out_path}...")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(recipes_to_save, f, indent=2)
    print("Done!")

if __name__ == "__main__":
    main()
