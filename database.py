import requests
import time
import os
import json
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from langchain.docstore.document import Document

# Load environment variables
load_dotenv()

# Get Spoonacular API key from environment
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# Constants for API optimization
CACHE_DIR = "cache"
DATABASE_FILE = "meal_recipes.db"
MAX_BATCH_SIZE = 100  # Maximum recipes per API call
API_DELAY = 1  # Seconds between API calls
MAX_DAILY_CALLS = 150  # Free tier limit

# List of diet types to search for
DIET_TYPES = [
    "vegetarian", "vegan", "gluten free", "ketogenic", 
    "paleo", "whole30", "pescatarian", "dairy free"
]

# Different meal types
MEAL_TYPES = [
    "main course", "side dish", "dessert", "appetizer", 
    "salad", "bread", "breakfast", "soup", "beverage", "sauce", "snack"
]

def setup_directories():
    """Create necessary directories if they don't exist"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_path(category, meal_type, offset):
    """Generate a cache file path based on query parameters"""
    safe_category = category.replace(" ", "_") if category else "none"
    safe_meal = meal_type.replace(" ", "_") if meal_type else "none"
    return os.path.join(CACHE_DIR, f"{safe_category}_{safe_meal}_{offset}.json")

def save_to_cache(category, meal_type, offset, data):
    """Save API response to cache"""
    setup_directories()
    cache_path = get_cache_path(category, meal_type, offset)
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)

def load_from_cache(category, meal_type, offset):
    """Load API response from cache if available"""
    cache_path = get_cache_path(category, meal_type, offset)
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def set_spoonacular_api_key(key):
    """Set Spoonacular API key (can be called from frontend)"""
    global SPOONACULAR_API_KEY
    SPOONACULAR_API_KEY = key
    os.environ["SPOONACULAR_API_KEY"] = key
    return "API key set successfully"

def fetch_recipes(category=None, meal_type=None, offset=0, number=MAX_BATCH_SIZE, min_calories=None, max_calories=None):
    """Fetch recipes from Spoonacular API with caching and rate limiting"""
    # Check if API key is available
    if not SPOONACULAR_API_KEY:
        print("Error: Spoonacular API key not found. Please set it before fetching recipes.")
        return None, False
        
    # First check if we have this query cached
    cached_data = load_from_cache(category, meal_type, offset)
    if cached_data:
        print(f"Using cached data for {category} {meal_type} (offset: {offset})")
        return cached_data, False  # False indicates no API call was made
    
    # If not in cache, make API request
    url = "https://api.spoonacular.com/recipes/complexSearch"
    
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "addRecipeNutrition": True,
        "fillIngredients": True,
        "number": number,
        "offset": offset,
        "instructionsRequired": True
    }
    
    # Add optional filters
    if category:
        params["diet"] = category
    if meal_type:
        params["type"] = meal_type
    if min_calories:
        params["minCalories"] = min_calories
    if max_calories:
        params["maxCalories"] = max_calories
    
    print(f"Fetching from API: {category} {meal_type} (offset: {offset})")
    
    try:
        response = requests.get(url, params=params)
        
        # Handle API errors
        if response.status_code == 402:
            print("Daily API limit reached.")
            return "LIMIT_REACHED", True
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return None, True
        
        # Cache successful response
        data = response.json()
        save_to_cache(category, meal_type, offset, data)
        return data, True
        
    except Exception as e:
        print(f"Request failed: {e}")
        return None, True

def determine_cooking_status(recipe):
    """Determine if a recipe requires cooking or not"""
    # Check if recipe requires cooking based on meal type or instructions
    if "dishTypes" in recipe:
        no_cook_types = ["salad", "beverage", "drink", "snack"]
        for dish_type in recipe.get("dishTypes", []):
            if dish_type and any(no_cook in dish_type.lower() for no_cook in no_cook_types):
                return "uncooked"
    
    # Check title for no-cook keywords
    title = recipe.get("title", "")
    if title:
        title = title.lower()
        no_cook_keywords = ["raw", "no-cook", "no cook", "uncooked", "salad", 
                            "smoothie", "shake", "overnight", "yogurt"]
        for keyword in no_cook_keywords:
            if keyword in title:
                return "uncooked"
    
    # Check ready time - very short times may indicate no cooking
    if recipe.get("readyInMinutes", 0) < 10:
        return "likely_uncooked"
        
    # Default to cooked if we can't determine otherwise
    return "cooked"

def extract_recipe_data(recipe):
    """Extract relevant data from a recipe object"""
    nutrition = {
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0,
        "fiber": 0
    }
    
    # Extract nutrition info
    if "nutrition" in recipe and "nutrients" in recipe["nutrition"]:
        for nutrient in recipe["nutrition"]["nutrients"]:
            if nutrient["name"] == "Calories":
                nutrition["calories"] = nutrient["amount"]
            elif nutrient["name"] == "Protein":
                nutrition["protein"] = nutrient["amount"]
            elif nutrient["name"] == "Carbohydrates":
                nutrition["carbs"] = nutrient["amount"]
            elif nutrient["name"] == "Fat":
                nutrition["fat"] = nutrient["amount"]
            elif nutrient["name"] == "Fiber":
                nutrition["fiber"] = nutrient["amount"]
    
    # Determine if recipe requires cooking
    cooking_status = determine_cooking_status(recipe)
    
    # Extract category information (formerly diet tags)
    categories = []
    if "diets" in recipe:
        categories = recipe["diets"]
    
    # Extract meal type
    meal_type = "main course"  # default
    if "dishTypes" in recipe and recipe["dishTypes"]:
        for dish_type in recipe["dishTypes"]:
            if dish_type.lower() in [mt.lower() for mt in MEAL_TYPES]:
                meal_type = dish_type.lower()
                break
    
    # Extract basic recipe info
    recipe_data = {
        "id": recipe["id"],
        "title": recipe["title"],
        "image": recipe.get("image", ""),
        "source_url": recipe.get("sourceUrl", ""),
        "ready_in_minutes": recipe.get("readyInMinutes", 0),
        "servings": recipe.get("servings", 0),
        "summary": recipe.get("summary", ""),
        "calories": round(nutrition["calories"]),
        "protein": round(nutrition["protein"], 1),
        "carbs": round(nutrition["carbs"], 1),
        "fat": round(nutrition["fat"], 1),
        "fiber": round(nutrition["fiber"], 1),
        "cooking_status": cooking_status,
        "category": ",".join(categories) if categories else "",
        "meal_type": meal_type
    }
    
    # Extract ingredients
    ingredients = []
    if "extendedIngredients" in recipe:
        for ingredient in recipe["extendedIngredients"]:
            ingredients.append({
                "name": ingredient.get("name", ""),
                "amount": ingredient.get("amount", 0),
                "unit": ingredient.get("unit", "")
            })
    
    # Add custom tags based on nutrition
    diet_tags = []
    if nutrition["protein"] > 25:
        diet_tags.append("high_protein")
    if nutrition["carbs"] < 15:
        diet_tags.append("low_carb")
    if nutrition["fat"] < 10:
        diet_tags.append("low_fat")
    if nutrition["fiber"] > 8:
        diet_tags.append("high_fiber")
    
    return recipe_data, ingredients, diet_tags

def create_database():
    """Create the SQLite database and tables"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Create recipes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY,
        title TEXT,
        image TEXT,
        source_url TEXT,
        ready_in_minutes INTEGER,
        servings INTEGER,
        calories INTEGER,
        protein REAL,
        carbs REAL,
        fat REAL,
        fiber REAL,
        summary TEXT,
        cooking_status TEXT,
        category TEXT,
        meal_type TEXT
    )
    ''')
    
    # Create ingredients table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER,
        name TEXT,
        amount REAL,
        unit TEXT,
        FOREIGN KEY (recipe_id) REFERENCES recipes (id)
    )
    ''')
    
    # Create diet tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS diet_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER,
        tag TEXT,
        FOREIGN KEY (recipe_id) REFERENCES recipes (id)
    )
    ''')
    
    conn.commit()
    return conn, cursor

def save_to_database(recipe_data, ingredients, diet_tags):
    """Save a recipe and its related data to the database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Insert recipe
    cursor.execute('''
    INSERT OR REPLACE INTO recipes 
    (id, title, image, source_url, ready_in_minutes, servings, calories, protein, carbs, fat, fiber, summary, cooking_status, category, meal_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        recipe_data["id"], recipe_data["title"], recipe_data["image"], 
        recipe_data["source_url"], recipe_data["ready_in_minutes"], 
        recipe_data["servings"], recipe_data["calories"], recipe_data["protein"],
        recipe_data["carbs"], recipe_data["fat"], recipe_data["fiber"],
        recipe_data["summary"], recipe_data["cooking_status"], recipe_data["category"],
        recipe_data["meal_type"]
    ))
    
    # Delete existing ingredients and tags before inserting new ones
    cursor.execute('DELETE FROM ingredients WHERE recipe_id = ?', (recipe_data["id"],))
    cursor.execute('DELETE FROM diet_tags WHERE recipe_id = ?', (recipe_data["id"],))
    
    # Insert ingredients
    for ingredient in ingredients:
        cursor.execute('''
        INSERT INTO ingredients (recipe_id, name, amount, unit)
        VALUES (?, ?, ?, ?)
        ''', (
            recipe_data["id"], ingredient["name"], ingredient["amount"], ingredient["unit"]
        ))
    
    # Insert diet tags
    for tag in diet_tags:
        cursor.execute('''
        INSERT INTO diet_tags (recipe_id, tag)
        VALUES (?, ?)
        ''', (recipe_data["id"], tag))
    
    conn.commit()
    conn.close()

