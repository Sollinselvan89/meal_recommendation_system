import streamlit as st
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
import json
from datetime import datetime
import time
import random
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import matplotlib.pyplot as plt
import itertools

# Import your modules
from database import get_recipes, search_recipes, set_spoonacular_api_key, initialize_database, get_recipe_by_id, count_recipes
from rules import create_rules_from_preferences, filter_recipes
from embeddings import generate_embedding, find_similar_recipes

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define color palette with more vibrant colors
COLORS = {
    "primary": "#FF3366",     # Vibrant pink
    "secondary": "#33CCFF",   # Bright cyan
    "accent1": "#FFCC00",     # Bright yellow
    "accent2": "#9933FF",     # Vibrant purple
    "accent3": "#66FF99",     # Bright mint
    "text": "#2F2D2E",        # Dark gray
    "success": "#00FF99",     # Neon green
    "warning": "#FFCC00",     # Bright yellow
    "error": "#FF3366",       # Vibrant pink
    "background": "#F7FFF7"   # Off-white (will be replaced with gradient)
}

# Diet type colors
DIET_COLORS = {
    "Vegetarian": "#4CAF50",  # Green
    "Vegan": "#8BC34A",       # Light Green
    "Keto": "#FF9800",        # Orange
    "Gluten-free": "#FFEB3B", # Yellow
    "Paleo": "#795548",       # Brown
    "Whole30": "#9C27B0",     # Purple
    "Pescatarian": "#03A9F4", # Light Blue
    "Dairy-free": "#E91E63",  # Pink
    "No restrictions": "#9E9E9E" # Gray
}

