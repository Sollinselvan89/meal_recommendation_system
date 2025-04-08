import streamlit as st
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
import json
from datetime import datetime
import pickle
from sklearn.metrics.pairwise import cosine_similarity
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set page configuration
st.set_page_config(
    page_title="Meal Recommendation Expert System",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2E7D32;
        margin-top: 2rem;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .meal-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1B5E20;
    }
    .meal-detail {
        margin-top: 5px;
        color: #424242;
    }
    .nutrition-badge {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-right: 5px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Define the FoodRule class (simplified version of your existing code)
class FoodRule:
    def __init__(self, rule_type, condition):
        self.rule_type = rule_type
        self.condition = condition
    
    def apply(self, meal):
        if self.rule_type == "exclude_ingredient":
            return self.condition not in meal["ingredients"].lower()
        elif self.rule_type == "require_diet":
            return self.condition in meal["diet_tags"].lower()
        elif self.rule_type == "max_calories":
            return meal["calories"] <= int(self.condition)
        elif self.rule_type == "min_protein":
            return meal["protein"] >= int(self.condition)
        elif self.rule_type == "cooking_preference":
            if self.condition == "cooked":
                return meal["cooking_status"] == "cooked"
            elif self.condition == "no-cook":
                return meal["cooking_status"] == "uncooked"
            else:
                return True
        return True

# Function to generate embeddings
def generate_embedding(text):
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        st.error(f"Error generating embedding: {str(e)}")
        return None

# Function to load or create recipe database with embeddings
@st.cache_data
def load_recipe_database():
    # In a real application, this would load from a database
    # For this demo, we'll use a predefined list of recipes
    recipes = [
        {
            "id": 1,
            "name": "Greek Yogurt Parfait with Berries",
            "description": "A delicious and nutritious breakfast parfait with layers of Greek yogurt, fresh berries, honey, and granola.",
            "calories": 320,
            "protein": 18,
            "carbs": 42,
            "fat": 8,
            "ingredients": "Greek yogurt, mixed berries, honey, granola",
            "cooking_status": "uncooked",
            "cooking_time": 5,
            "diet_tags": "vegetarian,gluten-free,high-protein",
            "meal_type": "breakfast",
            "instructions": "1. Layer Greek yogurt in a glass or bowl. 2. Add a layer of mixed berries. 3. Drizzle with honey. 4. Top with granola. 5. Repeat layers if desired."
        },
        {
            "id": 2,
            "name": "Grilled Chicken Salad with Avocado",
            "description": "A protein-packed salad featuring grilled chicken breast, fresh greens, avocado, and a light vinaigrette.",
            "calories": 450,
            "protein": 35,
            "carbs": 12,
            "fat": 28,
            "ingredients": "Chicken breast, mixed greens, avocado, cherry tomatoes, olive oil, lemon juice",
            "cooking_status": "cooked",
            "cooking_time": 20,
            "diet_tags": "gluten-free,dairy-free,high-protein,low-carb",
            "meal_type": "lunch",
            "instructions": "1. Season and grill chicken breast until cooked through. 2. Slice the cooked chicken. 3. Combine mixed greens, sliced avocado, and cherry tomatoes in a bowl. 4. Top with sliced chicken. 5. Drizzle with olive oil and lemon juice."
        },
        {
            "id": 3,
            "name": "Salmon with Roasted Vegetables",
            "description": "Oven-baked salmon fillet served with a colorful medley of roasted vegetables.",
            "calories": 520,
            "protein": 40,
            "carbs": 18,
            "fat": 30,
            "ingredients": "Salmon fillet, broccoli, carrots, bell peppers, olive oil, garlic, lemon",
            "cooking_status": "cooked",
            "cooking_time": 30,
            "diet_tags": "pescatarian,gluten-free,dairy-free,high-protein",
            "meal_type": "dinner",
            "instructions": "1. Preheat oven to 400°F. 2. Season salmon with salt, pepper, and lemon. 3. Chop vegetables and toss with olive oil and garlic. 4. Place salmon and vegetables on a baking sheet. 5. Roast for 15-20 minutes until salmon is cooked through."
        },
        {
            "id": 4,
            "name": "Keto Cauliflower Crust Pizza",
            "description": "A low-carb pizza alternative with a crispy cauliflower crust topped with cheese and your favorite toppings.",
            "calories": 480,
            "protein": 25,
            "carbs": 10,
            "fat": 38,
            "ingredients": "Cauliflower, mozzarella cheese, eggs, tomato sauce, pepperoni, bell peppers, olives",
            "cooking_status": "cooked",
            "cooking_time": 45,
            "diet_tags": "keto,gluten-free,low-carb",
            "meal_type": "dinner",
            "instructions": "1. Rice cauliflower and microwave for 5 minutes. 2. Mix with egg and part of the cheese to form a crust. 3. Bake crust at 425°F for 15 minutes. 4. Add sauce and toppings. 5. Bake for another 10 minutes until cheese is melted."
        },
        {
            "id": 5,
            "name": "Vegan Buddha Bowl",
            "description": "A nourishing bowl filled with quinoa, roasted vegetables, legumes, and a flavorful tahini dressing.",
            "calories": 420,
            "protein": 15,
            "carbs": 60,
            "fat": 16,
            "ingredients": "Quinoa, chickpeas, avocado, sweet potato, kale, tahini, lemon juice, garlic",
            "cooking_status": "cooked",
            "cooking_time": 35,
            "diet_tags": "vegan,vegetarian,gluten-free,dairy-free,high-fiber",
            "meal_type": "lunch",
            "instructions": "1. Cook quinoa according to package instructions. 2. Roast sweet potatoes for 25 minutes at 400°F. 3. Massage kale with olive oil. 4. Arrange quinoa, sweet potatoes, chickpeas, kale, and avocado in a bowl. 5. Mix tahini, lemon juice, and garlic for dressing and drizzle over bowl."
        },
        {
            "id": 6,
            "name": "Paleo Beef and Vegetable Stir Fry",
            "description": "A quick and flavorful stir fry with grass-fed beef and colorful vegetables.",
            "calories": 490,
            "protein": 32,
            "carbs": 20,
            "fat": 30,
            "ingredients": "Grass-fed beef strips, broccoli, carrots, bell peppers, coconut aminos, ginger, garlic",
            "cooking_status": "cooked",
            "cooking_time": 25,
            "diet_tags": "paleo,gluten-free,dairy-free,high-protein",
            "meal_type": "dinner",
            "instructions": "1. Heat oil in a wok or large skillet. 2. Stir-fry beef until browned. 3. Remove beef and stir-fry vegetables until tender-crisp. 4. Add ginger and garlic. 5. Return beef to the pan and add coconut aminos. 6. Stir-fry for another minute and serve."
        },
        {
            "id": 7,
            "name": "Overnight Oats with Chia Seeds",
            "description": "A make-ahead breakfast with oats, chia seeds, milk, and toppings of your choice.",
            "calories": 350,
            "protein": 12,
            "carbs": 45,
            "fat": 14,
            "ingredients": "Rolled oats, chia seeds, almond milk, maple syrup, cinnamon, berries, nuts",
            "cooking_status": "uncooked",
            "cooking_time": 5,
            "diet_tags": "vegetarian,high-fiber",
            "meal_type": "breakfast",
            "instructions": "1. Combine oats, chia seeds, almond milk, maple syrup, and cinnamon in a jar. 2. Stir well and refrigerate overnight. 3. In the morning, top with fresh berries and nuts."
        },
        {
            "id": 8,
            "name": "Mediterranean Chickpea Salad",
            "description": "A refreshing salad with chickpeas, cucumber, tomatoes, feta, and a lemon-herb dressing.",
            "calories": 380,
            "protein": 15,
            "carbs": 40,
            "fat": 18,
            "ingredients": "Chickpeas, cucumber, cherry tomatoes, red onion, feta cheese, olive oil, lemon juice, herbs",
            "cooking_status": "uncooked",
            "cooking_time": 15,
            "diet_tags": "vegetarian,high-fiber",
            "meal_type": "lunch",
            "instructions": "1. Rinse and drain chickpeas. 2. Chop cucumber, tomatoes, and red onion. 3. Combine all ingredients in a bowl. 4. Mix olive oil, lemon juice, and herbs for dressing. 5. Toss salad with dressing and crumbled feta."
        },
        {
            "id": 9,
            "name": "Turkey and Vegetable Stuffed Bell Peppers",
            "description": "Bell peppers stuffed with a savory mixture of ground turkey, vegetables, and spices.",
            "calories": 410,
            "protein": 30,
            "carbs": 25,
            "fat": 22,
            "ingredients": "Bell peppers, ground turkey, onion, garlic, zucchini, tomatoes, spices, cheese",
            "cooking_status": "cooked",
            "cooking_time": 50,
            "diet_tags": "gluten-free,high-protein",
            "meal_type": "dinner",
            "instructions": "1. Preheat oven to 375°F. 2. Cut tops off peppers and remove seeds. 3. Brown turkey with onion and garlic. 4. Add chopped zucchini, tomatoes, and spices. 5. Stuff peppers with mixture and top with cheese. 6. Bake for 30-35 minutes."
        },
        {
            "id": 10,
            "name": "Whole30 Chicken and Sweet Potato Hash",
            "description": "A hearty breakfast hash with chicken, sweet potatoes, and vegetables.",
            "calories": 440,
            "protein": 28,
            "carbs": 35,
            "fat": 22,
            "ingredients": "Chicken breast, sweet potatoes, bell peppers, onion, eggs, avocado, spices",
            "cooking_status": "cooked",
            "cooking_time": 30,
            "diet_tags": "whole30,paleo,gluten-free,dairy-free",
            "meal_type": "breakfast",
            "instructions": "1. Dice sweet potatoes and cook until tender. 2. Cook diced chicken in a separate pan. 3. Add diced peppers and onion to sweet potatoes. 4. Combine chicken with vegetables. 5. Make wells in the hash and crack eggs into them. 6. Cover and cook until eggs are set. 7. Top with sliced avocado."
        },
        {
            "id": 11,
            "name": "Lentil and Vegetable Soup",
            "description": "A hearty and nutritious soup packed with lentils and vegetables.",
            "calories": 320,
            "protein": 18,
            "carbs": 45,
            "fat": 6,
            "ingredients": "Lentils, carrots, celery, onion, garlic, tomatoes, vegetable broth, spices",
            "cooking_status": "cooked",
            "cooking_time": 40,
            "diet_tags": "vegan,vegetarian,gluten-free,dairy-free,high-fiber",
            "meal_type": "lunch",
            "instructions": "1. Sauté onion, carrots, and celery. 2. Add garlic and spices. 3. Add lentils, tomatoes, and vegetable broth. 4. Simmer for 30 minutes until lentils are tender."
        },
        {
            "id": 12,
            "name": "Baked Cod with Lemon and Herbs",
            "description": "Tender baked cod fillets with a bright lemon and herb topping.",
            "calories": 280,
            "protein": 35,
            "carbs": 5,
            "fat": 12,
            "ingredients": "Cod fillets, lemon, olive oil, garlic, fresh herbs, salt, pepper",
            "cooking_status": "cooked",
            "cooking_time": 25,
            "diet_tags": "pescatarian,gluten-free,dairy-free,low-carb,high-protein",
            "meal_type": "dinner",
            "instructions": "1. Preheat oven to 400°F. 2. Place cod fillets in a baking dish. 3. Mix olive oil, lemon juice, garlic, and herbs. 4. Pour mixture over fish. 5. Bake for 15-20 minutes until fish flakes easily."
        },
        {
            "id": 13,
            "name": "Protein-Packed Smoothie Bowl",
            "description": "A thick and creamy smoothie bowl topped with fruits, nuts, and seeds.",
            "calories": 390,
            "protein": 25,
            "carbs": 40,
            "fat": 15,
            "ingredients": "Protein powder, frozen banana, berries, almond milk, nut butter, toppings (granola, fruit, seeds)",
            "cooking_status": "uncooked",
            "cooking_time": 10,
            "diet_tags": "vegetarian,high-protein",
            "meal_type": "breakfast",
            "instructions": "1. Blend protein powder, frozen banana, berries, almond milk, and nut butter until thick. 2. Pour into a bowl. 3. Top with granola, fresh fruit, and seeds."
        },
        {
            "id": 14,
            "name": "Zucchini Noodles with Pesto and Cherry Tomatoes",
            "description": "A light and fresh low-carb alternative to pasta using spiralized zucchini.",
            "calories": 310,
            "protein": 10,
            "carbs": 15,
            "fat": 24,
            "ingredients": "Zucchini, basil pesto, cherry tomatoes, pine nuts, parmesan cheese",
            "cooking_status": "cooked",
            "cooking_time": 15,
            "diet_tags": "vegetarian,gluten-free,low-carb",
            "meal_type": "lunch",
            "instructions": "1. Spiralize zucchini into noodles. 2. Lightly sauté zucchini noodles for 2-3 minutes. 3. Toss with pesto. 4. Add halved cherry tomatoes. 5. Top with pine nuts and grated parmesan."
        },
        {
            "id": 15,
            "name": "Quinoa and Black Bean Stuffed Sweet Potatoes",
            "description": "Baked sweet potatoes stuffed with a flavorful quinoa and black bean mixture.",
            "calories": 420,
            "protein": 15,
            "carbs": 65,
            "fat": 12,
            "ingredients": "Sweet potatoes, quinoa, black beans, corn, red pepper, onion, spices, avocado",
            "cooking_status": "cooked",
            "cooking_time": 60,
            "diet_tags": "vegan,vegetarian,gluten-free,dairy-free,high-fiber",
            "meal_type": "dinner",
            "instructions": "1. Bake sweet potatoes at 400°F for 45-60 minutes. 2. Cook quinoa according to package instructions. 3. Mix quinoa with black beans, corn, diced red pepper, and spices. 4. Split open baked sweet potatoes and stuff with quinoa mixture. 5. Top with sliced avocado."
        }
    ]
    
    # Generate embeddings for each recipe if not already present
    for recipe in recipes:
        if "embedding" not in recipe:
            # Create a rich text representation for embedding
            recipe_text = f"{recipe['name']}. {recipe['description']}. Ingredients: {recipe['ingredients']}. Diet tags: {recipe['diet_tags']}. Meal type: {recipe['meal_type']}."
            recipe["embedding"] = generate_embedding(recipe_text)
    
    return recipes

# Function to filter recipes based on user preferences and rules
def filter_recipes(recipes, preferences):
    filtered_recipes = []
    rules = []
    
    # Create rules based on preferences
    if preferences["diet_type"] != "No restrictions":
        rules.append(FoodRule("require_diet", preferences["diet_type"].lower()))
    
    for allergy in preferences["allergies"]:
        rules.append(FoodRule("exclude_ingredient", allergy.lower()))
    
    if preferences["cooking_preference"] == "Cooked meals":
        rules.append(FoodRule("cooking_preference", "cooked"))
    elif preferences["cooking_preference"] == "No-cook/quick meals":
        rules.append(FoodRule("cooking_preference", "no-cook"))
    
    rules.append(FoodRule("max_calories", preferences["calories"]))
    
    # Apply rules to filter recipes
    for recipe in recipes:
        valid = True
        for rule in rules:
            if not rule.apply(recipe):
                valid = False
                break
        if valid:
            filtered_recipes.append(recipe)
    
    return filtered_recipes

# Function to find similar recipes using embeddings
def find_similar_recipes(query, recipes, top_n=5):
    # Generate embedding for the query
    query_embedding = generate_embedding(query)
    if not query_embedding:
        return []
    
    # Calculate similarity scores
    similarities = []
    for recipe in recipes:
        if "embedding" in recipe and recipe["embedding"]:
            similarity = cosine_similarity([query_embedding], [recipe["embedding"]])[0][0]
            similarities.append((recipe, similarity))
    
    # Sort by similarity and return top N
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in similarities[:top_n]]