def collect_recipes(target_count=20, diet_type=None, meal_type=None, min_calories=None, max_calories=None):
    """Collect recipes from API and store in database"""
    setup_directories()
    create_database()
    
    # Track API calls
    api_calls = 0
    collected_count = 0
    offset = 0
    
    # If specific diet_type and meal_type are provided, only fetch those
    diet_types_to_fetch = [diet_type] if diet_type else DIET_TYPES
    meal_types_to_fetch = [meal_type] if meal_type else MEAL_TYPES
    
    try:
        for diet in diet_types_to_fetch:
            for meal in meal_types_to_fetch:
                # Check if we've collected enough recipes
                if collected_count >= target_count:
                    break
                
                # Check if we've hit the API call limit
                if api_calls >= MAX_DAILY_CALLS:
                    print(f"Reached daily limit of {MAX_DAILY_CALLS} API calls.")
                    break
                
                offset = 0
                while collected_count < target_count and api_calls < MAX_DAILY_CALLS:
                    # Fetch recipes
                    recipes_data, api_call_made = fetch_recipes(
                        diet, meal, offset, min_calories=min_calories, max_calories=max_calories
                    )
                    
                    # Update API call counter
                    if api_call_made:
                        api_calls += 1
                        # Implement delay between API calls
                        time.sleep(API_DELAY)
                    
                    if recipes_data == "LIMIT_REACHED":
                        break
                    
                    if not recipes_data or "results" not in recipes_data or not recipes_data["results"]:
                        print(f"No more {diet} {meal} recipes found.")
                        break
                    
                    # Process each recipe
                    for recipe in recipes_data["results"]:
                        try:
                            # Extract and save recipe data
                            recipe_data, ingredients, diet_tags = extract_recipe_data(recipe)
                            save_to_database(recipe_data, ingredients, diet_tags)
                            collected_count += 1
                            
                            # Print progress
                            if collected_count % 10 == 0:
                                print(f"Collected {collected_count} recipes")
                            
                            # Check if we've collected enough recipes
                            if collected_count >= target_count:
                                break
                        
                        except Exception as e:
                            print(f"Error processing recipe {recipe['id']}: {e}")
                            continue
                    
                    # Update offset for next batch
                    offset += MAX_BATCH_SIZE
        
        print(f"Collection complete. Total recipes: {collected_count}")
        print(f"API calls made: {api_calls}")
        return collected_count
    
    except KeyboardInterrupt:
        print("\nCollection interrupted by user.")
        return collected_count

