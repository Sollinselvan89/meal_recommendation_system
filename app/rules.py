class FoodRule:
    def __init__(self):
        self.facts = {}
    
    def filter_foods(self, foods, user_preferences):
        """Basic filtering based on diet type and allergies"""
        filtered_foods = []
        
        for food in foods:
            # Skip if diet doesn't match
            if user_preferences.get('diet_type') == 'Vegetarian' and 'vegetarian' not in food['diet_tags']:
                continue
            if user_preferences.get('diet_type') == 'Vegan' and 'vegan' not in food['diet_tags']:
                continue
            # Add more diet filters as needed
            
            # Skip foods with allergens (would need actual allergen data)
            # if user_preferences.get('allergies') contains allergens in food
            
            filtered_foods.append(food)
        
        return filtered_foods
