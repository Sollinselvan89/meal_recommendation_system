import requests
import time
import os
import json
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from langchain.docstore.document import Document

load_dotenv()

# Get Spoonacular API key from environment
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# Function to set Spoonacular API key (called from Streamlit app)
def set_spoonacular_api_key(key):
    global SPOONACULAR_API_KEY
    SPOONACULAR_API_KEY = key
    os.environ["SPOONACULAR_API_KEY"] = key

# Constants for API optimization
CACHE_DIR = "cache"
PROGRESS_FILE = "collection_progress.json"
MAX_BATCH_SIZE = 100  # Maximum recipes per API call
API_DELAY = 2  # Seconds between API calls
MAX_DAILY_CALLS = 150  # Free tier limit

# List of diet types to search for (renamed to CATEGORIES for clarity)
CATEGORIES = [
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

def save_progress(progress_data):
    """Save collection progress to resume later"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f)

def load_progress():
    """Load collection progress if available"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Initialize new progress tracking
    return {
        "api_calls_today": 0,
        "last_reset_date": None,
        "category_quotas": {category: 0 for category in CATEGORIES},
        "current_category_index": 0,
        "current_meal_index": 0,
        "current_offset": 0,
        "collected_ids": []
    }

def fetch_recipes(category=None, meal_type=None, offset=0, number=MAX_BATCH_SIZE):
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
    
    print(f"Fetching from API: {category} {meal_type} (offset: {offset})")
    
    try:
        response = requests.get(url, params=params)
        
        # Handle API errors
        if response.status_code == 402:
            print("Daily API limit reached. Saving progress to resume later.")
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
    # Logic to determine if recipe is cooked or uncooked
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
    
    # Extract basic recipe info
    recipe_data = {
        "id": recipe["id"],
        "title": recipe["title"],
        "image": recipe.get("image", ""),
        "source_url": recipe.get("sourceUrl", ""),
        "ready_in_minutes": recipe.get("readyInMinutes", 0),
        "servings": recipe.get("servings", 0),
        "summary": recipe.get("summary", ""),
        "calories": nutrition["calories"],
        "protein": nutrition["protein"],
        "carbs": nutrition["carbs"],
        "fat": nutrition["fat"],
        "fiber": nutrition["fiber"],
        "cooking_status": cooking_status,
        "category": ",".join(categories) if categories else ""
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

def save_to_database(recipe_data, ingredients, diet_tags, conn, cursor):
    """Save a recipe and its related data to the database"""
    # Insert recipe
    cursor.execute('''
    INSERT OR REPLACE INTO recipes 
    (id, title, image, source_url, ready_in_minutes, servings, calories, protein, carbs, fat, fiber, summary, cooking_status, category)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        recipe_data["id"], recipe_data["title"], recipe_data["image"], 
        recipe_data["source_url"], recipe_data["ready_in_minutes"], 
        recipe_data["servings"], recipe_data["calories"], recipe_data["protein"],
        recipe_data["carbs"], recipe_data["fat"], recipe_data["fiber"],
        recipe_data["summary"], recipe_data["cooking_status"], recipe_data["category"]
    ))
    
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

def create_database():
    """Create the SQLite database and tables"""
    conn = sqlite3.connect('meal_recipes.db')
    cursor = conn.cursor()
    
    # Create recipes table with new columns
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
        category TEXT
    )
    ''')
    
    # Check if columns exist and add them if they don't
    # This ensures backward compatibility with existing databases
    try:
        cursor.execute("SELECT cooking_status FROM recipes LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE recipes ADD COLUMN cooking_status TEXT")
        print("Added cooking_status column to recipes table")
        
    try:
        cursor.execute("SELECT category FROM recipes LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE recipes ADD COLUMN category TEXT")
        print("Added category column to recipes table")
    
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

def collect_recipes(target_min=20, target_max=200):
    """Collect recipes from API and store in database with equal distribution"""
    setup_directories()
    progress = load_progress()
    
    # Load progress variables
    api_calls_today = progress["api_calls_today"]
    category_quotas = progress.get("category_quotas", {category: 0 for category in CATEGORIES})
    current_category_index = progress.get("current_category_index", 0)
    current_meal_index = progress.get("current_meal_index", 0)
    current_offset = progress.get("current_offset", 0)
    collected_ids = set(progress.get("collected_ids", []))
    
    # Create database connection
    conn, cursor = create_database()
    
    try:
        print(f"Starting collection with {api_calls_today} API calls used today")
        print(f"Category collection status: {category_quotas}")
        
        # Collect recipes with distribution across categories
        while min(category_quotas.values()) < target_min or max(category_quotas.values()) < target_max:
            # Check if we've hit the API call limit for today
            if api_calls_today >= MAX_DAILY_CALLS:
                print(f"Reached daily limit of {MAX_DAILY_CALLS} API calls. Saving progress.")
                break
            
            # Select the category with the lowest count that hasn't reached the max
            sorted_categories = sorted(
                [(cat, count) for cat, count in category_quotas.items() if count < target_max],
                key=lambda x: x[1]
            )
            
            if not sorted_categories:
                print("All categories have reached their maximum target.")
                break
                
            current_category = sorted_categories[0][0]
            
            # Loop through meal types
            for meal_index in range(current_meal_index, len(MEAL_TYPES)):
                meal_type = MEAL_TYPES[meal_index]
                
                # Start from the saved offset
                offset = current_offset if meal_index == current_meal_index else 0
                
                # Check if we've hit the max target for this category
                if category_quotas[current_category] >= target_max:
                    break
                
                # Check if we've hit API call limit
                if api_calls_today >= MAX_DAILY_CALLS:
                    print(f"Reached daily limit of {MAX_DAILY_CALLS} API calls. Saving progress.")
                    current_meal_index = meal_index
                    current_offset = offset
                    break
                
                print(f"Fetching {current_category} {meal_type} recipes (offset: {offset})...")
                
                # Fetch recipes with caching
                recipes_data, api_call_made = fetch_recipes(current_category, meal_type, offset)
                
                # Update API call counter if an actual API call was made
                if api_call_made:
                    api_calls_today += 1
                    # Implement delay between API calls
                    time.sleep(API_DELAY)
                
                if recipes_data == "LIMIT_REACHED":
                    # Save progress and exit
                    current_meal_index = meal_index
                    current_offset = offset
                    break
                
                if not recipes_data or "results" not in recipes_data or not recipes_data["results"]:
                    print(f"No more {current_category} {meal_type} recipes found.")
                    continue
                
                # Process each recipe
                for recipe in recipes_data["results"]:
                    recipe_id = recipe["id"]
                    
                    # Skip if we've already collected this recipe
                    if recipe_id in collected_ids:
                        continue
                    
                    try:
                        # Extract and save recipe data
                        recipe_data, ingredients, diet_tags = extract_recipe_data(recipe)
                        save_to_database(recipe_data, ingredients, diet_tags, conn, cursor)
                        
                        # Update tracking
                        collected_ids.add(recipe_id)
                        category_quotas[current_category] += 1
                        
                        # Print progress
                        if sum(category_quotas.values()) % 20 == 0:
                            print(f"Progress: {category_quotas}")
                        
                        # Check if we've hit the max target for this category
                        if category_quotas[current_category] >= target_max:
                            print(f"Completed max quota for {current_category}: {target_max} recipes")
                            break
                    
                    except Exception as e:
                        print(f"Error processing recipe {recipe_id}: {e}")
                        continue
                
                # Update offset for next batch
                offset += MAX_BATCH_SIZE
                current_offset = offset
                
                # Save progress periodically
                if api_call_made:
                    progress["api_calls_today"] = api_calls_today
                    progress["category_quotas"] = category_quotas
                    progress["current_category_index"] = current_category_index
                    progress["current_meal_index"] = meal_index
                    progress["current_offset"] = offset
                    progress["collected_ids"] = list(collected_ids)
                    save_progress(progress)
            
            # Reset meal index when moving to next category
            current_meal_index = 0
            
            # Check if all categories have met minimum target
            if min(category_quotas.values()) >= target_min and all(count >= target_min for count in category_quotas.values()):
                print(f"All categories have met the minimum target of {target_min} recipes.")
                if all(count >= target_max for count in category_quotas.values()):
                    print(f"All categories have met the maximum target of {target_max} recipes.")
                    break
        
        # Final save
        progress["api_calls_today"] = api_calls_today
        progress["category_quotas"] = category_quotas
        progress["current_category_index"] = current_category_index
        progress["current_meal_index"] = current_meal_index
        progress["current_offset"] = current_offset
        progress["collected_ids"] = list(collected_ids)
        save_progress(progress)
        
        # Report results
        total_recipes = sum(category_quotas.values())
        print(f"Collection complete or paused. Total recipes: {total_recipes}")
        print(f"Category distribution: {category_quotas}")
        print(f"API calls made today: {api_calls_today}")
    
    except KeyboardInterrupt:
        # Handle manual interruption
        print("\nCollection interrupted by user.")
    finally:
        # Clean up
        conn.close()
        
        # Save final progress
        progress["api_calls_today"] = api_calls_today
        progress["category_quotas"] = category_quotas
        progress["current_category_index"] = current_category_index
        progress["current_meal_index"] = current_meal_index
        progress["current_offset"] = current_offset
        progress["collected_ids"] = list(collected_ids)
        save_progress(progress)

def export_to_csv():
    """Export database to CSV for use in the app"""
    conn = sqlite3.connect('meal_recipes.db')
    
    # Get recipes with their diet tags and new columns
    query = '''
    SELECT r.id, r.title, r.calories, r.protein, r.carbs, r.fat, r.fiber, 
           r.cooking_status, r.category,
           GROUP_CONCAT(DISTINCT dt.tag) as diet_tags
    FROM recipes r
    LEFT JOIN diet_tags dt ON r.id = dt.recipe_id
    GROUP BY r.id
    '''
    
    recipes_df = pd.read_sql_query(query, conn)
    
    # Get ingredients for each recipe
    ingredients_df = pd.read_sql_query('''
    SELECT recipe_id, GROUP_CONCAT(name || ' (' || amount || ' ' || unit || ')') as ingredients
    FROM ingredients
    GROUP BY recipe_id
    ''', conn)
    
    # Merge the dataframes
    merged_df = pd.merge(recipes_df, ingredients_df, left_on='id', right_on='recipe_id', how='left')
    
    # Drop unnecessary columns
    merged_df.drop('recipe_id', axis=1, inplace=True)
    
    # Save to CSV
    merged_df.to_csv('advanced_recipes.csv', index=False)
    print("Exported recipes to advanced_recipes.csv")
    
    conn.close()

def load_food_data():
    """Load recipes from the database for use in a Streamlit app"""
    # Check if database exists, otherwise fall back to CSV
    if os.path.exists('meal_recipes.db'):
        conn = sqlite3.connect('meal_recipes.db')
        
        # Get recipes with their diet tags and new columns - removing the comment from SQL
        query = '''
        SELECT r.id, r.title as name, r.calories, r.protein, r.carbs, r.fat, r.fiber, 
               r.cooking_status, r.category,
               GROUP_CONCAT(DISTINCT dt.tag) as diet_tags,
               GROUP_CONCAT(DISTINCT i.name) as ingredients
        FROM recipes r
        LEFT JOIN diet_tags dt ON r.id = dt.recipe_id
        LEFT JOIN ingredients i ON r.id = i.recipe_id
        GROUP BY r.id
        LIMIT 1000
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
    else:
        # Fall back to CSV if database doesn't exist
        csv_path = 'data/sample_foods.csv'
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        elif os.path.exists('advanced_recipes.csv'):
            df = pd.read_csv('advanced_recipes.csv')
        else:
            print("Warning: No database or CSV file found. Returning empty DataFrame.")
            return pd.DataFrame(), []
    
    documents = []
    
    for _, row in df.iterrows():
        # Create a text representation of the recipe
        content = f"Name: {row['name']}\n"
        content += f"Calories: {row['calories']}\n"
        content += f"Protein: {row['protein']}g\n"
        content += f"Carbs: {row['carbs']}g\n"
        content += f"Fat: {row['fat']}g\n"
        
        # Add fiber if available
        if 'fiber' in row and not pd.isna(row['fiber']):
            content += f"Fiber: {row['fiber']}g\n"
            
        # Add new columns if available
        if 'cooking_status' in row and not pd.isna(row['cooking_status']):
            content += f"Cooking Status: {row['cooking_status']}\n"
            
        if 'category' in row and not pd.isna(row['category']):
            content += f"Category: {row['category']}\n"
            
        content += f"Diet Tags: {row['diet_tags']}\n"
        
        # Add ingredients if available
        if 'ingredients' in row and not pd.isna(row['ingredients']):
            content += f"Ingredients: {row['ingredients']}\n"
        
        # Create document with metadata for filtering
        doc = Document(
            page_content=content,
            metadata={
                "name": row['name'],
                "calories": float(row['calories']) if isinstance(row['calories'], str) else row['calories'],
                "cooking_status": row['cooking_status'] if 'cooking_status' in row else "",
                "category": row['category'] if 'category' in row else "",
                "diet_tags": row['diet_tags'] if 'diet_tags' in row else "",
                "ingredients": row['ingredients'] if 'ingredients' in row else ""
            }
        )
        documents.append(doc)
    
    return df, documents

def calculate_api_usage(target_min=20, target_max=200):
    """Calculate how many API calls would be needed for the target collection"""
    # Calculate minimum required and maximum possible recipes
    minimum_recipes = len(CATEGORIES) * target_min
    maximum_recipes = len(CATEGORIES) * target_max
    
    # Assuming 100 recipes per API call (optimistic)
    min_estimated_calls = minimum_recipes // MAX_BATCH_SIZE
    if minimum_recipes % MAX_BATCH_SIZE > 0:
        min_estimated_calls += 1
    
    max_estimated_calls = maximum_recipes // MAX_BATCH_SIZE
    if maximum_recipes % MAX_BATCH_SIZE > 0:
        max_estimated_calls += 1
    
    # Add overhead for searches that return fewer results
    min_estimated_calls = int(min_estimated_calls * 1.5)
    max_estimated_calls = int(max_estimated_calls * 1.5)
    
    min_days_needed = min_estimated_calls // MAX_DAILY_CALLS
    if min_estimated_calls % MAX_DAILY_CALLS > 0:
        min_days_needed += 1
    
    max_days_needed = max_estimated_calls // MAX_DAILY_CALLS
    if max_estimated_calls % MAX_DAILY_CALLS > 0:
        max_days_needed += 1
    
    print(f"Estimated API calls needed: {min_estimated_calls} to {max_estimated_calls}")
    print(f"With {MAX_DAILY_CALLS} calls per day, collection will take approximately {min_days_needed} to {max_days_needed} days")
    print(f"Target: {minimum_recipes} to {maximum_recipes} recipes ({target_min} to {target_max} per category)")

if __name__ == "__main__":
    # Calculate API usage estimates
    calculate_api_usage(target_min=20, target_max=200)
    
    # Ask for confirmation before starting
    print("\nWould you like to:")
    print("1. Start/resume recipe collection")
    print("2. Export existing database to CSV")
    print("3. Exit")
    
    choice = input("Enter your choice (1-3): ")
    
    if choice == "1":
        # Use a range of 20-200 recipes per category as specified
        collect_recipes(target_min=20, target_max=200)  
    elif choice == "2":
        export_to_csv()
    else:
        print("Exiting without action")