# Set page configuration
st.set_page_config(
    page_title="🍽️ Meal Recommendation System",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, clean styling
st.markdown(f"""
<style>
    /* Reset and base styles */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }}
    
    body {{
        font-family: 'Inter', sans-serif;
        color: #333;
        background-color: #f8f9fa;
    }}
    
    /* Header styles */
    h1 {{
        color: #4a4a4a;
        font-size: 3rem !important;
        font-weight: 700 !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
    }}
    
    h2 {{
        color: #4a4a4a;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem;
    }}
    
    h3 {{
        color: #4a4a4a;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }}
    
    /* Card container */
    .content-container {{
        background-color: #ffffff;
        border-radius: 10px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #e0e0e0;
    }}
    
    /* Form elements */
    .stTextInput > div > div > input {{
        border-radius: 5px;
        border: 1px solid #e0e0e0;
    }}
    
    .stSelectbox > div > div > div {{
        border-radius: 5px;
        border: 1px solid #e0e0e0;
    }}
    
    /* Buttons */
    .stButton>button {{
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    
    .stButton>button:hover {{
        background-color: #2980b9;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }}
    
    /* Section headers with icons */
    .section-header {{
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        font-weight: 600;
        font-size: 1.1rem;
    }}
    
    .section-header svg {{
        margin-right: 8px;
    }}
    
    /* Checkbox container */
    .checkbox-container {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 15px;
    }}
    
    .checkbox-item {{
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 8px 15px;
        display: flex;
        align-items: center;
        min-width: 120px;
    }}
    
    /* Subtitle */
    .subtitle {{
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 5px;
        gap: 1px;
        padding: 10px 20px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: #3498db;
        color: white;
    }}
    
    /* Recipe cards */
    .recipe-card {{
        background: #ffffff;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #e0e0e0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    
    .recipe-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    /* Badges */
    .badge {{
        display: inline-block;
        padding: 4px 8px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 5px;
        margin-bottom: 5px;
        background-color: #e0e0e0;
        color: #333;
    }}
    
    /* Slider */
    .stSlider [data-baseweb="slider"] {{
        margin-top: 10px;
        margin-bottom: 10px;
    }}
    
    /* Calorie label */
    .calorie-label {{
        background-color: #f0f0f0;
        border-radius: 15px;
        padding: 5px 10px;
        font-weight: 500;
        display: inline-block;
    }}
</style>
""", unsafe_allow_html=True)

# Food emoji dictionary
FOOD_EMOJIS = {
    "breakfast": "🍳",
    "lunch": "🥗",
    "dinner": "🍲",
    "dessert": "🍰",
    "snack": "🍎",
    "vegetarian": "🥦",
    "vegan": "🌱",
    "keto": "🥑",
    "gluten free": "🌾",
    "high-protein": "💪",
    "low-carb": "🥩",
    "pescatarian": "🐟"
}

# Function to get a food emoji
def get_food_emoji(key):
    if not key:
        return "🍽️"
    key = key.lower()
    return FOOD_EMOJIS.get(key, "🍽️")

# Function to get a color for diet type
def get_diet_color(diet_type):
    return DIET_COLORS.get(diet_type, "#9E9E9E")

# Initialize the database if needed
@st.cache_resource
def init_db(min_recipes=150):  # Increased minimum recipes
    try:
        return initialize_database(min_recipes=min_recipes)
    except Exception as e:
        st.error(f"Error initializing database: {e}")
        return 0

# Function to update database with more recipes
@st.cache_resource(show_spinner=False)
def update_database(additional_recipes=100):  # Increased additional recipes
    from database import collect_recipes
    try:
        return collect_recipes(target_count=additional_recipes)
    except Exception as e:
        st.error(f"Error updating database: {e}")
        return 0

# Load recipes from database
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_recipe_database(diet_type=None, meal_type=None, limit=200):  # Increased limit
    try:
        return get_recipes(limit=limit, diet_type=diet_type, meal_type=meal_type)
    except Exception as e:
        st.error(f"Error loading recipes: {e}")
        # Return empty DataFrame as fallback
        return pd.DataFrame()

# Function to find the best combination of meals to match calorie target
def find_best_meal_combination(breakfast_recipes, lunch_recipes, dinner_recipes, snack_recipes, target_calories):
    # If any category is empty, fill with recipes from other categories
    if not breakfast_recipes:
        breakfast_recipes = lunch_recipes if lunch_recipes else dinner_recipes if dinner_recipes else snack_recipes
    if not lunch_recipes:
        lunch_recipes = dinner_recipes if dinner_recipes else breakfast_recipes if breakfast_recipes else snack_recipes
    if not dinner_recipes:
        dinner_recipes = lunch_recipes if lunch_recipes else breakfast_recipes if breakfast_recipes else snack_recipes
    if not snack_recipes:
        snack_recipes = breakfast_recipes if breakfast_recipes else lunch_recipes if lunch_recipes else dinner_recipes
    
    # Ensure we have at least one recipe in each category
    if not breakfast_recipes or not lunch_recipes or not dinner_recipes or not snack_recipes:
        return None, None, None, None
    
    # Limit the number of recipes to consider to avoid combinatorial explosion
    max_recipes_per_category = 10
    breakfast_recipes = breakfast_recipes[:max_recipes_per_category]
    lunch_recipes = lunch_recipes[:max_recipes_per_category]
    dinner_recipes = dinner_recipes[:max_recipes_per_category]
    snack_recipes = snack_recipes[:max_recipes_per_category]
    
    best_combination = None
    best_diff = float('inf')
    
    # Try different combinations of breakfast, lunch, dinner, and snack
    for b in breakfast_recipes:
        for l in lunch_recipes:
            for d in dinner_recipes:
                for s in snack_recipes:
                    total_calories = b['calories'] + l['calories'] + d['calories'] + s['calories']
                    diff = abs(total_calories - target_calories)
                    
                    if diff < best_diff:
                        best_diff = diff
                        best_combination = (b, l, d, s)
    
    if best_combination:
        return best_combination
    else:
        # Fallback: just return the first recipe from each category
        return (breakfast_recipes[0], lunch_recipes[0], dinner_recipes[0], snack_recipes[0])

# Function to generate a meal plan using RAG
def generate_meal_plan(preferences, filtered_recipes):
    if not filtered_recipes:
        return "No recipes match your preferences. Please try adjusting your criteria."
    
    # Create a prompt for the LLM
    plan_type = "a single day meal plan" if preferences["plan_type"] == "Single Day Plan" else "a full week meal plan"
    
    # For demo purposes, we'll create a simple meal plan without using the API
    if preferences["plan_type"] == "Single Day Plan":
        # Find recipes for each meal type with better calorie targeting
        breakfast_recipes = [r for r in filtered_recipes if r.get("meal_type") == "breakfast"]
        lunch_recipes = [r for r in filtered_recipes if r.get("meal_type") == "lunch"]
        dinner_recipes = [r for r in filtered_recipes if r.get("meal_type") == "dinner"]
        snack_recipes = [r for r in filtered_recipes if r.get("meal_type") == "snack"]
        
        # If we don't have enough recipes in specific categories, use any recipes
        if len(breakfast_recipes) < 5:
            additional_breakfast = [r for r in filtered_recipes if r.get("calories", 0) < 500][:10]
            breakfast_recipes.extend(additional_breakfast)
        
        if len(lunch_recipes) < 5:
            additional_lunch = [r for r in filtered_recipes if 300 <= r.get("calories", 0) <= 700][:10]
            lunch_recipes.extend(additional_lunch)
        
        if len(dinner_recipes) < 5:
            additional_dinner = [r for r in filtered_recipes if r.get("calories", 0) >= 400][:10]
            dinner_recipes.extend(additional_dinner)
            
        if len(snack_recipes) < 5:
            additional_snacks = [r for r in filtered_recipes if r.get("calories", 0) <= 300][:10]
            snack_recipes.extend(additional_snacks)

        # Find the best combination of meals to match the target calories
        breakfast, lunch, dinner, snack = find_best_meal_combination(
            breakfast_recipes, 
            lunch_recipes, 
            dinner_recipes, 
            snack_recipes, 
            preferences['calories']
        )
        
        # Calculate totals
        total_calories = breakfast["calories"] + lunch["calories"] + dinner["calories"] + snack["calories"]
        total_protein = breakfast["protein"] + lunch["protein"] + dinner["protein"] + snack["protein"]
        total_carbs = breakfast["carbs"] + lunch["carbs"] + dinner["carbs"] + snack["carbs"]
        total_fat = breakfast["fat"] + lunch["fat"] + dinner["fat"] + snack["fat"]
        
        plan = f"""# Your Personalized Daily Meal Plan 🍽️

## Breakfast: {breakfast['name']} {get_food_emoji('breakfast')}
**Calories:** {breakfast['calories']} | **Protein:** {breakfast['protein']}g | **Carbs:** {breakfast['carbs']}g | **Fat:** {breakfast['fat']}g

{breakfast.get('ingredients', 'A delicious breakfast option')}

This breakfast is perfect for your {preferences['goal'] if preferences['goal'] else 'nutritional needs'} because it provides a balanced start to your day with protein and essential nutrients.

## Lunch: {lunch['name']} {get_food_emoji('lunch')}
**Calories:** {lunch['calories']} | **Protein:** {lunch['protein']}g | **Carbs:** {lunch['carbs']}g | **Fat:** {lunch['fat']}g

{lunch.get('ingredients', 'A nutritious lunch option')}

This lunch option supports your {preferences['goal'] if preferences['goal'] else 'dietary preferences'} with lean protein and vegetables.

## Dinner: {dinner['name']} {get_food_emoji('dinner')}
**Calories:** {dinner['calories']} | **Protein:** {dinner['protein']}g | **Carbs:** {dinner['carbs']}g | **Fat:** {dinner['fat']}g

{dinner.get('ingredients', 'A satisfying dinner choice')}

This dinner is designed to complement your earlier meals while supporting your {preferences['goal'] if preferences['goal'] else 'nutritional goals'}.

## Snack: {snack['name']} {get_food_emoji('snack')}
**Calories:** {snack['calories']} | **Protein:** {snack['protein']}g | **Carbs:** {snack['carbs']}g | **Fat:** {snack['fat']}g

{snack.get('ingredients', 'A tasty snack option')}

This snack helps you reach your daily calorie target while providing additional nutrients to support your goals.

## Daily Nutrition Summary
- **Total Calories:** {total_calories} (Target: {preferences['calories']})
- **Total Protein:** {total_protein}g
- **Total Carbs:** {total_carbs}g
- **Total Fat:** {total_fat}g

This meal plan is specifically designed for your {preferences['diet_type']} diet and takes into account your {', '.join(preferences['allergies']) if preferences['allergies'] else 'preferences'}.
"""
    else:
        # For a weekly plan, we'll create a more sophisticated version
        # Group recipes by meal type
        breakfast_recipes = [r for r in filtered_recipes if r.get("meal_type") == "breakfast"]
        lunch_recipes = [r for r in filtered_recipes if r.get("meal_type") == "lunch"]
        dinner_recipes = [r for r in filtered_recipes if r.get("meal_type") == "dinner"]
        snack_recipes = [r for r in filtered_recipes if r.get("meal_type") == "snack"]
        
        # If we don't have enough recipes in specific categories, use any recipes
        if len(breakfast_recipes) < 7:
            additional_breakfast = [r for r in filtered_recipes if r.get("calories", 0) < 500][:14]
            breakfast_recipes.extend(additional_breakfast)
        
        if len(lunch_recipes) < 7:
            additional_lunch = [r for r in filtered_recipes if 300 <= r.get("calories", 0) <= 700][:14]
            lunch_recipes.extend(additional_lunch)
        
        if len(dinner_recipes) < 7:
            additional_dinner = [r for r in filtered_recipes if r.get("calories", 0) >= 400][:14]
            dinner_recipes.extend(additional_dinner)
            
        if len(snack_recipes) < 7:
            additional_snacks = [r for r in filtered_recipes if r.get("calories", 0) <= 300][:14]
            snack_recipes.extend(additional_snacks)
        
        # Ensure we have at least 7 recipes for each meal type
        breakfast_recipes = breakfast_recipes[:7] if len(breakfast_recipes) >= 7 else breakfast_recipes * (7 // len(breakfast_recipes) + 1)
        lunch_recipes = lunch_recipes[:7] if len(lunch_recipes) >= 7 else lunch_recipes * (7 // len(lunch_recipes) + 1)
        dinner_recipes = dinner_recipes[:7] if len(dinner_recipes) >= 7 else dinner_recipes * (7 // len(dinner_recipes) + 1)
        snack_recipes = snack_recipes[:7] if len(snack_recipes) >= 7 else snack_recipes * (7 // len(snack_recipes) + 1)
        
        # Shuffle recipes to ensure variety
        random.shuffle(breakfast_recipes)
        random.shuffle(lunch_recipes)
        random.shuffle(dinner_recipes)
        random.shuffle(snack_recipes)
        
        # Create weekly plan
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekly_plan = []
        
        for i, day in enumerate(days):
            b = breakfast_recipes[i % len(breakfast_recipes)]
            l = lunch_recipes[i % len(lunch_recipes)]
            d = dinner_recipes[i % len(dinner_recipes)]
            s = snack_recipes[i % len(snack_recipes)]
            
            daily_calories = b['calories'] + l['calories'] + d['calories'] + s['calories']
            
            daily_plan = {
                "day": day,
                "breakfast": b,
                "lunch": l,
                "dinner": d,
                "snack": s,
                "total_calories": daily_calories
            }
            
            weekly_plan.append(daily_plan)
        
        # Generate the plan text
        plan = f"# Your Personalized Weekly Meal Plan 🍽️\n\n"
        
        for day_plan in weekly_plan:
            plan += f"## {day_plan['day']}\n"
            plan += f"- **Breakfast:** {day_plan['breakfast']['name']} ({day_plan['breakfast']['calories']} calories)\n"
            plan += f"- **Lunch:** {day_plan['lunch']['name']} ({day_plan['lunch']['calories']} calories)\n"
            plan += f"- **Dinner:** {day_plan['dinner']['name']} ({day_plan['dinner']['calories']} calories)\n"
            plan += f"- **Snack:** {day_plan['snack']['name']} ({day_plan['snack']['calories']} calories)\n"
            plan += f"- **Daily Total:** {day_plan['total_calories']} calories\n\n"
        
        # Calculate weekly averages
        avg_calories = sum(day['total_calories'] for day in weekly_plan) / 7
        
        plan += f"""## Weekly Nutrition Summary
This meal plan is specifically designed for your {preferences['diet_type']} diet and takes into account your {', '.join(preferences['allergies']) if preferences['allergies'] else 'preferences'}. It provides a variety of meals throughout the week to ensure you get a balanced diet.

The plan emphasizes {preferences['goal'] if preferences['goal'] else 'balanced nutrition'} with a good mix of proteins, healthy fats, and complex carbohydrates. Each meal was selected to support your dietary needs while providing variety throughout the week.

**Average Daily Calories:** {avg_calories:.0f} (Target: {preferences['calories']})
"""
    
    return plan

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "page" not in st.session_state:
    st.session_state.page = "home"
if "db_initialized" not in st.session_state:
    st.session_state.db_initialized = False

# App Header with cleaner design
st.markdown("""
<h1>Expert Meal Recommendation System</h1>
<p class="subtitle">Get tailored meal suggestions based on your dietary preferences, calorie requirements, and nutritional goals</p>
""", unsafe_allow_html=True)

# Initialize database if not already done
if not st.session_state.db_initialized:
    recipe_count = init_db(min_recipes=150)  # Increased from default 20
    st.session_state.db_initialized = True

# Create tabs with simple icons
tab1, tab2, tab3 = st.tabs([
    "🍽️ Get Recommendations", 
    "🔍 Recipe Explorer", 
    "📊 Your History"
])

with tab1:
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="section-header">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 3h18v18H3zM12 8v8M8 12h8"></path>
        </svg>
        Your Preferences
    </div>
    <p style="color: #666; margin-bottom: 20px;">Tell us about your dietary needs and goals</p>
    """, unsafe_allow_html=True)
    
    # Create a cleaner form
    with st.form("meal_preferences_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Diet type with cleaner display
            st.markdown("""
            <div class="section-header" style="margin-top: 20px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 3L9 5v4l-5 7h12l-5-7V5l-2-2z"></path>
                    <path d="M13.8 12a4 4 0 1 0 0 8 4 4 0 1 0 0-8z"></path>
                </svg>
                Diet Type
            </div>
            """, unsafe_allow_html=True)
            
            diet_type = st.selectbox(
                "Select your diet type:", 
                ["No restrictions", "Vegetarian", "Vegan", "Keto", "Gluten-free", "Paleo", "Whole30", "Pescatarian", "Dairy-free"],
                label_visibility="collapsed"
            )
            
            # Allergies with checkbox grid
            st.markdown("""
            <div class="section-header" style="margin-top: 20px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0-3.42 0z"></path>
                    <line x1="12" y1="9" x2="12" y2="13"></line>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                Allergies
            </div>
            """, unsafe_allow_html=True)
            
            allergens = ["Nuts", "Dairy", "Shellfish", "Eggs", "Soy", "Wheat", "Fish", "Gluten"]
            allergies = []
            
            # Create a 2x4 grid for allergies
            for i in range(0, len(allergens), 2):
                col_a, col_b = st.columns(2)
                with col_a:
                    if i < len(allergens):
                        if st.checkbox(allergens[i], key=f"allergy_{allergens[i]}"):
                            allergies.append(allergens[i])
                with col_b:
                    if i+1 < len(allergens):
                        if st.checkbox(allergens[i+1], key=f"allergy_{allergens[i+1]}"):
                            allergies.append(allergens[i+1])
            
            # Cooking preference
            st.markdown("""
            <div class="section-header" style="margin-top: 20px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"></path>
                    <path d="M9 18h6"></path>
                    <path d="M10 22h4"></path>
                </svg>
                Cooking Preference
            </div>
            """, unsafe_allow_html=True)
            
            cooking_preference = st.selectbox(
                "Cooking preference:",
                ["Any", "Cooked meals", "No-cook/quick meals"],
                label_visibility="collapsed"
            )
        
        with col2:
            # Calorie slider with cleaner design
            st.markdown("""
            <div class="section-header">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M16.2 7.8l-2 6.3-6.4 2.1 2-6.3z"></path>
                </svg>
                Daily Calorie Target
            </div>
            """, unsafe_allow_html=True)
            
            calories = st.slider("", 1000, 3000, 2000, label_visibility="collapsed")
            
            # Display calorie category
            calorie_category = "Low calorie diet" if calories < 1500 else "Moderate calorie diet" if calories < 2000 else "Standard calorie diet" if calories < 2500 else "High calorie diet"
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                <span>1000</span>
                <span class="calorie-label">{calorie_category}</span>
                <span>3000</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Nutrition goal
            st.markdown("""
            <div class="section-header" style="margin-top: 20px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M12 8v8"></path>
                    <path d="M8  r="10"></circle>
                    <path d="M12 8v8"></path>
                    <path d="M8 12h8"></path>
                </svg>
                Nutrition Goal
            </div>
            """, unsafe_allow_html=True)
            
            goal = st.text_input("", placeholder="e.g., weight loss, muscle gain, heart health", label_visibility="collapsed")
            
            # Plan type with button-like selection
            st.markdown("""
            <div class="section-header" style="margin-top: 20px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                What would you like to generate?
            </div>
            """, unsafe_allow_html=True)
            
            plan_type = st.radio(
                "",
                ["Single Day Plan", "Full Week Plan"],
                horizontal=True,
                label_visibility="collapsed"
            )
            
            # Display preference
            st.markdown("""
            <div class="section-header" style="margin-top: 20px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="3" y1="9" x2="21" y2="9"></line>
                    <line x1="9" y1="21" x2="9" y2="9"></line>
                </svg>
                Display Preference
            </div>
            """, unsafe_allow_html=True)
            
            display_preference = st.selectbox(
                "",
                ["Text format", "Table format", "Both text and table"],
                label_visibility="collapsed"
            )
        
        # Add a cleaner submit button
        submit = st.form_submit_button("Generate My Meal Plan")

    # Process form submission
    if submit:
        # Show a spinner with custom styling
        with st.spinner("Creating your personalized meal plan..."):
            # Simulate processing time
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.02)
                progress_bar.progress(i + 1)
            
            # Load recipes
            recipes = load_recipe_database(diet_type=diet_type.lower() if diet_type != "No restrictions" else None)
            
            # Prepare user preferences
            user_preferences = {
                'diet_type': diet_type,
                'allergies': allergies,
                'calories': calories,
                'goal': goal,
                'cooking_preference': cooking_preference,
                'plan_type': plan_type
            }
            
            # Filter recipes based on preferences
            filtered_recipes = filter_recipes(recipes, user_preferences)
            
            if not filtered_recipes:
                st.error("No recipes match your criteria. Please try adjusting your preferences.")
            else:
                # Generate meal plan
                recommendation = generate_meal_plan(user_preferences, filtered_recipes)
                
                # Save to history
                st.session_state.history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "preferences": user_preferences,
                    "recommendation": recommendation
                })
                
                # Remove progress bar
                progress_bar.empty()
            
                # Display recommendation with cleaner styling
                st.markdown('<h2>Your Meal Plan</h2>', unsafe_allow_html=True)
                
                # Create a clean card for the meal plan
                st.markdown(f"""
                <div class="content-container">
                    {recommendation}
                </div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="content-container"><h2>Recipe Explorer</h2>', unsafe_allow_html=True)
    st.write("Browse our collection of recipes with vibrant visuals and detailed information.")
    
    # Load recipes
    recipes = load_recipe_database()
    
    # Add colorful filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        meal_type_filter = st.multiselect(
            "Filter by meal type:",
            options=["breakfast", "lunch", "dinner", "snack", "dessert", "appetizer", "salad", "soup"],
            default=[]
        )
    
    with col2:
        diet_filter = st.multiselect(
            "Filter by diet:",
            options=["vegetarian", "vegan", "keto", "gluten free", "paleo", "whole30", "pescatarian", "dairy free"],
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
    
    if not filtered_db_recipes.empty:
        if meal_type_filter:
            filtered_db_recipes = filtered_db_recipes[filtered_db_recipes['meal_type'].str.lower().isin([m.lower() for m in meal_type_filter])]
        
        if diet_filter:
            # Filter by diet tags or category
            mask = pd.Series(False, index=filtered_db_recipes.index)
            for diet in diet_filter:
                diet_mask = filtered_db_recipes['diet_tags'].str.contains(diet, case=False, na=False) | filtered_db_recipes['category'].str.contains(diet, case=False, na=False)
                mask = mask | diet_mask
            filtered_db_recipes = filtered_db_recipes[mask]
        
        if cooking_filter:
            filtered_db_recipes = filtered_db_recipes[filtered_db_recipes['cooking_status'].str.lower().isin([c.lower() for c in cooking_filter])]
    
    # Add search box with colorful styling
    st.markdown("""
    <div style="background-color: white; padding: 15px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <h3 style="margin-top: 0;">Search Recipes</h3>
    </div>
    """, unsafe_allow_html=True)
    
    search_query = st.text_input("Search by name or ingredient:", placeholder="e.g., chicken, breakfast, high-protein...")
    
    # Apply search filter if provided
    if search_query and not filtered_db_recipes.empty:
        search_results = search_recipes(search_query)
        if not search_results.empty:
            filtered_db_recipes = search_results
    
    # Display recipes in a colorful grid
    if filtered_db_recipes.empty:
        st.warning("No recipes found. Try adjusting your filters or search query.")
    else:
        st.markdown(f"<h3>Showing {len(filtered_db_recipes)} delicious recipes</h3>", unsafe_allow_html=True)
        
        # Create rows of recipes with colorful cards
        for i in range(0, len(filtered_db_recipes), 3):
            cols = st.columns(3)
            for j in range(3):
                if i+j < len(filtered_db_recipes):
                    recipe = filtered_db_recipes.iloc[i+j]
                    with cols[j]:
                        # Get diet tags and their colors
                        diet_tags = str(recipe.get("diet_tags", "")).split(",") if pd.notna(recipe.get("diet_tags", "")) else []
                        
                        # Create a colorful recipe card
                        st.markdown(f"""
                        <div class="recipe-card">
                            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                <span class="food-icon">{get_food_emoji(recipe.get('meal_type', 'dinner'))}</span>
                                <span class="meal-title">{recipe['name']}</span>
                            </div>
                            <p class="meal-detail">{recipe.get('ingredients', 'Delicious ingredients')}</p>
                            <div>
                                <span class="nutrition-badge" style="background-color: {COLORS['primary']};">{recipe['calories']} cal</span>
                                <span class="nutrition-badge" style="background-color: {COLORS['secondary']};">{recipe['protein']}g protein</span>
                            </div>
                            <div style="margin-top: 10px;">
                        """, unsafe_allow_html=True)
                        
                        # Add diet tags with different colors
                        for tag in diet_tags:
                            tag = tag.strip()
                            if tag:
                                tag_color = COLORS["accent2"]
                                if "vegetarian" in tag:
                                    tag_color = "#4CAF50"
                                elif "vegan" in tag:
                                    tag_color = "#8BC34A"
                                elif "keto" in tag:
                                    tag_color = "#FF9800"
                                elif "gluten-free" in tag:
                                    tag_color = "#FFEB3B"
                                
                                st.markdown(f"""
                                <span class="diet-badge" style="background-color: {tag_color};">{tag}</span>
                                """, unsafe_allow_html=True)
                        
                        st.markdown("""
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add a button to view recipe details
                        if st.button(f"View Details", key=f"view_{recipe['id']}"):
                            st.session_state.selected_recipe = recipe.to_dict()

    # Display recipe details if one is selected
    if "selected_recipe" in st.session_state:
        recipe = st.session_state.selected_recipe
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, white, {COLORS['accent3']}); 
                    border-radius: 15px; 
                    padding: 30px; 
                    margin-top: 30px;
                    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
                    border-left: 8px solid {COLORS['primary']};">
            <h2 style="color: {COLORS['primary']}; margin-top: 0;">{recipe['name']} {get_food_emoji(recipe.get('meal_type', 'dinner'))}</h2>
            <p style="font-size: 1.1rem; font-style: italic; color: {COLORS['text']};">{recipe.get('ingredients', 'A delicious recipe')}</p>
        """, unsafe_allow_html=True)
        
        # Create two columns for details
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background-color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <h3 style="color: {COLORS['secondary']}; margin-top: 0;">Nutrition Information</h3>
                <div style="display: flex; flex-wrap: wrap;">
                    <div style="background-color: {COLORS['primary']}; color: white; border-radius: 10px; padding: 15px; margin: 5px; flex: 1; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold;">{recipe['calories']}</div>
                        <div>Calories</div>
                    </div>
                    <div style="background-color: {COLORS['secondary']}; color: white; border-radius: 10px; padding: 15px; margin: 5px; flex: 1; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold;">{recipe['protein']}g</div>
                        <div>Protein</div>
                    </div>
                    <div style="background-color: {COLORS['accent1']}; color: {COLORS['text']}; border-radius: 10px; padding: 15px; margin: 5px; flex: 1; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold;">{recipe['carbs']}g</div>
                        <div>Carbs</div>
                    </div>
                    <div style="background-color: {COLORS['accent2']}; color: white; border-radius: 10px; padding: 15px; margin: 5px; flex: 1; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold;">{recipe['fat']}g</div>
                        <div>Fat</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background-color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <h3 style="color: {COLORS['secondary']}; margin-top: 0;">Preparation</h3>
                <div style="display: flex; flex-wrap: wrap;">
                    <div style="background-color: {COLORS['accent3']}; border: 2px solid {COLORS['secondary']}; border-radius: 10px; padding: 15px; margin: 5px; flex: 1; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold;">{recipe.get('ready_in_minutes', '20')}</div>
                        <div>Minutes</div>
                    </div>
                    <div style="background-color: {COLORS['accent3']}; border: 2px solid {COLORS['primary']}; border-radius: 10px; padding: 15px; margin: 5px; flex: 1; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold;">{recipe.get('cooking_status', 'cooked').capitalize()}</div>
                        <div>Status</div>
                    </div>
                </div>
                <div style="margin-top: 15px;">
                    <div style="font-weight: bold; margin-bottom: 5px;">Diet Tags:</div>
            """, unsafe_allow_html=True)
            
            # Add diet tags
            diet_tags = str(recipe.get('diet_tags', '')).split(",") if pd.notna(recipe.get('diet_tags', '')) else []
            for tag in diet_tags:
                tag = tag.strip()
                if tag:
                    tag_color = COLORS["accent2"]
                    if "vegetarian" in tag:
                        tag_color = "#4CAF50"
                    elif "vegan" in tag:
                        tag_color = "#8BC34A"
                    elif "keto" in tag:
                        tag_color = "#FF9800"
                    elif "gluten-free" in tag:
                        tag_color = "#FFEB3B"
                    
                    st.markdown(f"""
                    <span class="diet-badge" style="background-color: {tag_color};">{tag}</span>
                    """, unsafe_allow_html=True)
            
            st.markdown("""
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Ingredients and Instructions
        st.markdown(f"""
        <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-top: 20px;">
            <div style="flex: 1; min-width: 300px; background-color: white; padding: 20px; border-radius: 10px; border-top: 5px solid {COLORS['primary']};">
                <h3 style="color: {COLORS['primary']}; margin-top: 0;">Ingredients</h3>
                <ul style="padding-left: 20px;">
        """, unsafe_allow_html=True)
        
        # List ingredients
        ingredients = str(recipe.get('ingredients', '')).split(", ")
        for ingredient in ingredients:
            if ingredient.strip():
                st.markdown(f"<li>{ingredient}</li>", unsafe_allow_html=True)
        
        st.markdown("""
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style="flex: 1; min-width: 300px; background-color: white; padding: 20px; border-radius: 10px; border-top: 5px solid {COLORS['secondary']};">
                <h3 style="color: {COLORS['secondary']}; margin-top: 0;">Instructions</h3>
                <ol style="padding-left: 20px;">
                    <li>Prepare all ingredients as listed</li>
                    <li>Follow cooking instructions for this {recipe.get('cooking_status', 'cooked')} meal</li>
                    <li>Enjoy your delicious {recipe['name']}!</li>
                </ol>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("Close Recipe Details"):
            del st.session_state.selected_recipe

    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="content-container"><h2>Your Recommendation History</h2>', unsafe_allow_html=True)
    
    if not st.session_state.history:
        st.info("You haven't generated any recommendations yet. Try creating a meal plan!")
    else:
        # Create a timeline visualization
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px;">
            <h3 style="margin-top: 0;">Your Recommendation Timeline</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Display history entries with colorful styling
        for i, entry in enumerate(reversed(st.session_state.history)):
            # Alternate colors for entries
            border_color = COLORS["primary"] if i % 2 == 0 else COLORS["secondary"]
            
            with st.expander(f"Meal Plan from {entry['timestamp']}"):
                # Create columns for preferences and recommendation
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid {border_color};">
                        <h3 style="color: {border_color}; margin-top: 0;">Your Preferences</h3>
                        <p><strong>Diet Type:</strong> {entry['preferences']['diet_type']}</p>
                        <p><strong>Allergies:</strong> {', '.join(entry['preferences']['allergies']) if entry['preferences']['allergies'] else 'None'}</p>
                        <p><strong>Calorie Target:</strong> {entry['preferences']['calories']}</p>
                        <p><strong>Goal:</strong> {entry['preferences']['goal'] if entry['preferences']['goal'] else 'Not specified'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid {border_color};">
                        <h3 style="color: {border_color}; margin-top: 0;">Your Meal Plan</h3>
                        {entry['recommendation']}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Add a download button for this recommendation
                st.download_button(
                    label=f"📥 Download This Meal Plan",
                    data=entry['recommendation'],
                    file_name=f"meal_plan_{entry['timestamp'].replace(' ', '_').replace(':', '-')}.txt",
                    mime="text/plain",
                    key=f"download_{i}"
                )

    st.markdown('</div>', unsafe_allow_html=True)

# Add database update option in sidebar
st.sidebar.markdown(f"""
<div style="background-color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid {COLORS['primary']}">
    <h3 style="margin-top: 0; color: {COLORS['primary']};">Database Management</h3>
    <p>Current recipe count: {count_recipes()}</p>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🔄 Update Database with More Recipes"):
    with st.sidebar:
        with st.spinner("Fetching new recipes... This may take a minute."):
            new_count = update_database(additional_recipes=100)  # Increased to 100
            if new_count > 0:
                st.success(f"Successfully added new recipes! Database now contains {count_recipes()} recipes.")
                # Clear cache to reload recipes
                load_recipe_database.clear()
            else:
                st.warning("No new recipes were added. This could be due to API limits or network issues.")

# Add information about the app in the sidebar with colorful styling
st.sidebar.markdown(f"""
<div style="background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['secondary']}); 
            color: white; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 20px;">
    <h2 style="margin-top: 0; color: white;">About This System</h2>
    <p>This meal recommendation system uses AI with Retrieval Augmented Generation (RAG) to provide personalized meal suggestions based on your preferences.</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<div style="background-color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
    <h3 style="margin-top: 0; color: {COLORS['secondary']};">How It Works</h3>
    <ol style="padding-left: 20px;">
        <li><span style="color: {COLORS['primary']}; font-weight: bold;">Rule-Based Filtering:</span> Your preferences are converted to rules that filter our recipe database</li>
        <li><span style="color: {COLORS['primary']}; font-weight: bold;">Semantic Search:</span> We use AI embeddings to find recipes that match your goals</li>
        <li><span style="color: {COLORS['primary']}; font-weight: bold;">RAG Generation:</span> The system combines filtered recipes with your preferences to generate a personalized meal plan</li>
        <li><span style="color: {COLORS['primary']}; font-weight: bold;">Nutritional Analysis:</span> Each recommendation is analyzed for nutritional balance</li>
    </ol>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<div style="background-color: white; padding: 20px; border-radius: 10px;">
    <h3 style="margin-top: 0; color: {COLORS['secondary']};">Features</h3>
    <ul style="padding-left: 20px;">
        <li>Personalized meal plans based on dietary preferences</li>
        <li>Support for various diet types and allergies</li>
        <li>Calorie and macronutrient targeting</li>
        <li>Goal-specific recommendations</li>
        <li>Recipe database with detailed nutritional information</li>
        <li>Integration with Spoonacular API for thousands of recipes</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    # This is handled by Streamlit automatically
    pass
