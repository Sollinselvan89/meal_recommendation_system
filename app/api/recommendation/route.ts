import { NextResponse } from "next/server"
import { generateText } from "ai"
import { openai } from "@ai-sdk/openai"

export async function POST(request: Request) {
  try {
    const { preferences } = await request.json()

    if (!preferences) {
      return NextResponse.json({ error: "Missing user preferences" }, { status: 400 })
    }

    // Sample meal data for demonstration
    const sampleMeals = [
      {
        name: "Greek Yogurt Parfait with Berries",
        calories: 320,
        protein: 18,
        carbs: 42,
        fat: 8,
        ingredients: "Greek yogurt, mixed berries, honey, granola",
        cookingStatus: "uncooked",
        category: "vegetarian,gluten free",
      },
      {
        name: "Grilled Chicken Salad with Avocado",
        calories: 450,
        protein: 35,
        carbs: 12,
        fat: 28,
        ingredients: "Chicken breast, mixed greens, avocado, cherry tomatoes, olive oil",
        cookingStatus: "cooked",
        category: "gluten free,dairy free",
      },
      // Add more sample meals as needed
    ]

    const mealsText = sampleMeals
      .map(
        (meal) =>
          `Name: ${meal.name}\nCalories: ${meal.calories}\nProtein: ${meal.protein}g\nCarbs: ${meal.carbs}g\nFat: ${meal.fat}g\nIngredients: ${meal.ingredients}\nCooking Status: ${meal.cookingStatus}\nCategory: ${meal.category}`,
      )
      .join("\n\n")

    // Create a prompt based on user preferences
    let prompt = `Based on the user's preferences:
- Diet: ${preferences.dietType}
- Allergies: ${preferences.allergies.length > 0 ? preferences.allergies.join(", ") : "None"}
- Cooking preference: ${preferences.cookingPreference}
- Calorie target: ${preferences.calories} calories per day
- Goal: ${preferences.goal || "Not specified"}

And using these potential meals as inspiration:
${mealsText}

`

    // Add specific instructions based on plan type and display preference
    if (preferences.planType === "Full Week Meal Plan") {
      prompt += `Create a comprehensive 7-day meal plan (breakfast, lunch, dinner) that:
1. Strictly adheres to their dietary restrictions and avoids all allergens
2. Maintains daily calories around their target of ${preferences.calories}
3. Respects their cooking preference of ${preferences.cookingPreference}
4. Supports their goal of ${preferences.goal || "healthy eating"}
5. Provides variety throughout the week

Return this in a structured format that can be easily converted to a table.`
    } else {
      prompt += `Provide THREE personalized meal recommendations with detailed explanations for each.
For each meal:
1. Name the meal and describe its key ingredients
2. Explain exactly how it matches the user's dietary needs and cooking preference
3. Detail the specific nutritional benefits that align with their goal
4. Mention calorie content and macronutrient breakdown

Make your recommendations varied and comprehensive.`
    }

    // Generate recommendation using AI
    const { text } = await generateText({
      model: openai("gpt-3.5-turbo"),
      prompt: prompt,
      temperature: 0.7,
      maxTokens: 1500,
    })

    return NextResponse.json({ recommendation: text })
  } catch (error) {
    console.error("Error generating recommendation:", error)
    return NextResponse.json({ error: "Failed to generate meal recommendations" }, { status: 500 })
  }
}
