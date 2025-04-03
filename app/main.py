import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# Import local modules
from rules import FoodRule
from database import load_food_data, set_spoonacular_api_key

# Load environment variables
load_dotenv()

# API key handling in sidebar
st.sidebar.title("API Keys")

# Spoonacular API key handling
spoonacular_key = st.sidebar.text_input("Enter your Spoonacular API key:", type="password", key="spoonacular_key")
if spoonacular_key:
    os.environ["SPOONACULAR_API_KEY"] = spoonacular_key
    set_spoonacular_api_key(spoonacular_key)

# OpenAI API key handling
openai_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password", key="openai_key")
if openai_key:
    os.environ["OPENAI_API_KEY"] = openai_key

# Check if we have the necessary API keys
if "OPENAI_API_KEY" not in os.environ:
    st.warning("Please enter your OpenAI API key in the sidebar to get personalized recommendations.")
    st.stop()

# Create vector store
@st.cache_resource
def get_vector_store(_documents):
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(_documents, embeddings)
    return vector_store

# App Title and Description
st.title("Personalized Meal Recommendation System")
st.write("Welcome to our expert system that provides meal recommendations based on your preferences!")

# User Input Form
st.header("Your Preferences")

# Added more diet types
diet_type = st.selectbox(
    "Select your diet type:", 
    ["No restrictions", "Vegetarian", "Vegan", "Keto", "Gluten-free", "Paleo", "Whole30", "Pescatarian", "Dairy-free"]
)

allergies = st.multiselect(
    "Select any allergies:", 
    ["None", "Nuts", "Dairy", "Shellfish", "Eggs", "Soy", "Wheat", "Fish", "Gluten"]
)

# Add cooking preference option
cooking_preference = st.selectbox(
    "Cooking preference:",
    ["Any", "Cooked meals", "No-cook/quick meals"]
)

calories = st.slider("Daily calorie target:", 1000, 3000, 2000)

goal = st.text_input("Your nutrition goal (e.g., weight loss, muscle gain, heart health):")

# Add toggle for meal plan or single recommendation
plan_type = st.radio(
    "What would you like to generate?", 
    ["Single Meal Recommendation", "Full Week Meal Plan"]
)

# Add display preference
display_preference = st.selectbox(
    "How would you like to see your recommendations?",
    ["Text format", "Table format", "Both text and table"]
)