def get_recipes(limit=100, diet_type=None, meal_type=None, cooking_status=None, min_calories=None, max_calories=None):
    """Get recipes from database with optional filtering"""
    conn = sqlite3.connect(DATABASE_FILE)
    
    # Build query with optional filters
    query = '''
    SELECT r.id, r.title as name, r.image, r.calories, r.protein, r.carbs, r.fat, r.fiber, 
           r.cooking_status, r.category, r.meal_type,
           GROUP_CONCAT(DISTINCT dt.tag) as diet_tags,
           GROUP_CONCAT(DISTINCT i.name) as ingredients
    FROM recipes r
    LEFT JOIN diet_tags dt ON r.id = dt.recipe_id
    LEFT JOIN ingredients i ON r.id = i.recipe_id
    '''
    
    # Add WHERE clause if filters are provided
    where_clauses = []
    params = []
    
    if diet_type:
        where_clauses.append("(r.category LIKE ? OR EXISTS (SELECT 1 FROM diet_tags WHERE recipe_id = r.id AND tag LIKE ?))")
        params.extend([f"%{diet_type}%", f"%{diet_type}%"])
    
    if meal_type:
        where_clauses.append("r.meal_type LIKE ?")
        params.append(f"%{meal_type}%")
    
    if cooking_status:
        where_clauses.append("r.cooking_status = ?")
        params.append(cooking_status)
    
    if min_calories is not None:
        where_clauses.append("r.calories >= ?")
        params.append(min_calories)
    
    if max_calories is not None:
        where_clauses.append("r.calories <= ?")
        params.append(max_calories)
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    # Group by and limit
    query += " GROUP BY r.id LIMIT ?"
    params.append(limit)
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        print(f"Error querying database: {e}")
        conn.close()
        return pd.DataFrame()

