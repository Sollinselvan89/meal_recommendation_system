import numpy as np
from openai import OpenAI
import os

def generate_embedding(text, client=None):
    """Generate embedding for text using OpenAI API"""
    if not client:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Return random embedding for demo if no API key
            return np.random.rand(1536).tolist()
        client = OpenAI(api_key=api_key)
    
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return random embedding as fallback
        return np.random.rand(1536).tolist()

def find_similar_recipes(query, recipes, top_n=5):
    """Find similar recipes based on query (simplified version)"""
    # For demo purposes, just return a subset of recipes
    # In a real implementation, this would use embeddings and similarity search
    if recipes.empty:
        return []
    
    # Simple keyword matching for demo
    query = query.lower()
    matching_recipes = []
    
    for _, recipe in recipes.iterrows():
        score = 0
        # Check name
        if query in recipe['name'].lower():
            score += 3
        
        # Check ingredients
        if 'ingredients' in recipe and query in recipe['ingredients'].lower():
            score += 2
            
        # Check diet tags
        if 'diet_tags' in recipe and query in recipe['diet_tags'].lower():
            score += 1
            
        if score > 0:
            matching_recipes.append((recipe, score))
    
    # Sort by score and return top N
    matching_recipes.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in matching_recipes[:top_n]]
