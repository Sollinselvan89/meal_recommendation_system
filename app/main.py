import streamlit as st
import pandas as pd
import os
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from rules import FoodRule

# OpenAI API key handling
if "OPENAI_API_KEY" not in os.environ:
    api_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    else:
        st.warning("Please enter your OpenAI API key to get personalized recommendations.")
        st.stop()

# Load data and create food documents
@st.cache_data
def load_food_data():
    df = pd.read_csv('data/sample_foods.csv')
    documents = []
    
    for _, row in df.iterrows():
        content = f"Name: {row['name']}\n"
        content += f"Calories: {row['calories']}\n"
        content += f"Protein: {row['protein']}g\n"
        content += f"Carbs: {row['carbs']}g\n"
        content += f"Fat: {row['fat']}g\n"
        content += f"Diet Tags: {row['diet_tags']}\n"
        
        doc = Document(
            page_content=content,
            metadata={
                "name": row['name'],
                "calories": row['calories'],
                "diet_tags": row['diet_tags'],
            }
        )
        documents.append(doc)
    
    return df, documents

# Create vector store
@st.cache_resource
def get_vector_store(documents):
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(documents, embeddings)
    return vector_store

# App Title and Description
st.title("Personalized Meal Recommendation System")
st.write("Welcome to our expert system that provides meal recommendations based on your preferences!")

# User Input Form
st.header("Your Preferences")
diet_type = st.selectbox("Select your diet type:", ["No restrictions", "Vegetarian", "Vegan", "Keto", "Gluten-free"])
allergies = st.multiselect("Select any allergies:", ["None", "Nuts", "Dairy", "Shellfish", "Eggs", "Soy", "Wheat"])
calories = st.slider("Daily calorie target:", 1000, 3000, 2000)
goal = st.text_input("Your nutrition goal (e.g., weight loss, muscle gain):")

if st.button("Get Recommendations"):
    # Show a spinner while processing
    with st.spinner("Generating your personalized recommendation..."):
        # Load data
        df, documents = load_food_data()
        vector_store = get_vector_store(documents)
        
        # Apply rules to filter data
        rule_engine = FoodRule()
        foods_df = df.to_dict('records')
        user_preferences = {
            'diet_type': diet_type,
            'allergies': allergies,
            'calories': calories,
            'goal': goal
        }
        
        filtered_foods = rule_engine.filter_foods(foods_df, user_preferences)
        
        # Create a query based on user preferences
        query = f"I need a meal that is {diet_type.lower()} friendly"
        if "None" not in allergies:
            query += f", without {', '.join(allergies).lower()}"
        query += f", around {calories} calories"
        if goal:
            query += f" for {goal.lower()}"
        
        # Get relevant meals from vector database
        results = vector_store.similarity_search(query, k=3)
        
        # Use LLM to generate personalized recommendation
        template = """
        Based on the user's preferences:
        - Diet: {diet_type}
        - Allergies: {allergies}
        - Calorie target: {calories}
        - Goal: {goal}
        
        And these potential meals:
        {meals}
        
        Provide a personalized meal recommendation with explanation why it suits their needs.
        Include specific nutritional benefits that align with their goal.
        Reference specific details from the meal data to support your recommendation.
        """
        
        prompt = PromptTemplate(
            input_variables=["diet_type", "allergies", "calories", "goal", "meals"],
            template=template,
        )
        
        # Format meals for the prompt
        meals_text = "\n\n".join([doc.page_content for doc in results])
        
        # Create a chain
        llm = OpenAI(temperature=0.7)
        chain = LLMChain(llm=llm, prompt=prompt)
        
        # Generate recommendation
        recommendation = chain.run({
            "diet_type": diet_type,
            "allergies": allergies,
            "calories": calories,
            "goal": goal,
            "meals": meals_text
        })
        
        # Display recommendation
        st.header("Your Recommendation")
        st.write(recommendation)
        
        # Show the top meals that were considered
        st.subheader("Top Meal Matches")
        for i, doc in enumerate(results):
            with st.expander(f"Meal {i+1}: {doc.metadata['name']}"):
                st.write(doc.page_content)