import pandas as pd
import numpy as np

class FoodRule:
    def __init__(self, rule_type, condition, priority=1):
        self.rule_type = rule_type
        self.condition = condition
        self.priority = priority  # Higher number = higher priority

    def apply(self, recipe):
        """Apply rule to a recipe (works with both dict and pandas Series)"""
        # Helper function to safely get a value from either dict or pandas Series
        def get_value(obj, key, default=None):
            if hasattr(obj, 'get') and callable(obj.get):  # Dictionary-like
                return obj.get(key, default)
            elif hasattr(obj, key):  # Pandas Series attribute
                val = getattr(obj, key)
                return val if not pd.isna(val) else default
            elif isinstance(obj, dict) and key in obj:  # Dictionary
                return obj[key]
            elif hasattr(obj, '__getitem__') and key in obj:  # Series with string index
                val = obj[key]
                return val if not pd.isna(val) else default
            else:
                return default
        
        # Check rule type and apply appropriate condition
        if self.rule_type == "exclude_ingredient":
            ingredients = get_value(recipe, "ingredients", "")
            if isinstance(ingredients, str):
                return self.condition.lower() not in ingredients.lower()
            return True  # If no ingredients, rule passes
            
        elif self.rule_type == "require_diet":
            # Check in both diet_tags and category
            diet_tags = get_value(recipe, "diet_tags", "")
            category = get_value(recipe, "category", "")
            
            if isinstance(diet_tags, str) and isinstance(category, str):
                return (self.condition.lower() in diet_tags.lower() or 
                        self.condition.lower() in category.lower())
            elif isinstance(diet_tags, str):
                return self.condition.lower() in diet_tags.lower()
            elif isinstance(category, str):
                return self.condition.lower() in category.lower()
            return False
            
        elif self.rule_type == "max_calories":
            calories = get_value(recipe, "calories", 0)
            try:
                return float(calories) <= float(self.condition)
            except (ValueError, TypeError):
                return False
                
        elif self.rule_type == "min_protein":
            protein = get_value(recipe, "protein", 0)
            try:
                return float(protein) >= float(self.condition)
            except (ValueError, TypeError):
                return False
                
        elif self.rule_type == "cooking_preference":
            cooking_status = get_value(recipe, "cooking_status", "")
            if self.condition == "cooked":
                return cooking_status == "cooked"
            elif self.condition == "no-cook":
                return cooking_status == "uncooked"
            else:
                return True
                
        elif self.rule_type == "calorie_range":
            calories = get_value(recipe, "calories", 0)
            try:
                min_cal, max_cal = self.condition
                return float(min_cal) <= float(calories) <= float(max_cal)
            except (ValueError, TypeError):
                return False
                
        elif self.rule_type == "macro_ratio":
            protein = get_value(recipe, "protein", 0)
            carbs = get_value(recipe, "carbs", 0)
            fat = get_value(recipe, "fat", 0)
            
            try:
                target_ratio = self.condition  # e.g., {"protein": 0.3, "carbs": 0.4, "fat": 0.3}
                total_calories = float(protein) * 4 + float(carbs) * 4 + float(fat) * 9
                
                if total_calories == 0:
                    return False
                    
                actual_ratio = {
                    "protein": (float(protein) * 4) / total_calories,
                    "carbs": (float(carbs) * 4) / total_calories,
                    "fat": (float(fat) * 9) / total_calories
                }
                
                # Check if actual ratio is within 10% of target ratio
                for macro, target in target_ratio.items():
                    actual = actual_ratio.get(macro, 0)
                    if abs(actual - target) > 0.1:
                        return False
                return True
            except (ValueError, TypeError):
                return False
                
        return True  # Default: rule passes if not recognized

