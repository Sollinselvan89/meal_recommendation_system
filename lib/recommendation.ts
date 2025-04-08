import { generateText } from "ai"
import { openai } from "@ai-sdk/openai"

// Define types
type DietType =
  | "No restrictions"
  | "Vegetarian"
  | "Vegan"
  | "Keto"
  | "Gluten-free"
  | "Paleo"
  | "Whole30"
  | "Pescatarian"
  | "Dairy-free"

type CookingPreference = "Any" | "Cooked meals" | "No-cook/quick meals"

type PlanType = "Single Meal Recommendation" | "Full Week Meal Plan"

type DisplayPreference = "Text format" | "Table format" | "Both text and table"

type Allergen = "Nuts" | "Dairy" | "Shellfish" | "Eggs" | "Soy" | "Wheat" | "Fish" | "Gluten"

interface UserPreferences {
  dietType: DietType
  allergies: Allergen[]
  cookingPreference: CookingPreference
  calories: number
  goal: string
  planType: PlanType
  displayPreference: DisplayPreference
}

// Expert system rules for calorie distribution
const calorieDistributionRules = {
  breakfast: {
    low: { min: 250, max: 350, percentage: 0.2 },
    medium: { min: 350, max: 450, percentage: 0.25 },
    high: { min: 450, max: 600, percentage: 0.3 },
  },
  lunch: {
    low: { min: 350, max: 450, percentage: 0.3 },
    medium: { min: 450, max: 550, percentage: 0.35 },
    high: { min: 550, max: 700, percentage: 0.35 },
  },
  dinner: {
    low: { min: 350, max: 450, percentage: 0.3 },
    medium: { min: 450, max: 550, percentage: 0.35 },
    high: { min: 550, max: 700, percentage: 0.35 },
  },
  snack: {
    low: { min: 100, max: 150, percentage: 0.1 },
    medium: { min: 150, max: 200, percentage: 0.1 },
    high: { min: 200, max: 250, percentage: 0.1 },
  },
}

// Expert system rules for macronutrient distribution based on goals
const macroDistributionRules = {
  "weight loss": {
    protein: { min: 0.3, max: 0.4 },
    carbs: { min: 0.2, max: 0.3 },
    fat: { min: 0.3, max: 0.4 },
  },
  "muscle gain": {
    protein: { min: 0.3, max: 0.4 },
    carbs: { min: 0.4, max: 0.5 },
    fat: { min: 0.2, max: 0.3 },
  },
  maintenance: {
    protein: { min: 0.25, max: 0.35 },
    carbs: { min: 0.4, max: 0.5 },
    fat: { min: 0.25, max: 0.35 },
  },
  "heart health": {
    protein: { min: 0.25, max: 0.35 },
    carbs: { min: 0.45, max: 0.55 },
    fat: { min: 0.2, max: 0.3 },
  },
}

// Helper function to determine calorie category
function getCalorieCategory(calories: number): "low" | "medium" | "high" {
  if (calories < 1800) return "low"
  if (calories < 2400) return "medium"
  return "high"
}