def search_recipes(query, limit=20, min_calories=None, max_calories=None):
    """Search recipes by name or ingredients"""
    if not query:
        return get_recipes(limit=limit, min_calories=min_calories, max_calories=max_calories)
    
    conn = sqlite3.connect(DATABASE_FILE)
    
    search_query = '''
    SELECT r.id, r.title as name, r.image, r.calories, r.protein, r.carbs, r.fat, r.fiber, 
           r.cooking_status, r.category, r.meal_type,
           GROUP_CONCAT(DISTINCT dt.tag) as diet_tags,
           GROUP_CONCAT(DISTINCT i.name) as ingredients
    FROM recipes r
    LEFT JOIN diet_tags dt ON r.id = dt.recipe_id
    LEFT JOIN ingredients i ON r.id = i.recipe_id
    WHERE (r.title LIKE ? OR EXISTS (SELECT 1 FROM ingredients WHERE recipe_id = r.id AND name LIKE ?))
    '''
    
    params = [f"%{query}%", f"%{query}%"]
    
    # Add calorie filters if provided
    if min_calories is not None:
        search_query += " AND r.calories >= ?"
        params.append(min_calories)
    
    if max_calories is not None:
        search_query += " AND r.calories <= ?"
        params.append(max_calories)
    
    search_query += " GROUP BY r.id LIMIT ?"
    params.append(limit)
    
    try:
        df = pd.read_sql_query(search_query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        print(f"Error searching database: {e}")
        conn.close()
        return pd.DataFrame()

def count_recipes():
    """Count the number of recipes in the database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM recipes")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

def get_recipe_by_id(recipe_id):
    """Get a specific recipe by ID with all details"""
    conn = sqlite3.connect(DATABASE_FILE)
    
    # Get recipe details
    recipe_query = '''
    SELECT r.id, r.title as name, r.image, r.source_url, r.ready_in_minutes, r.servings,
           r.calories, r.protein, r.carbs, r.fat, r.fiber, r.summary,
           r.cooking_status, r.category, r.meal_type
    FROM recipes r
    WHERE r.id = ?
    '''
    
    # Get ingredients
    ingredients_query = '''
    SELECT name, amount, unit
    FROM ingredients
    WHERE recipe_id = ?
    '''
    
    # Get diet tags
    tags_query = '''
    SELECT tag
    FROM diet_tags
    WHERE recipe_id = ?
    '''
    
    try:
        recipe_df = pd.read_sql_query(recipe_query, conn, params=[recipe_id])
        
        if recipe_df.empty:
            conn.close()
            return None
        
        ingredients_df = pd.read_sql_query(ingredients_query, conn, params=[recipe_id])
        tags_df = pd.read_sql_query(tags_query, conn, params=[recipe_id])
        
        # Convert to dictionary
        recipe = recipe_df.iloc[0].to_dict()
        recipe['ingredients'] = ingredients_df.to_dict('records')
        recipe['diet_tags'] = tags_df['tag'].tolist() if not tags_df.empty else []
        
        conn.close()
        return recipe
    except Exception as e:
        print(f"Error getting recipe {recipe_id}: {e}")
        conn.close()
        return None

def export_to_csv(filename="recipes_export.csv"):
    """Export database to CSV for backup or analysis"""
    conn = sqlite3.connect(DATABASE_FILE)
    
    query = '''
    SELECT r.id, r.title, r.image, r.source_url, r.ready_in_minutes, r.servings,
           r.calories, r.protein, r.carbs, r.fat, r.fiber,
           r.cooking_status, r.category, r.meal_type,
           GROUP_CONCAT(DISTINCT dt.tag) as diet_tags,
           GROUP_CONCAT(DISTINCT i.name || ' (' || i.amount || ' ' || i.unit || ')') as ingredients
    FROM recipes r
    LEFT JOIN diet_tags dt ON r.id = dt.recipe_id
    LEFT JOIN ingredients i ON r.id = i.recipe_id
    GROUP BY r.id
    '''
    
    try:
        df = pd.read_sql_query(query, conn)
        df.to_csv(filename, index=False)
        print(f"Exported {len(df)} recipes to {filename}")
        conn.close()
        return True
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        conn.close()
        return False

def initialize_database(min_recipes=50):
    """Initialize database with recipes if it's empty or has fewer than min_recipes"""
    # Create database if it doesn't exist
    if not os.path.exists(DATABASE_FILE):
        create_database()
    
    # Check if we have enough recipes
    recipe_count = count_recipes()
    print(f"Database contains {recipe_count} recipes")
    
    if recipe_count < min_recipes:
        print(f"Collecting more recipes to reach minimum of {min_recipes}...")
        collect_recipes(target_count=min_recipes)
    
    return count_recipes()

def load_sample_recipes():
    """Load sample recipes when database is not available or empty"""
    # Create sample data with the same structure as your database
    sample_data = [
        {
            "id": 1,
            "name": "Greek Yogurt Parfait with Berries",
            "calories": 320,
            "protein": 18,
            "carbs": 42,
            "fat": 8,
            "fiber": 5,
            "ingredients": "Greek yogurt, mixed berries, honey, granola",
            "cooking_status": "uncooked",
            "category": "vegetarian",
            "diet_tags": "vegetarian,gluten-free,high-protein",
            "meal_type": "breakfast",
            "image": "https://spoonacular.com/recipeImages/715497-312x231.jpg"
        },
        {
            "id": 2,
            "name": "Grilled Chicken Salad with Avocado",
            "calories": 450,
            "protein": 35,
            "carbs": 12,
            "fat": 28,
            "fiber": 8,
            "ingredients": "Chicken breast, mixed greens, avocado, cherry tomatoes, olive oil, lemon juice",
            "cooking_status": "cooked",
            "category": "gluten-free",
            "diet_tags": "gluten-free,dairy-free,high-protein,low-carb",
            "meal_type": "lunch",
            "image": "https://spoonacular.com/recipeImages/642585-312x231.jpg"
        },
        {
            "id": 3,
            "name": "Salmon with Roasted Vegetables",
            "calories": 520,
            "protein": 40,
            "carbs": 18,
            "fat": 30,
            "fiber": 6,
            "ingredients": "Salmon fillet, broccoli, carrots, bell peppers, olive oil, garlic, lemon",
            "cooking_status": "cooked",
            "category": "pescatarian",
            "diet_tags": "pescatarian,gluten-free,dairy-free,high-protein",
            "meal_type": "dinner",
            "image": "https://spoonacular.com/recipeImages/659135-312x231.jpg"
        },
        {
            "id": 4,
            "name": "Keto Cauliflower Crust Pizza",
            "calories": 480,
            "protein": 25,
            "carbs": 10,
            "fat": 38,
            "fiber": 4,
            "ingredients": "Cauliflower, mozzarella cheese, eggs, tomato sauce, pepperoni, bell peppers, olives",
            "cooking_status": "cooked",
            "category": "keto",
            "diet_tags": "keto,gluten-free,low-carb",
            "meal_type": "dinner",
            "image": "https://spoonacular.com/recipeImages/655235-312x231.jpg"
        },
        {
            "id": 5,
            "name": "Vegan Buddha Bowl",
            "calories": 420,
            "protein": 15,
            "carbs": 60,
            "fat": 16,
            "fiber": 12,
            "ingredients": "Quinoa, chickpeas, avocado, sweet potato, kale, tahini, lemon juice, garlic",
            "cooking_status": "cooked",
            "category": "vegan",
            "diet_tags": "vegan,vegetarian,gluten-free,dairy-free,high-fiber",
            "meal_type": "lunch",
            "image": "https://spoonacular.com/recipeImages/716627-312x231.jpg"
        },
        {
            "id": 6,
            "name": "Paleo Beef and Vegetable Stir Fry",
            "calories": 490,
            "protein": 32,
            "carbs": 20,
            "fat": 30,
            "fiber": 6,
            "ingredients": "Grass-fed beef strips, broccoli, carrots, bell peppers, coconut aminos, ginger, garlic",
            "cooking_status": "cooked",
            "category": "paleo",
            "diet_tags": "paleo,gluten-free,dairy-free,high-protein",
            "meal_type": "dinner",
            "image": "https://spoonacular.com/recipeImages/633942-312x231.jpg"
        },
        {
            "id": 7,
            "name": "Overnight Oats with Chia Seeds",
            "calories": 350,
            "protein": 12,
            "carbs": 45,
            "fat": 14,
            "fiber": 9,
            "ingredients": "Rolled oats, chia seeds, almond milk, maple syrup, cinnamon, berries, nuts",
            "cooking_status": "uncooked",
            "category": "vegetarian",
            "diet_tags": "vegetarian,high-fiber",
            "meal_type": "breakfast",
            "image": "https://spoonacular.com/recipeImages/658509-312x231.jpg"
        },
        {
            "id": 8,
            "name": "Mediterranean Chickpea Salad",
            "calories": 380,
            "protein": 15,
            "carbs": 40,
            "fat": 18,
            "fiber": 11,
            "ingredients": "Chickpeas, cucumber, cherry tomatoes, red onion, feta cheese, olive oil, lemon juice, herbs",
            "cooking_status": "uncooked",
            "category": "vegetarian",
            "diet_tags": "vegetarian,high-fiber",
            "meal_type": "lunch",
            "image": "https://spoonacular.com/recipeImages/716195-312x231.jpg"
        },
        {
            "id": 9,
            "name": "Turkey and Vegetable Stuffed Bell Peppers",
            "calories": 410,
            "protein": 30,
            "carbs": 25,
            "fat": 22,
            "fiber": 5,
            "ingredients": "Bell peppers, ground turkey, onion, garlic, zucchini, tomatoes, spices, cheese",
            "cooking_status": "cooked",
            "category": "gluten-free",
            "diet_tags": "gluten-free,high-protein",
            "meal_type": "dinner",
            "image": "https://spoonacular.com/recipeImages/664090-312x231.jpg"
        },
        {
            "id": 10,
            "name": "Whole30 Chicken and Sweet Potato Hash",
            "calories": 440,
            "protein": 28,
            "carbs": 35,
            "fat": 22,
            "fiber": 6,
            "ingredients": "Chicken breast, sweet potatoes, bell peppers, onion, eggs, avocado, spices",
            "cooking_status": "cooked",
            "category": "whole30",
            "diet_tags": "whole30,paleo,gluten-free,dairy-free",
            "meal_type": "breakfast",
            "image": "https://spoonacular.com/recipeImages/715523-312x231.jpg"
        }
    ]
    
    return pd.DataFrame(sample_data)

# Main function to initialize the database
if __name__ == "__main__":
    # Check if API key is available
    if not SPOONACULAR_API_KEY:
        print("Warning: Spoonacular API key not found in environment variables.")
        print("Please set your API key using set_spoonacular_api_key() function or as an environment variable.")
        print("Using sample recipes instead.")
    else:
        # Initialize database with at least 50 recipes
        initialize_database(min_recipes=50)
        
        # Export to CSV for backup
        export_to_csv()
