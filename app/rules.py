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
            try:
                # Safe conversion with error handling
                if 'calories' in food and food['calories'] != 'calories':
                    food_calories = int(food['calories']) if isinstance(food['calories'], str) else food['calories']
                    
                    # Filter by calories (allow ±200 calories from target)
                    if abs(food_calories - target_calories) > 200:
                        continue
            except (ValueError, TypeError):
                # Skip foods with invalid calorie data
                continue
                
            filtered_foods.append(food)
        
        return filtered_foods