// Helper function to determine goal category
function getGoalCategory(goal: string): keyof typeof macroDistributionRules {
  goal = goal.toLowerCase()
  if (goal.includes("weight loss") || goal.includes("lose weight") || goal.includes("fat loss")) {
    return "weight loss"
  }
  if (goal.includes("muscle") || goal.includes("strength") || goal.includes("gain")) {
    return "muscle gain"
  }
  if (goal.includes("heart") || goal.includes("cardio") || goal.includes("cholesterol")) {
    return "heart health"
  }
  return "maintenance"
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
    mealType: "breakfast",
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
    mealType: "lunch",
  },
  {
    name: "Salmon with Roasted Vegetables",
    calories: 520,
    protein: 40,
    carbs: 18,
    fat: 30,
    ingredients: "Salmon fillet, broccoli, carrots, bell peppers, olive oil",
    cookingStatus: "cooked",
    category: "pescatarian,gluten free,dairy free",
    mealType: "dinner",
  },
  {
    name: "Keto Cauliflower Crust Pizza",
    calories: 480,
    protein: 25,
    carbs: 10,
    fat: 38,
    ingredients: "Cauliflower, mozzarella cheese, eggs, tomato sauce, toppings",
    cookingStatus: "cooked",
    category: "keto,gluten free",
    mealType: "dinner",
  },
  {
    name: "Vegan Buddha Bowl",
    calories: 420,
    protein: 15,
    carbs: 60,
    fat: 16,
    ingredients: "Quinoa, chickpeas, avocado, sweet potato, kale, tahini dressing",
    cookingStatus: "cooked",
    category: "vegan,vegetarian,gluten free,dairy free",
    mealType: "lunch",
  },
  {
    name: "Paleo Beef and Vegetable Stir Fry",
    calories: 490,
    protein: 32,
    carbs: 20,
    fat: 30,
    ingredients: "Grass-fed beef, broccoli, carrots, bell peppers, coconut aminos",
    cookingStatus: "cooked",
    category: "paleo,gluten free,dairy free",
    mealType: "dinner",
  },
  {
    name: "Overnight Oats with Chia Seeds",
    calories: 350,
    protein: 12,
    carbs: 45,
    fat: 14,
    ingredients: "Rolled oats, chia seeds, almond milk, maple syrup, cinnamon, berries",
    cookingStatus: "uncooked",
    category: "vegetarian,vegan",
    mealType: "breakfast",
  },
  {
    name: "Protein Smoothie Bowl",
    calories: 380,
    protein: 25,
    carbs: 40,
    fat: 10,
    ingredients: "Protein powder, banana, berries, almond milk, granola, chia seeds",
    cookingStatus: "uncooked",
    category: "vegetarian,gluten free",
    mealType: "breakfast",
  },
  {
    name: "Quinoa Salad with Roasted Vegetables",
    calories: 410,
    protein: 12,
    carbs: 55,
    fat: 18,
    ingredients: "Quinoa, roasted vegetables, feta cheese, olive oil, lemon juice",
    cookingStatus: "cooked",
    category: "vegetarian,gluten free",
    mealType: "lunch",
  },
  {
    name: "Lentil Soup with Vegetables",
    calories: 320,
    protein: 18,
    carbs: 45,
    fat: 8,
    ingredients: "Lentils, carrots, celery, onion, tomatoes, vegetable broth",
    cookingStatus: "cooked",
    category: "vegetarian,vegan,gluten free",
    mealType: "lunch",
  },
  {
    name: "Baked Cod with Herb Crust",
    calories: 280,
    protein: 35,
    carbs: 10,
    fat: 12,
    ingredients: "Cod fillet, herbs, breadcrumbs, lemon, olive oil",
    cookingStatus: "cooked",
    category: "pescatarian",
    mealType: "dinner",
  },
  {
    name: "Turkey and Sweet Potato Chili",
    calories: 380,
    protein: 30,
    carbs: 35,
    fat: 12,
    ingredients: "Ground turkey, sweet potatoes, beans, tomatoes, chili spices",
    cookingStatus: "cooked",
    category: "gluten free,dairy free",
    mealType: "dinner",
  },
]

// Expert system function to filter meals based on calorie requirements
function filterMealsByCalories(meals: any[], targetCalories: number, mealType: string) {
  const calorieCategory = getCalorieCategory(targetCalories)
  const calorieRule = calorieDistributionRules[mealType as keyof typeof calorieDistributionRules][calorieCategory]

  // Calculate target calories for this meal type
  const mealTargetCalories = targetCalories * calorieRule.percentage

  // Filter meals that are within 20% of the target calories for this meal type
  return meals.filter((meal) => {
    const mealCalories = meal.calories
    const lowerBound = mealTargetCalories * 0.8
    const upperBound = mealTargetCalories * 1.2

    return mealCalories >= lowerBound && mealCalories <= upperBound && meal.mealType === mealType
  })
}

// Expert system function to filter meals based on diet type
function filterMealsByDietType(meals: any[], dietType: DietType) {
  if (dietType === "No restrictions") {
    return meals
  }

  return meals.filter((meal) => {
    const category = meal.category.toLowerCase()
    return category.includes(dietType.toLowerCase())
  })
}

// Expert system function to filter meals based on cooking preference
function filterMealsByCookingPreference(meals: any[], cookingPreference: CookingPreference) {
  if (cookingPreference === "Any") {
    return meals
  }

  const desiredStatus = cookingPreference === "Cooked meals" ? "cooked" : "uncooked"
  return meals.filter((meal) => meal.cookingStatus === desiredStatus)
}

// Expert system function to filter meals based on allergies
function filterMealsByAllergies(meals: any[], allergies: Allergen[]) {
  if (!allergies.length) {
    return meals
  }

  return meals.filter((meal) => {
    const ingredients = meal.ingredients.toLowerCase()
    return !allergies.some((allergy) => ingredients.includes(allergy.toLowerCase()))
  })
}

