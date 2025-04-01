# app/rules.py
class FoodRule:
    def __init__(self):
        self.facts = {}
    
    def filter_foods(self, foods, user_preferences):
        """Filter foods based on user preferences and dietary restrictions"""
        filtered_foods = []
        
        diet_type = user_preferences.get('diet_type')
        allergies = user_preferences.get('allergies', [])
        target_calories = user_preferences.get('calories', 2000)
        
        # Remove "None" from allergies if present
        if "None" in allergies:
            allergies.remove("None")
        
        for food in foods:
            # Skip if diet doesn't match
            diet_tags = food['diet_tags'].lower().split(',')
            
            if diet_type == 'Vegetarian' and 'vegetarian' not in diet_tags:
                continue
            if diet_type == 'Vegan' and 'vegan' not in diet_tags:
                continue
            if diet_type == 'Keto' and 'keto' not in diet_tags:
                continue
            if diet_type == 'Gluten-free' and 'gluten-free' not in diet_tags:
                # Skip if diet is gluten-free but food is not tagged as such
                continue
            
            # Skip foods with allergens
            # This is simplified - would need ingredient lists to properly check
            allergen_found = False
            for allergen in allergies:
                # Check if allergen appears in the food name or diet tags
                if allergen.lower() in food['name'].lower() or allergen.lower() in food['diet_tags'].lower():
                    allergen_found = True
                    break
            
            if allergen_found:
                continue
            
            # Filter by calories (allow ±200 calories from target)
            if abs(food['calories'] - target_calories) > 200:
                continue
                
            filtered_foods.append(food)
        
        return filtered_foods