class FoodRule:
    def __init__(self):
        self.facts = {}
    
    def filter_foods(self, foods, user_preferences):
        """Filter foods based on user preferences and dietary restrictions"""
        filtered_foods = []
        
        diet_type = user_preferences.get('diet_type')
        allergies = user_preferences.get('allergies', [])
        target_calories = user_preferences.get('calories', 2000)
        cooking_preference = user_preferences.get('cooking_preference', 'Any')
        
        # Remove "None" from allergies if present
        if "None" in allergies:
            allergies.remove("None")
        
        for food in foods:
            try:
                # Skip if diet doesn't match (except when "No restrictions" is selected)
                if diet_type != "No restrictions":
                    # Check category first (new column)
                    if 'category' in food and food['category']:
                        category = str(food['category']).lower()
                        
                        # Check if diet type matches with category
                        if diet_type == 'Vegetarian' and 'vegetarian' not in category:
                            continue
                        if diet_type == 'Vegan' and 'vegan' not in category:
                            continue
                        if diet_type == 'Keto' and 'keto' not in category and 'ketogenic' not in category:
                            continue
                        if diet_type == 'Gluten-free' and 'gluten' not in category:
                            continue
                        if diet_type == 'Paleo' and 'paleo' not in category:
                            continue
                        if diet_type == 'Whole30' and 'whole30' not in category:
                            continue
                        if diet_type == 'Pescatarian' and 'pescatarian' not in category:
                            continue
                        if diet_type == 'Dairy-free' and 'dairy' not in category:
                            continue
                    # Fallback to diet_tags if category is not available
                    elif 'diet_tags' in food and food['diet_tags']:
                        diet_tags = str(food['diet_tags']).lower()
                        
                        # Check if diet type matches with diet_tags
                        if diet_type == 'Vegetarian' and 'vegetarian' not in diet_tags:
                            continue
                        if diet_type == 'Vegan' and 'vegan' not in diet_tags:
                            continue
                        if diet_type == 'Keto' and 'keto' not in diet_tags and 'ketogenic' not in diet_tags:
                            continue
                        if diet_type == 'Gluten-free' and 'gluten-free' not in diet_tags and 'gluten free' not in diet_tags:
                            continue
                        if diet_type == 'Paleo' and 'paleo' not in diet_tags:
                            continue
                        if diet_type == 'Whole30' and 'whole30' not in diet_tags:
                            continue
                        if diet_type == 'Pescatarian' and 'pescatarian' not in diet_tags:
                            continue
                        if diet_type == 'Dairy-free' and 'dairy-free' not in diet_tags and 'dairy free' not in diet_tags:
                            continue
                    else:
                        # If neither category nor diet_tags are available, skip this food
                        continue
                
                # Check cooking preference
                if cooking_preference != "Any" and 'cooking_status' in food and food['cooking_status']:
                    cooking_status = str(food['cooking_status']).lower()
                    
                    if cooking_preference == "Cooked meals" and ('uncooked' in cooking_status or 'likely_uncooked' in cooking_status):
                        continue
                    
                    if cooking_preference == "No-cook/quick meals" and 'cooked' in cooking_status:
                        continue
                
                # Check for allergens in ingredients or name
                if allergies:
                    allergen_found = False
                    
                    # Check ingredients if available
                    ingredients_text = ""
                    if 'ingredients' in food and food['ingredients']:
                        ingredients_text = str(food['ingredients']).lower()
                    
                    # Check food name as fallback
                    food_name = str(food['name']).lower()
                    
                    for allergen in allergies:
                        allergen_lower = allergen.lower()
                        
                        # Skip if allergen is found in ingredients or name
                        if (allergen_lower in ingredients_text or 
                            allergen_lower in food_name or 
                            allergen_lower in str(food.get('diet_tags', '')).lower() or
                            allergen_lower in str(food.get('category', '')).lower()):
                            allergen_found = True
                            break
                    
                    if allergen_found:
                        continue
                
                # Safe conversion with error handling for calories
                food_calories = 0
                if 'calories' in food and food['calories'] != 'calories':
                    food_calories = float(food['calories']) if isinstance(food['calories'], str) else food['calories']
                    
                    # Filter by calories (allow ±300 calories from target for more flexibility)
                    if abs(food_calories - target_calories) > 300:
                        continue
                        
                filtered_foods.append(food)
                
            except (ValueError, TypeError, KeyError) as e:
                # Skip foods with data issues
                continue
                
        return filtered_foods