# Function to generate meal plan using RAG
def generate_meal_plan(preferences, filtered_recipes):
    if not filtered_recipes:
        return "No recipes match your preferences. Please try adjusting your criteria."
    
    # Create a prompt for the LLM
    recipe_descriptions = "\n\n".join([
        f"Recipe {i+1}: {recipe['name']}\n"
        f"Description: {recipe['description']}\n"
        f"Calories: {recipe['calories']}\n"
        f"Protein: {recipe['protein']}g\n"
        f"Carbs: {recipe['carbs']}g\n"
        f"Fat: {recipe['fat']}g\n"
        f"Ingredients: {recipe['ingredients']}\n"
        f"Diet tags: {recipe['diet_tags']}\n"
        f"Meal type: {recipe['meal_type']}"
        for i, recipe in enumerate(filtered_recipes[:10])  # Limit to 10 recipes for token constraints
    ])
    
    plan_type = "a single day meal plan with breakfast, lunch, and dinner" if preferences["plan_type"] == "Single Day Plan" else "a full week meal plan"
    
    prompt = f"""Based on the user's preferences:
- Diet: {preferences['diet_type']}
- Allergies: {', '.join(preferences['allergies']) if preferences['allergies'] else 'None'}
- Cooking preference: {preferences['cooking_preference']}
- Calorie target: {preferences['calories']} calories per day
- Goal: {preferences['goal'] if preferences['goal'] else 'Not specified'}

And using these available recipes:
{recipe_descriptions}

Create {plan_type} that:
1. Strictly adheres to their dietary restrictions and avoids all allergens
2. Maintains daily calories around their target of {preferences['calories']}
3. Respects their cooking preference of {preferences['cooking_preference']}
4. Supports their goal of {preferences['goal'] if preferences['goal'] else 'healthy eating'}
5. Provides variety throughout the plan
6. Includes nutritional benefits of key meals

For each meal, specify:
- The recipe name (from the provided recipes)
- Calories
- Key nutritional benefits related to their goal
- Any modifications to better suit their preferences

Format as a clear plan with brief explanations of how specific meals support their goals.
"""

    try:
        # Generate meal plan using OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a nutritionist and meal planning expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating meal plan: {str(e)}")
        return "Error generating meal plan. Please try again."