if st.button("Get Recommendations"):
    # Show a spinner while processing
    with st.spinner("Generating your personalized recommendation..."):
        try:
            # Load data
            df, documents = load_food_data()
            
            if df.empty:
                st.error("No recipe data available. Please ensure your database or CSV file is properly set up.")
                st.stop()
                
            vector_store = get_vector_store(documents)
            
            # Apply rules to filter data
            rule_engine = FoodRule()
            foods_df = df.to_dict('records')
            user_preferences = {
                'diet_type': diet_type,
                'allergies': allergies,
                'calories': calories,
                'goal': goal,
                'cooking_preference': cooking_preference
            }
            
            filtered_foods = rule_engine.filter_foods(foods_df, user_preferences)
            
            # Create a query based on user preferences
            query = f"I need a meal that is {diet_type.lower()} friendly"
            if "None" not in allergies:
                query += f", without {', '.join(allergies).lower()}"
            query += f", around {calories} calories"
            
            # Add cooking preference to query
            if cooking_preference == "Cooked meals":
                query += ", that requires cooking"
            elif cooking_preference == "No-cook/quick meals":
                query += ", that requires minimal or no cooking"
                
            if goal:
                query += f" for {goal.lower()}"
            
            # Get more relevant meals from vector database for a meal plan
            k_value = 10 if plan_type == "Full Week Meal Plan" else 5
            results = vector_store.similarity_search(query, k=k_value)
            
            if not results:
                st.warning("No matching recipes found. Try adjusting your preferences.")
                st.stop()
            
            # Select appropriate template based on plan type and display preference
            if plan_type == "Full Week Meal Plan":
                if display_preference == "Table format" or display_preference == "Both text and table":
                    template = """
                    Based on the user's preferences:
                    - Diet: {diet_type}
                    - Allergies: {allergies}
                    - Cooking preference: {cooking_preference}
                    - Calorie target: {calories} calories per day
                    - Goal: {goal}

                    And using these potential meals as inspiration:
                    {meals}

                    Create a comprehensive 7-day meal plan (breakfast, lunch, dinner) that:
                    1. Strictly adheres to their dietary restrictions and avoids all allergens
                    2. Maintains daily calories around their target of {calories}
                    3. Respects their cooking preference of {cooking_preference}
                    4. Supports their goal of {goal}
                    5. Provides variety throughout the week

                    Return this in a structured format that can be easily converted to a table:
                    Day 1:
                    - Breakfast: [meal name] ([calories] calories) - [key ingredients]
                    - Lunch: [meal name] ([calories] calories) - [key ingredients]
                    - Dinner: [meal name] ([calories] calories) - [key ingredients]
                    - Daily Total: [total calories] calories

                    ... and so on for all 7 days.

                    After the table data, provide a brief paragraph explaining how this meal plan supports the user's goal of {goal}.
                    """
                else:
                    template = """
                    Based on the user's preferences:
                    - Diet: {diet_type}
                    - Allergies: {allergies}
                    - Cooking preference: {cooking_preference}
                    - Calorie target: {calories} calories per day
                    - Goal: {goal}

                    And using these potential meals as inspiration:
                    {meals}

                    Create a comprehensive 7-day meal plan (breakfast, lunch, dinner) that:
                    1. Strictly adheres to their dietary restrictions and avoids all allergens
                    2. Maintains daily calories around their target of {calories}
                    3. Respects their cooking preference of {cooking_preference}
                    4. Supports their goal of {goal}
                    5. Provides variety throughout the week
                    6. Includes nutritional benefits of key meals

                    Format as a clear 7-day plan with brief explanations of how specific meals support their goals.
                    """
            else:
                if display_preference == "Table format" or display_preference == "Both text and table":
                    template = """
                    Based on the user's preferences:
                    - Diet: {diet_type}
                    - Allergies: {allergies}
                    - Cooking preference: {cooking_preference}
                    - Calorie target: {calories}
                    - Goal: {goal}
                    
                    And these potential meals:
                    {meals}
                    
                    Provide THREE personalized meal recommendations that can be formatted into a table.
                    
                    For each meal, provide the following in a structured format:
                    
                    Recommendation 1:
                    - Name: [meal name]
                    - Calories: [calories]
                    - Protein: [protein]g
                    - Carbs: [carbs]g
                    - Fat: [fat]g
                    - Key Ingredients: [list of main ingredients]
                    - Cooking Time: [time in minutes]
                    - Cooking Required: [Yes/No]
                    - Supports Goal: [how it supports the user's goal]
                    
                    ... and so on for all 3 recommendations.
                    
                    After providing the structured data, add a brief paragraph summarizing how these meals collectively address the user's preferences and goals.
                    """
                else:
                    template = """
                    Based on the user's preferences:
                    - Diet: {diet_type}
                    - Allergies: {allergies}
                    - Cooking preference: {cooking_preference}
                    - Calorie target: {calories}
                    - Goal: {goal}
                    
                    And these potential meals:
                    {meals}
                    
                    Provide THREE personalized meal recommendations with detailed explanations for each.
                    For each meal:
                    1. Name the meal and describe its key ingredients
                    2. Explain exactly how it matches the user's dietary needs and cooking preference
                    3. Detail the specific nutritional benefits that align with their goal
                    4. Mention calorie content and macronutrient breakdown
                    
                    Make your recommendations varied and comprehensive.
                    """
            
            prompt = PromptTemplate(
                input_variables=["diet_type", "allergies", "cooking_preference", "calories", "goal", "meals"],
                template=template,
            )
            
            # Format meals for the prompt
            meals_text = "\n\n".join([doc.page_content for doc in results])
            
            # Create a chain with GPT-3.5
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
            chain = LLMChain(llm=llm, prompt=prompt)
            
            # Generate recommendation
            recommendation = chain.run({
                "diet_type": diet_type,
                "allergies": allergies,
                "cooking_preference": cooking_preference,
                "calories": calories,
                "goal": goal,
                "meals": meals_text
            })
            
            # Display recommendation based on preference
            st.header("Your 7-Day Meal Plan" if plan_type == "Full Week Meal Plan" else "Your Meal Recommendations")
            
            if display_preference == "Text format" or display_preference == "Both text and table":
                st.write(recommendation)
            
            # Parse and display as table if requested
            if display_preference == "Table format" or display_preference == "Both text and table":
                st.subheader("Recommendation Summary Table")
                
                try:
                    # Parse the recommendation text into a dataframe
                    if plan_type == "Full Week Meal Plan":
                        # Initialize data structure for weekly meal plan
                        meal_data = []
                        current_day = None
                        
                        # Parse text line by line
                        for line in recommendation.split('\n'):
                            line = line.strip()
                            
                            # Skip empty lines
                            if not line:
                                continue
                                
                            # Check if this is a day header
                            if line.startswith('Day') or line.lower().startswith('monday') or line.lower().startswith('tuesday') or line.lower().startswith('wednesday') or line.lower().startswith('thursday') or line.lower().startswith('friday') or line.lower().startswith('saturday') or line.lower().startswith('sunday'):
                                current_day = line.split(':')[0].strip()
                                continue
                                
                            # Check if this is a meal line
                            meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
                            if any(line.lower().startswith(f"- {meal_type}") for meal_type in meal_types) or any(line.lower().startswith(f"{meal_type}:") for meal_type in meal_types):
                                if current_day:
                                    # Extract meal type and details
                                    for meal_type in meal_types:
                                        if line.lower().startswith(f"- {meal_type}") or line.lower().startswith(f"{meal_type}:"):
                                            meal_info = line.split(':', 1)[1].strip() if ':' in line else line.split('-', 2)[2].strip()
                                            # Try to extract calories if present
                                            calories_info = ""
                                            if '(' in meal_info and ')' in meal_info and 'calories' in meal_info.lower():
                                                calories_parts = meal_info.split('(')
                                                for part in calories_parts:
                                                    if 'calories' in part.lower() and ')' in part:
                                                        calories_info = part.split(')')[0].strip()
                                                        break
                                            
                                            meal_data.append({
                                                'Day': current_day,
                                                'Meal Type': meal_type.capitalize(),
                                                'Description': meal_info,
                                                'Calories': calories_info
                                            })
                                            break
                        
                        # Create and display dataframe
                        if meal_data:
                            meal_df = pd.DataFrame(meal_data)
                            st.dataframe(meal_df, use_container_width=True)
                        else:
                            st.warning("Could not parse meal plan into table format. Please view the text recommendation.")
                    
                    else:  # Single meal recommendations
                        # Initialize data for single recommendations
                        recs_data = []
                        current_rec = None
                        rec_details = {}
                        
                        # Parse recommendation sections
                        for line in recommendation.split('\n'):
                            line = line.strip()
                            
                            # Skip empty lines
                            if not line:
                                continue
                                
                            # Check if this is a recommendation header
                            if line.startswith('Recommendation') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                                # Save previous recommendation if exists
                                if rec_details and current_rec:
                                    recs_data.append(rec_details)
                                
                                # Start new recommendation
                                current_rec = line
                                rec_details = {'Recommendation': current_rec}
                                continue
                            
                            # Extract details for current recommendation
                            if current_rec and ':' in line:
                                key, value = line.split(':', 1)
                                key = key.strip().strip('-').strip()
                                value = value.strip()
                                rec_details[key] = value
                        
                        # Add the last recommendation
                        if rec_details and current_rec:
                            recs_data.append(rec_details)
                        
                        # Create and display dataframe
                        if recs_data:
                            recs_df = pd.DataFrame(recs_data)
                            st.dataframe(recs_df, use_container_width=True)
                        else:
                            st.warning("Could not parse recommendations into table format. Please view the text recommendation.")
                
                except Exception as e:
                    st.warning(f"Could not format as table: {str(e)}. Please view the text recommendation.")
            
            # Show the top meals that were considered
            st.subheader("Top Meal Matches")
            for i, doc in enumerate(results[:5]):  # Show at most 5 matches
                with st.expander(f"Meal {i+1}: {doc.metadata['name']}"):
                    st.write(doc.page_content)
            
            # Add reference note for weekly plan
            if plan_type == "Full Week Meal Plan":
                st.subheader("Meal Plan Reference")
                st.write("This plan is based on your preferences and nutritional needs. Adjust portion sizes as needed to meet your exact calorie targets.")
                
        except Exception as e:
            st.error(f"An error occurred while generating recommendations: {str(e)}")
            if "openai" in str(e).lower():
                st.warning("There may be an issue with the OpenAI API key or connection.")
            elif "api key" in str(e).lower():
                st.warning("Please check that your API keys are entered correctly.")

# Add data collection links and information in the sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Recipe Database")
db_status = "Available ✓" if os.path.exists('meal_recipes.db') else "Not Found ✗"
st.sidebar.write(f"Database status: {db_status}")

if not os.path.exists('meal_recipes.db'):
    st.sidebar.warning("Database not found. App will use sample data if available.")
    
    if st.sidebar.button("Run Data Collection Tool"):
        st.sidebar.info("Please run 'python database.py' in your terminal to collect recipe data.")
        st.sidebar.code("python database.py", language="bash")
else:
    # Show database update option
    if st.sidebar.button("Update Existing Recipe Data"):
        st.sidebar.info("Please run 'python update_existing_data.py' in your terminal to update existing recipes.")
        st.sidebar.code("python update_existing_data.py", language="bash")

# Add information about the app
st.sidebar.markdown("---")
st.sidebar.subheader("About")
st.sidebar.info(
    "This meal recommendation system uses AI to provide personalized meal suggestions "
    "based on your dietary preferences, restrictions, cooking preferences, and nutritional goals."
)

if __name__ == "__main__":
    # No setup code needed here as everything is handled when the app runs
    pass