export async function generateRecommendation(preferences: UserPreferences): Promise<string> {
  try {
    // Apply expert system rules to filter meals
    let filteredMeals = [...sampleMeals]

    // Step 1: Filter by diet type
    filteredMeals = filterMealsByDietType(filteredMeals, preferences.dietType)

    // Step 2: Filter by cooking preference
    filteredMeals = filterMealsByCookingPreference(filteredMeals, preferences.cookingPreference)

    // Step 3: Filter by allergies
    filteredMeals = filterMealsByAllergies(filteredMeals, preferences.allergies)

    // Step 4: Group meals by type
    const breakfastMeals = filterMealsByCalories(filteredMeals, preferences.calories, "breakfast")
    const lunchMeals = filterMealsByCalories(filteredMeals, preferences.calories, "lunch")
    const dinnerMeals = filterMealsByCalories(filteredMeals, preferences.calories, "dinner")

    // Create a prompt based on user preferences and filtered meals
    const mealsText = filteredMeals
      .map(
        (meal) =>
          `Name: ${meal.name}\nCalories: ${meal.calories}\nProtein: ${meal.protein}g\nCarbs: ${meal.carbs}g\nFat: ${meal.fat}g\nIngredients: ${meal.ingredients}\nCooking Status: ${meal.cookingStatus}\nCategory: ${meal.category}\nMeal Type: ${meal.mealType}`,
      )
      .join("\n\n")

    // Get goal category for macronutrient distribution
    const goalCategory = getGoalCategory(preferences.goal)
    const macroRules = macroDistributionRules[goalCategory]

    // Create a prompt based on user preferences and expert system rules
    let prompt = `Based on the user's preferences:
- Diet: ${preferences.dietType}
- Allergies: ${preferences.allergies.length > 0 ? preferences.allergies.join(", ") : "None"}
- Cooking preference: ${preferences.cookingPreference}
- Calorie target: ${preferences.calories} calories per day
- Goal: ${preferences.goal || "Not specified"}

Expert System Rules Applied:
- Calorie Category: ${getCalorieCategory(preferences.calories)}
- Goal Category: ${goalCategory}
- Recommended Protein: ${Math.round(macroRules.protein.min * 100)}%-${Math.round(macroRules.protein.max * 100)}% of calories
- Recommended Carbs: ${Math.round(macroRules.carbs.min * 100)}%-${Math.round(macroRules.carbs.max * 100)}% of calories
- Recommended Fat: ${Math.round(macroRules.fat.min * 100)}%-${Math.round(macroRules.fat.max * 100)}% of calories

And using these filtered meals as inspiration:
${mealsText}

`

    // Add specific instructions based on plan type and display preference
    if (preferences.planType === "Full Week Meal Plan") {
      if (preferences.displayPreference === "Table format" || preferences.displayPreference === "Both text and table") {
        prompt += `Create a comprehensive 7-day meal plan (breakfast, lunch, dinner) that:
1. Strictly adheres to their dietary restrictions and avoids all allergens
2. Maintains daily calories around their target of ${preferences.calories}
3. Respects their cooking preference of ${preferences.cookingPreference}
4. Supports their goal of ${preferences.goal || "healthy eating"} with the recommended macronutrient distribution
5. Provides variety throughout the week

Return this in a structured format that can be easily converted to a table:
Day 1:
- Breakfast: [meal name] ([calories] calories) - [key ingredients]
- Lunch: [meal name] ([calories] calories) - [key ingredients]
- Dinner: [meal name] ([calories] calories) - [key ingredients]
- Daily Total: [total calories] calories

... and so on for all 7 days.

After the table data, provide a brief paragraph explaining how this meal plan supports the user's goal.`
      } else {
        prompt += `Create a comprehensive 7-day meal plan (breakfast, lunch, dinner) that:
1. Strictly adheres to their dietary restrictions and avoids all allergens
2. Maintains daily calories around their target of ${preferences.calories}
3. Respects their cooking preference of ${preferences.cookingPreference}
4. Supports their goal of ${preferences.goal || "healthy eating"} with the recommended macronutrient distribution
5. Provides variety throughout the week
6. Includes nutritional benefits of key meals

Format as a clear 7-day plan with brief explanations of how specific meals support their goals.`
      }
    } else {
      if (preferences.displayPreference === "Table format" || preferences.displayPreference === "Both text and table") {
        prompt += `Provide THREE personalized meal recommendations that can be formatted into a table.

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

After providing the structured data, add a brief paragraph summarizing how these meals collectively address the user's preferences and goals.`
      } else {
        prompt += `Provide THREE personalized meal recommendations with detailed explanations for each.
For each meal:
1. Name the meal and describe its key ingredients
2. Explain exactly how it matches the user's dietary needs and cooking preference
3. Detail the specific nutritional benefits that align with their goal
4. Mention calorie content and macronutrient breakdown

Make your recommendations varied and comprehensive.`
      }
    }

    // Generate recommendation using AI
    const { text } = await generateText({
      model: openai("gpt-3.5-turbo"),
      prompt: prompt,
      temperature: 0.7,
      maxTokens: 1500,
    })

    return text
  } catch (error) {
    console.error("Error generating recommendation:", error)
    throw new Error("Failed to generate meal recommendations")
  }
}
