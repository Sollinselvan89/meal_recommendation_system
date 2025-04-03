import sqlite3
import json
import os
from pathlib import Path

def determine_cooking_status(recipe_data):
    """Determine if a recipe requires cooking or not based on available data"""
    ready_in_minutes = recipe_data.get("ready_in_minutes", 0)
    
    # Handle None values safely
    title = ""
    if recipe_data.get("title") is not None:
        title = recipe_data.get("title", "").lower()
    
    summary = ""
    if recipe_data.get("summary") is not None:
        summary = recipe_data.get("summary", "").lower()
    
    # Check title and summary for keywords suggesting no cooking
    no_cook_keywords = ["raw", "no-cook", "no cook", "uncooked", "salad", 
                        "smoothie", "shake", "overnight", "yogurt", 
                        "sandwich", "wrap", "dip", "juice"]
    
    for keyword in no_cook_keywords:
        if keyword in title or keyword in summary:
            return "uncooked"
    
    # Check ready time - very short times may indicate no cooking
    if ready_in_minutes < 10:
        return "likely_uncooked"
    
    # Check if cooking words are in the title or summary
    cook_keywords = ["bake", "roast", "broil", "grill", "sauté", "saute", 
                    "fry", "boil", "simmer", "steam", "cook", "heat"]
    
    for keyword in cook_keywords:
        if keyword in title or keyword in summary:
            return "cooked"
            
    # Default to cooked if we can't determine otherwise
    return "cooked"

def extract_categories_from_tags(diet_tags):
    """Extract relevant categories from diet tags"""
    # Define mapping from diet tags to categories
    category_mappings = {
        "vegan": "vegan",
        "vegetarian": "vegetarian",
        "gluten free": "gluten free",
        "dairy free": "dairy free",
        "pescatarian": "pescatarian",
        "ketogenic": "ketogenic",
        "keto": "ketogenic",
        "paleo": "paleo",
        "whole30": "whole30"
    }
    
    # List of the eight main categories we're tracking
    main_categories = ["vegetarian", "vegan", "gluten free", "ketogenic", 
                      "paleo", "whole30", "pescatarian", "dairy free"]
    
    # Extract categories from diet tags
    categories = set()
    if diet_tags:
        diet_tags_list = diet_tags.split(',')
        for tag in diet_tags_list:
            tag = tag.strip().lower()
            if tag in category_mappings:
                categories.add(category_mappings[tag])
    
    # Sort categories to ensure consistent ordering, prioritizing main categories
    sorted_categories = []
    for category in main_categories:
        if category in categories:
            sorted_categories.append(category)
    
    # Add any remaining categories not in the main list
    for category in sorted(categories):
        if category not in main_categories and category not in sorted_categories:
            sorted_categories.append(category)
    
    return sorted_categories

def update_database():
    """Update existing database rows with missing cooking status and category information"""
    db_path = 'meal_recipes.db'
    
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} not found.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, ensure the columns exist
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
    
    # Get all recipes that have empty cooking_status or category
    cursor.execute("""
    SELECT r.id, r.title, r.ready_in_minutes, r.summary, 
           GROUP_CONCAT(dt.tag) as diet_tags,
           r.cooking_status, r.category
    FROM recipes r
    LEFT JOIN diet_tags dt ON r.id = dt.recipe_id
    GROUP BY r.id
    """)
    
    recipes = cursor.fetchall()
    updated_count = 0
    
    for recipe in recipes:
        recipe_id, title, ready_in_minutes, summary, diet_tags, cooking_status, category = recipe
        
        # Check if we need to update cooking_status
        need_cooking_update = cooking_status is None or cooking_status == ''
        
        # Check if we need to update category
        need_category_update = category is None or category == ''
        
        if need_cooking_update or need_category_update:
            # Create recipe data dictionary
            recipe_data = {
                "id": recipe_id,
                "title": title,
                "ready_in_minutes": ready_in_minutes,
                "summary": summary
            }
            
            # Determine cooking status if needed
            if need_cooking_update:
                new_cooking_status = determine_cooking_status(recipe_data)
            else:
                new_cooking_status = cooking_status
            
            # Extract categories if needed
            if need_category_update:
                categories = extract_categories_from_tags(diet_tags)
                new_category = ','.join(categories)
            else:
                new_category = category
            
            # Update the database
            cursor.execute("""
            UPDATE recipes
            SET cooking_status = ?, category = ?
            WHERE id = ?
            """, (new_cooking_status, new_category, recipe_id))
            
            updated_count += 1
            
            # Print progress periodically
            if updated_count % 20 == 0:
                print(f"Updated {updated_count} recipes...")
                conn.commit()
    
    # Final commit
    conn.commit()
    print(f"Update complete. Updated {updated_count} recipes in total.")
    
    # Generate statistics
    cursor.execute("""
    SELECT cooking_status, COUNT(*) as count
    FROM recipes
    GROUP BY cooking_status
    ORDER BY count DESC
    """)
    cooking_stats = cursor.fetchall()
    
    print("\nCooking Status Distribution:")
    for status, count in cooking_stats:
        status_display = status if status else "None"
        print(f"  {status_display}: {count}")
    
    cursor.execute("""
    SELECT category, COUNT(*) as count
    FROM recipes
    GROUP BY category
    ORDER BY count DESC
    LIMIT 10
    """)
    category_stats = cursor.fetchall()
    
    print("\nTop 10 Category Distribution:")
    for cat, count in category_stats:
        cat_display = cat if cat else "None"
        print(f"  {cat_display}: {count}")
    
    # Print counts for each main category
    main_categories = ["vegetarian", "vegan", "gluten free", "ketogenic", 
                      "paleo", "whole30", "pescatarian", "dairy free"]
    
    print("\nMain Category Distribution:")
    for main_cat in main_categories:
        cursor.execute("""
        SELECT COUNT(*) as count
        FROM recipes
        WHERE category LIKE ?
        """, (f"%{main_cat}%",))
        
        count = cursor.fetchone()[0]
        print(f"  {main_cat}: {count}")
    
    conn.close()

if __name__ == "__main__":
    print("Starting update of existing recipe data...")
    update_database()
    print("Done.")
