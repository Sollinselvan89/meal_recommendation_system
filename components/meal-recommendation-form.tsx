"use client"

import { useState } from "react"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Slider } from "@/components/ui/slider"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Checkbox } from "@/components/ui/checkbox"
import { Loader2, Utensils, Leaf, AlertTriangle, Target, Calendar, LayoutList } from "lucide-react"
import MealRecommendationResults from "./meal-recommendation-results"
import { generateRecommendation } from "@/lib/recommendation"

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

export default function MealRecommendationForm() {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [recommendation, setRecommendation] = useState<string | null>(null)
  const [preferences, setPreferences] = useState<UserPreferences>({
    dietType: "No restrictions",
    allergies: [],
    cookingPreference: "Any",
    calories: 2000,
    goal: "",
    planType: "Single Meal Recommendation",
    displayPreference: "Both text and table",
  })

  const dietTypes: DietType[] = [
    "No restrictions",
    "Vegetarian",
    "Vegan",
    "Keto",
    "Gluten-free",
    "Paleo",
    "Whole30",
    "Pescatarian",
    "Dairy-free",
  ]

  const allergens: Allergen[] = ["Nuts", "Dairy", "Shellfish", "Eggs", "Soy", "Wheat", "Fish", "Gluten"]

  const cookingPreferences: CookingPreference[] = ["Any", "Cooked meals", "No-cook/quick meals"]

  const handleAllergyToggle = (allergy: Allergen) => {
    setPreferences((prev) => {
      if (prev.allergies.includes(allergy)) {
        return {
          ...prev,
          allergies: prev.allergies.filter((item) => item !== allergy),
        }
      } else {
        return { ...prev, allergies: [...prev.allergies, allergy] }
      }
    })
  }

  const handleSubmit = async () => {
    setIsLoading(true)
    setRecommendation(null)

    try {
      // Check if OpenAI API key is available
      if (!process.env.NEXT_PUBLIC_OPENAI_API_KEY) {
        toast({
          title: "API Key Missing",
          description: "Please add your OpenAI API key in the settings.",
          variant: "destructive",
        })
        setIsLoading(false)
        return
      }

      const result = await generateRecommendation(preferences)
      setRecommendation(result)
    } catch (error) {
      console.error("Error generating recommendation:", error)
      toast({
        title: "Error",
        description: "Failed to generate meal recommendations. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Get calorie range description
  const getCalorieRangeDescription = (calories: number) => {
    if (calories < 1500) return "Low calorie diet"
    if (calories < 2000) return "Moderate calorie diet"
    if (calories < 2500) return "Standard calorie diet"
    return "High calorie diet"
  }

  return (
    <div className="space-y-8">
      <Card className="border-2 border-primary/10 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-primary/10 to-secondary/10">
          <div className="flex items-center gap-2">
            <Utensils className="h-6 w-6 text-primary" />
            <CardTitle>Your Preferences</CardTitle>
          </div>
          <CardDescription>Tell us about your dietary needs and goals</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-6">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Leaf className="h-4 w-4 text-primary" />
                  <Label htmlFor="diet-type" className="font-medium">
                    Diet Type
                  </Label>
                </div>
                <Select
                  value={preferences.dietType}
                  onValueChange={(value) => setPreferences({ ...preferences, dietType: value as DietType })}
                >
                  <SelectTrigger id="diet-type" className="w-full">
                    <SelectValue placeholder="Select diet type" />
                  </SelectTrigger>
                  <SelectContent>
                    {dietTypes.map((diet) => (
                      <SelectItem key={diet} value={diet}>
                        {diet}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-primary" />
                  <Label className="font-medium">Allergies</Label>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {allergens.map((allergy) => (
                    <div
                      key={allergy}
                      className="flex items-center space-x-2 rounded-md border p-3 hover:bg-muted/50 transition-colors"
                    >
                      <Checkbox
                        id={`allergy-${allergy}`}
                        checked={preferences.allergies.includes(allergy)}
                        onCheckedChange={() => handleAllergyToggle(allergy)}
                      />
                      <Label htmlFor={`allergy-${allergy}`} className="cursor-pointer">
                        {allergy}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Utensils className="h-4 w-4 text-primary" />
                  <Label htmlFor="cooking-preference" className="font-medium">
                    Cooking Preference
                  </Label>
                </div>
                <Select
                  value={preferences.cookingPreference}
                  onValueChange={(value) =>
                    setPreferences({
                      ...preferences,
                      cookingPreference: value as CookingPreference,
                    })
                  }
                >
                  <SelectTrigger id="cooking-preference" className="w-full">
                    <SelectValue placeholder="Select cooking preference" />
                  </SelectTrigger>
                  <SelectContent>
                    {cookingPreferences.map((pref) => (
                      <SelectItem key={pref} value={pref}>
                        {pref}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Target className="h-4 w-4 text-primary" />
                    <Label htmlFor="calories" className="font-medium">
                      Daily Calorie Target
                    </Label>
                  </div>
                  <span className="text-sm font-medium bg-primary/10 text-primary px-2 py-1 rounded-md">
                    {preferences.calories} cal
                  </span>
                </div>
                <Slider
                  id="calories"
                  min={1000}
                  max={3000}
                  step={50}
                  value={[preferences.calories]}
                  onValueChange={(value) => setPreferences({ ...preferences, calories: value[0] })}
                  className="py-4"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>1000</span>
                  <span className="text-primary font-medium">{getCalorieRangeDescription(preferences.calories)}</span>
                  <span>3000</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-primary" />
                  <Label htmlFor="goal" className="font-medium">
                    Nutrition Goal
                  </Label>
                </div>
                <Input
                  id="goal"
                  placeholder="e.g., weight loss, muscle gain, heart health"
                  value={preferences.goal}
                  onChange={(e) => setPreferences({ ...preferences, goal: e.target.value })}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-primary" />
                  <Label className="font-medium">What would you like to generate?</Label>
                </div>
                <Tabs
                  defaultValue="single"
                  value={preferences.planType === "Single Meal Recommendation" ? "single" : "weekly"}
                  onValueChange={(value) =>
                    setPreferences({
                      ...preferences,
                      planType: value === "single" ? "Single Meal Recommendation" : "Full Week Meal Plan",
                    })
                  }
                  className="w-full"
                >
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="single">Single Meal</TabsTrigger>
                    <TabsTrigger value="weekly">Weekly Plan</TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <LayoutList className="h-4 w-4 text-primary" />
                  <Label htmlFor="display-preference" className="font-medium">
                    Display Preference
                  </Label>
                </div>
                <Select
                  value={preferences.displayPreference}
                  onValueChange={(value) =>
                    setPreferences({
                      ...preferences,
                      displayPreference: value as DisplayPreference,
                    })
                  }
                >
                  <SelectTrigger id="display-preference" className="w-full">
                    <SelectValue placeholder="Select display preference" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Text format">Text format</SelectItem>
                    <SelectItem value="Table format">Table format</SelectItem>
                    <SelectItem value="Both text and table">Both text and table</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <Button
            onClick={handleSubmit}
            className="w-full mt-6 text-lg py-6 bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary transition-all duration-300 shadow-md hover:shadow-lg"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Generating your personalized meal plan...
              </>
            ) : (
              "Get Expert Recommendations"
            )}
          </Button>
        </CardContent>
      </Card>

      {recommendation && (
        <MealRecommendationResults
          recommendation={recommendation}
          displayPreference={preferences.displayPreference}
          planType={preferences.planType}
        />
      )}
    </div>
  )
}