# Expert system rules for calorie distribution
def get_calorie_distribution_rules(total_calories):
    """Get calorie distribution rules based on total daily calories"""
    if total_calories < 1800:  # Low calorie
        return {
            "breakfast": {"min": total_calories * 0.2, "max": total_calories * 0.25},
            "lunch": {"min": total_calories * 0.3, "max": total_calories * 0.35},
            "dinner": {"min": total_calories * 0.3, "max": total_calories * 0.35},
            "snack": {"min": total_calories * 0.1, "max": total_calories * 0.15}
        }
    elif total_calories < 2400:  # Medium calorie
        return {
            "breakfast": {"min": total_calories * 0.25, "max": total_calories * 0.3},
            "lunch": {"min": total_calories * 0.3, "max": total_calories * 0.35},
            "dinner": {"min": total_calories * 0.3, "max": total_calories * 0.35},
            "snack": {"min": total_calories * 0.05, "max": total_calories * 0.1}
        }
    else:  # High calorie
        return {
            "breakfast": {"min": total_calories * 0.25, "max": total_calories * 0.3},
            "lunch": {"min": total_calories * 0.3, "max": total_calories * 0.35},
            "dinner": {"min": total_calories * 0.3, "max": total_calories * 0.35},
            "snack": {"min": total_calories * 0.05, "max": total_calories * 0.1}
        }

# Expert system rules for macronutrient distribution based on goals
def get_macro_distribution_rules(goal):
    """Get macronutrient distribution rules based on goal"""
    goal = goal.lower() if goal else ""
    
    if "weight loss" in goal or "lose weight" in goal or "fat loss" in goal:
        return {
            "protein": {"min": 0.3, "max": 0.4},
            "carbs": {"min": 0.2, "max": 0.3},
            "fat": {"min": 0.3, "max": 0.4}
        }
    elif "muscle" in goal or "strength" in goal or "gain" in goal:
        return {
            "protein": {"min": 0.3, "max": 0.4},
            "carbs": {"min": 0.4, "max": 0.5},
            "fat": {"min": 0.2, "max": 0.3}
        }
    elif "heart" in goal or "cardio" in goal or "cholesterol" in goal:
        return {
            "protein": {"min": 0.25, "max": 0.35},
            "carbs": {"min": 0.45, "max": 0.55},
            "fat": {"min": 0.2, "max": 0.3}
        }
    else:  # Default/maintenance
        return {
            "protein": {"min": 0.25, "max": 0.35},
            "carbs": {"min": 0.4, "max": 0.5},
            "fat": {"min": 0.25, "max": 0.35}
        }

def create_rules_from_preferences(preferences):
    """Create food rules based on user preferences using expert system approach"""
    rules = []
    
    # Diet type rule (high priority)
    if preferences["diet_type"] != "No restrictions":
        rules.append(FoodRule("require_diet", preferences["diet_type"].lower(), priority=5))
    
    # Allergies rules (highest priority - safety)
    for allergy in preferences["allergies"]:
        rules.append(FoodRule("exclude_ingredient", allergy.lower(), priority=10))
    
    # Cooking preference rule
    if preferences["cooking_preference"] == "Cooked meals":
        rules.append(FoodRule("cooking_preference", "cooked", priority=3))
    elif preferences["cooking_preference"] == "No-cook/quick meals":
        rules.append(FoodRule("cooking_preference", "no-cook", priority=3))
    
    # Calorie rules based on expert system
    calorie_rules = get_calorie_distribution_rules(preferences["calories"])
    
    # Add calorie range rules for each meal type
    for meal_type, range_data in calorie_rules.items():
        rules.append(FoodRule("calorie_range", (range_data["min"], range_data["max"]), priority=4))
    
    # Macronutrient rules based on goal
    if preferences.get("goal"):
        macro_rules = get_macro_distribution_rules(preferences["goal"])
        target_ratio = {
            "protein": (macro_rules["protein"]["min"] + macro_rules["protein"]["max"]) / 2,
            "carbs": (macro_rules["carbs"]["min"] + macro_rules["carbs"]["max"]) / 2,
            "fat": (macro_rules["fat"]["min"] + macro_rules["fat"]["max"]) / 2
        }
        rules.append(FoodRule("macro_ratio", target_ratio, priority=2))
    
    # Sort rules by priority (highest first)
    rules.sort(key=lambda x: x.priority, reverse=True)
    
    return rules