# Function to save user preferences and recommendations
def save_user_data(preferences, recommendation):
    try:
        # In a real app, this would save to a database
        # For this demo, we'll just create a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.history.append({
            "timestamp": timestamp,
            "preferences": preferences,
            "recommendation": recommendation
        })
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return False

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

# App Header
st.markdown('<h1 class="main-header">🍽️ Personalized Meal Recommendation Expert System</h1>', unsafe_allow_html=True)
st.markdown("""
This expert system uses AI and Retrieval Augmented Generation (RAG) to provide personalized meal recommendations 
based on your dietary preferences, restrictions, and nutritional goals.
""")

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Get Recommendations", "Recipe Database", "History"])

with tab1:
    # User Input Form
    st.markdown('<h2 class="sub-header">Your Preferences</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # API key handling
        api_key = st.text_input("OpenAI API Key (required):", type="password", key="openai_key")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            client = OpenAI(api_key=api_key)
        
        diet_type = st.selectbox(
            "Select your diet type:", 
            ["No restrictions", "Vegetarian", "Vegan", "Keto", "Gluten-free", "Paleo", "Whole30", "Pescatarian", "Dairy-free"]
        )
        
        allergies = st.multiselect(
            "Select any allergies:", 
            ["Nuts", "Dairy", "Shellfish", "Eggs", "Soy", "Wheat", "Fish", "Gluten"]
        )
        
        cooking_preference = st.selectbox(
            "Cooking preference:",
            ["Any", "Cooked meals", "No-cook/quick meals"]
        )
    
    with col2:
        calories = st.slider("Daily calorie target:", 1000, 3000, 2000)
        
        goal = st.text_input("Your nutrition goal (e.g., weight loss, muscle gain, heart health):")
        
        plan_type = st.radio(
            "What would you like to generate?", 
            ["Single Day Plan", "Full Week Plan"]
        )
        
        # Add a text area for additional preferences or constraints
        additional_info = st.text_area("Any additional preferences or health conditions:", 
                                      placeholder="E.g., low sodium, high iron, pregnancy, diabetes, etc.")
    
    # Check if we have the necessary API key
    if "OPENAI_API_KEY" not in os.environ:
        st.warning("Please enter your OpenAI API key to get personalized recommendations.")
    else:
        if st.button("Generate Meal Plan", type="primary"):
            # Show a spinner while processing
            with st.spinner("Analyzing your preferences and generating personalized recommendations..."):
                try:
                    # Load recipe database
                    recipes = load_recipe_database()
                    
                    # Prepare user preferences
                    user_preferences = {
                        'diet_type': diet_type,
                        'allergies': allergies,
                        'calories': calories,
                        'goal': goal,
                        'cooking_preference': cooking_preference,
                        'plan_type': plan_type,
                        'additional_info': additional_info
                    }
                    
                    # Filter recipes based on preferences
                    filtered_recipes = filter_recipes(recipes, user_preferences)
                    
                    if not filtered_recipes:
                        st.error("No recipes match your criteria. Please try adjusting your preferences.")
                    else:
                        # Find similar recipes if user has a specific goal
                        if goal:
                            goal_specific_recipes = find_similar_recipes(
                                f"Recipes that support {goal} with {diet_type} diet", 
                                filtered_recipes
                            )
                            # Add these to the top of filtered recipes
                            # Remove duplicates
                            filtered_recipes = goal_specific_recipes + [r for r in filtered_recipes if r not in goal_specific_recipes]
                        
                        # Generate meal plan
                        recommendation = generate_meal_plan(user_preferences, filtered_recipes)
                        
                        # Save to history
                        save_user_data(user_preferences, recommendation)
                        
                        # Display recommendation
                        st.markdown('<h2 class="sub-header">Your Personalized Meal Plan</h2>', unsafe_allow_html=True)
                        st.markdown(f'<div class="card">{recommendation}</div>', unsafe_allow_html=True)
                        
                        # Add a download button for the meal plan
                        st.download_button(
                            label="Download Meal Plan",
                            data=recommendation,
                            file_name=f"meal_plan_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain"
                        )
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

with tab2:
    st.markdown('<h2 class="sub-header">Recipe Database</h2>', unsafe_allow_html=True)
    st.write("Browse our collection of recipes that can be used in your meal plans.")
    
    # Load recipes
    recipes = load_recipe_database()
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        meal_type_filter = st.multiselect(
            "Filter by meal type:",
            options=list(set(recipe["meal_type"] for recipe in recipes)),
            default=[]
        )
    
    with col2:
        diet_filter = st.multiselect(
            "Filter by diet:",
            options=["vegetarian", "vegan", "keto", "gluten-free", "paleo", "whole30", "pescatarian", "dairy-free"],
            default=[]
        )
    
    with col3:
        cooking_filter = st.multiselect(
            "Filter by cooking status:",
            options=["cooked", "uncooked"],
            default=[]
        )
    
    # Apply filters
    filtered_db_recipes = recipes
    if meal_type_filter:
        filtered_db_recipes = [r for r in filtered_db_recipes if r["meal_type"] in meal_type_filter]
    
    if diet_filter:
        filtered_db_recipes = [r for r in filtered_db_recipes if any(diet in r["diet_tags"] for diet in diet_filter)]
    
    if cooking_filter:
        filtered_db_recipes = [r for r in filtered_db_recipes if r["cooking_status"] in cooking_filter]
    
    # Display recipes in a grid
    st.write(f"Showing {len(filtered_db_recipes)} recipes")
    
    # Create rows of recipes
    for i in range(0, len(filtered_db_recipes), 3):
        cols = st.columns(3)
        for j in range(3):
            if i+j < len(filtered_db_recipes):
                recipe = filtered_db_recipes[i+j]
                with cols[j]:
                    st.markdown(f'<div class="card">', unsafe_allow_html=True)
                    st.markdown(f'<p class="meal-title">{recipe["name"]}</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="meal-detail">{recipe["description"]}</p>', unsafe_allow_html=True)
                    st.markdown(f'<p><span class="nutrition-badge">{recipe["calories"]} cal</span> <span class="nutrition-badge">{recipe["protein"]}g protein</span></p>', unsafe_allow_html=True)
                    
                    # Display diet tags
                    tags = recipe["diet_tags"].split(",")
                    tag_html = "".join([f'<span class="nutrition-badge">{tag}</span>' for tag in tags])
                    st.markdown(f'<p>{tag_html}</p>', unsafe_allow_html=True)
                    
                    # Add a button to view recipe details
                    if st.button(f"View Details", key=f"view_{recipe['id']}"):
                        st.session_state.selected_recipe = recipe
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display recipe details if one is selected
    if "selected_recipe" in st.session_state:
        recipe = st.session_state.selected_recipe
        st.markdown('<h3 class="sub-header">Recipe Details</h3>', unsafe_allow_html=True)
        st.markdown(f'<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<p class="meal-title">{recipe["name"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="meal-detail">{recipe["description"]}</p>', unsafe_allow_html=True)
        
        # Create two columns for details
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Nutrition Information")
            st.markdown(f"**Calories:** {recipe['calories']}")
            st.markdown(f"**Protein:** {recipe['protein']}g")
            st.markdown(f"**Carbs:** {recipe['carbs']}g")
            st.markdown(f"**Fat:** {recipe['fat']}g")
        
        with col2:
            st.markdown("### Preparation")
            st.markdown(f"**Cooking Time:** {recipe['cooking_time']} minutes")
            st.markdown(f"**Cooking Status:** {recipe['cooking_status']}")
            st.markdown(f"**Meal Type:** {recipe['meal_type']}")
        
        st.markdown("### Ingredients")
        ingredients = recipe["ingredients"].split(", ")
        for ingredient in ingredients:
            st.markdown(f"- {ingredient}")
        
        st.markdown("### Instructions")
        instructions = recipe["instructions"].split(". ")
        for i, instruction in enumerate(instructions):
            if instruction:
                st.markdown(f"{i+1}. {instruction}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("Close Recipe"):
            del st.session_state.selected_recipe

with tab3:
    st.markdown('<h2 class="sub-header">Your Recommendation History</h2>', unsafe_allow_html=True)
    
    if not st.session_state.history:
        st.info("You haven't generated any recommendations yet. Try creating a meal plan!")
    else:
        for i, entry in enumerate(reversed(st.session_state.history)):
            with st.expander(f"Recommendation from {entry['timestamp']}"):
                st.markdown("### Your Preferences")
                st.write(f"Diet Type: {entry['preferences']['diet_type']}")
                st.write(f"Allergies: {', '.join(entry['preferences']['allergies']) if entry['preferences']['allergies'] else 'None'}")
                st.write(f"Calorie Target: {entry['preferences']['calories']}")
                st.write(f"Goal: {entry['preferences']['goal'] if entry['preferences']['goal'] else 'Not specified'}")
                
                st.markdown("### Recommendation")
                st.markdown(entry['recommendation'])
                
                # Add a download button for this recommendation
                st.download_button(
                    label="Download This Meal Plan",
                    data=entry['recommendation'],
                    file_name=f"meal_plan_{entry['timestamp'].replace(' ', '_').replace(':', '-')}.txt",
                    mime="text/plain",
                    key=f"download_{i}"
                )

# Add information about the app in the sidebar
st.sidebar.markdown("## About This Expert System")
st.sidebar.info(
    "This meal recommendation system uses AI with Retrieval Augmented Generation (RAG) to provide personalized meal suggestions "
    "based on your dietary preferences, restrictions, cooking preferences, and nutritional goals."
)

st.sidebar.markdown("### How It Works")
st.sidebar.markdown(
    "1. **Rule-Based Filtering**: Your preferences are converted to rules that filter our recipe database\n"
    "2. **Semantic Search**: We use AI embeddings to find recipes that match your goals\n"
    "3. **RAG Generation**: The system combines filtered recipes with your preferences to generate a personalized meal plan\n"
    "4. **Nutritional Analysis**: Each recommendation is analyzed for nutritional balance"
)

st.sidebar.markdown("### Features")
st.sidebar.markdown(
    "- Personalized meal plans based on dietary preferences\n"
    "- Support for various diet types and allergies\n"
    "- Calorie and macronutrient targeting\n"
    "- Goal-specific recommendations\n"
    "- Recipe database with detailed nutritional information"
)

# Run the app
if __name__ == "__main__":
    # This is handled by Streamlit automatically
    pass