def filter_recipes_with_rules(recipes, rules):
    """Filter recipes based on rules with expert system approach"""
    import pandas as pd
    
    # First apply high-priority rules (allergies, diet type)
    high_priority_rules = [rule for rule in rules if rule.priority >= 5]
    medium_priority_rules = [rule for rule in rules if 2 < rule.priority < 5]
    low_priority_rules = [rule for rule in rules if rule.priority <= 2]
    
    filtered_recipes = []
    
    # Handle both DataFrame and list of dictionaries
    if isinstance(recipes, pd.DataFrame):
        # First pass: Apply high-priority rules (must pass all)
        for _, recipe in recipes.iterrows():
            valid = True
            for rule in high_priority_rules:
                if not rule.apply(recipe):
                    valid = False
                    break
            if valid:
                filtered_recipes.append(recipe.to_dict())
        
        # If we have too few recipes after high-priority filtering, skip medium priority
        if len(filtered_recipes) < 5:
            print(f"Warning: Only {len(filtered_recipes)} recipes match high-priority criteria. Relaxing constraints.")
        else:
            # Second pass: Apply medium-priority rules
            filtered_recipes_medium = []
            for recipe in filtered_recipes:
                valid = True
                for rule in medium_priority_rules:
                    if not rule.apply(recipe):
                        valid = False
                        break
                if valid:
                    filtered_recipes_medium.append(recipe)
            
            # If we have enough recipes after medium-priority filtering, use those
            if len(filtered_recipes_medium) >= 3:
                filtered_recipes = filtered_recipes_medium
    else:
        # Same logic for list of dictionaries
        for recipe in recipes:
            valid = True
            for rule in high_priority_rules:
                if not rule.apply(recipe):
                    valid = False
                    break
            if valid:
                filtered_recipes.append(recipe)
        
        # If we have too few recipes after high-priority filtering, skip medium priority
        if len(filtered_recipes) < 5:
            print(f"Warning: Only {len(filtered_recipes)} recipes match high-priority criteria. Relaxing constraints.")
        else:
            # Second pass: Apply medium-priority rules
            filtered_recipes_medium = []
            for recipe in filtered_recipes:
                valid = True
                for rule in medium_priority_rules:
                    if not rule.apply(recipe):
                        valid = False
                        break
                if valid:
                    filtered_recipes_medium.append(recipe)
            
            # If we have enough recipes after medium-priority filtering, use those
            if len(filtered_recipes_medium) >= 3:
                filtered_recipes = filtered_recipes_medium
    
    # Apply low-priority rules as a scoring mechanism
    # This doesn't filter out recipes but ranks them by how many rules they satisfy
    scored_recipes = []
    for recipe in filtered_recipes:
        score = 0
        for rule in low_priority_rules:
            if rule.apply(recipe):
                score += 1
        
        # Add score to recipe
        recipe_copy = recipe.copy() if hasattr(recipe, 'copy') else recipe
        if isinstance(recipe_copy, dict):
            recipe_copy['expert_score'] = score
        else:
            recipe_copy.expert_score = score
        
        scored_recipes.append(recipe_copy)
    
    # Sort by score (highest first)
    scored_recipes.sort(key=lambda x: x.get('expert_score', 0) if isinstance(x, dict) else getattr(x, 'expert_score', 0), reverse=True)
    
    return scored_recipes

def filter_recipes(recipes, preferences):
    """Filter recipes based on user preferences"""
    rules = create_rules_from_preferences(preferences)
    return filter_recipes_with_rules(recipes, rules)
