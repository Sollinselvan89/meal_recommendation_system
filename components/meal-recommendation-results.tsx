"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Utensils, Calendar, BarChart3, FileText } from "lucide-react"

interface MealRecommendationResultsProps {
  recommendation: string
  displayPreference: "Text format" | "Table format" | "Both text and table"
  planType: "Single Meal Recommendation" | "Full Week Meal Plan"
}

interface MealData {
  name: string
  calories: string
  protein?: string
  carbs?: string
  fat?: string
  ingredients?: string
  cookingTime?: string
  cookingRequired?: string
  supportsGoal?: string
}

interface DayMealData {
  day: string
  mealType: string
  description: string
  calories: string
}

export default function MealRecommendationResults({
  recommendation,
  displayPreference,
  planType,
}: MealRecommendationResultsProps) {
  const [parsedData, setParsedData] = useState<MealData[] | DayMealData[]>([])
  const [activeTab, setActiveTab] = useState<string>(displayPreference === "Table format" ? "table" : "text")

  useEffect(() => {
    if (displayPreference === "Text format") {
      setActiveTab("text")
    } else if (displayPreference === "Table format") {
      setActiveTab("table")
    }

    // Parse recommendation text into structured data
    try {
      if (planType === "Full Week Meal Plan") {
        parseWeeklyPlan(recommendation)
      } else {
        parseSingleMealRecommendation(recommendation)
      }
    } catch (error) {
      console.error("Error parsing recommendation:", error)
    }
  }, [recommendation, displayPreference, planType])

  const parseWeeklyPlan = (text: string) => {
    const mealData: DayMealData[] = []
    let currentDay: string | null = null

    // Split by lines and process
    const lines = text.split("\n")
    for (const line of lines) {
      const trimmedLine = line.trim()
      if (!trimmedLine) continue

      // Check if this is a day header
      if (
        trimmedLine.startsWith("Day") ||
        /^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)/i.test(trimmedLine)
      ) {
        currentDay = trimmedLine.split(":")[0].trim()
        continue
      }

      // Check if this is a meal line
      const mealTypes = ["breakfast", "lunch", "dinner", "snack"]
      for (const mealType of mealTypes) {
        if (
          trimmedLine.toLowerCase().startsWith(`- ${mealType}`) ||
          trimmedLine.toLowerCase().startsWith(`${mealType}:`)
        ) {
          if (currentDay) {
            // Extract meal info
            let mealInfo = ""
            if (trimmedLine.includes(":")) {
              mealInfo = trimmedLine.split(":", 2)[1].trim()
            } else if (trimmedLine.includes("-")) {
              const parts = trimmedLine.split("-")
              if (parts.length > 1) {
                mealInfo = parts.slice(1).join("-").trim()
              }
            }

            // Try to extract calories if present
            let caloriesInfo = ""
            if (mealInfo.includes("(") && mealInfo.includes(")") && mealInfo.toLowerCase().includes("calories")) {
              const caloriesParts = mealInfo.split("(")
              for (const part of caloriesParts) {
                if (part.toLowerCase().includes("calories") && part.includes(")")) {
                  caloriesInfo = part.split(")")[0].trim()
                  break
                }
              }
            }

            mealData.push({
              day: currentDay,
              mealType: mealType.charAt(0).toUpperCase() + mealType.slice(1),
              description: mealInfo,
              calories: caloriesInfo,
            })
            break
          }
        }
      }
    }

    setParsedData(mealData)
  }

  const parseSingleMealRecommendation = (text: string) => {
    const mealData: MealData[] = []
    let currentMeal: MealData | null = null

    // Split by lines and process
    const lines = text.split("\n")
    for (const line of lines) {
      const trimmedLine = line.trim()
      if (!trimmedLine) continue

      // Check if this is a recommendation header
      if (trimmedLine.startsWith("Recommendation") || /^\d+\./.test(trimmedLine)) {
        if (currentMeal && Object.keys(currentMeal).length > 1) {
          mealData.push(currentMeal)
        }
        currentMeal = { name: trimmedLine, calories: "" }
        continue
      }

      // Extract details for current meal
      if (currentMeal && trimmedLine.includes(":")) {
        const [key, value] = trimmedLine.split(":", 2)
        const cleanKey = key.trim().replace(/^[-•]/, "").trim().toLowerCase()

        if (cleanKey === "name") {
          currentMeal.name = value.trim()
        } else if (cleanKey === "calories") {
          currentMeal.calories = value.trim()
        } else if (cleanKey === "protein") {
          currentMeal.protein = value.trim()
        } else if (cleanKey === "carbs") {
          currentMeal.carbs = value.trim()
        } else if (cleanKey === "fat") {
          currentMeal.fat = value.trim()
        } else if (cleanKey === "key ingredients") {
          currentMeal.ingredients = value.trim()
        } else if (cleanKey === "cooking time") {
          currentMeal.cookingTime = value.trim()
        } else if (cleanKey === "cooking required") {
          currentMeal.cookingRequired = value.trim()
        } else if (cleanKey === "supports goal") {
          currentMeal.supportsGoal = value.trim()
        }
      }
    }

    // Add the last meal
    if (currentMeal && Object.keys(currentMeal).length > 1) {
      mealData.push(currentMeal)
    }

    setParsedData(mealData)
  }

  const renderWeeklyPlanTable = () => {
    const data = parsedData as DayMealData[]
    if (!data.length) return <p>No data available</p>

    // Group by day
    const dayGroups: { [key: string]: DayMealData[] } = {}
    data.forEach((item) => {
      if (!dayGroups[item.day]) {
        dayGroups[item.day] = []
      }
      dayGroups[item.day].push(item)
    })

    return (
      <div className="space-y-6">
        {Object.entries(dayGroups).map(([day, meals]) => (
          <div key={day} className="rounded-lg border shadow-sm overflow-hidden">
            <div className="border-b bg-muted/50 px-4 py-3 font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4 text-primary" />
              <h3 className="font-semibold">{day}</h3>
            </div>
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/20">
                  <TableHead className="w-[150px]">Meal</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="w-[120px] text-right">Calories</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {meals.map((meal, idx) => (
                  <TableRow key={`${day}-${meal.mealType}-${idx}`} className="hover:bg-muted/30 transition-colors">
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Utensils className="h-4 w-4 text-primary" />
                        {meal.mealType}
                      </div>
                    </TableCell>
                    <TableCell>{meal.description}</TableCell>
                    <TableCell className="text-right font-medium">
                      {meal.calories && (
                        <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">
                          {meal.calories}
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ))}
      </div>
    )
  }

  const renderSingleMealTable = () => {
    const data = parsedData as MealData[]
    if (!data.length) return <p>No data available</p>

    return (
      <Table className="border rounded-lg overflow-hidden shadow-sm">
        <TableHeader className="bg-muted/30">
          <TableRow>
            <TableHead>Meal</TableHead>
            <TableHead>Calories</TableHead>
            <TableHead>Protein</TableHead>
            <TableHead>Carbs</TableHead>
            <TableHead>Fat</TableHead>
            <TableHead>Cooking Required</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((meal, idx) => (
            <TableRow key={idx} className="hover:bg-muted/30 transition-colors">
              <TableCell className="font-medium">{meal.name}</TableCell>
              <TableCell>
                <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">
                  {meal.calories}
                </Badge>
              </TableCell>
              <TableCell>{meal.protein || "-"}</TableCell>
              <TableCell>{meal.carbs || "-"}</TableCell>
              <TableCell>{meal.fat || "-"}</TableCell>
              <TableCell>{meal.cookingRequired || "-"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    )
  }

  return (
    <Card className="border-2 border-primary/10 shadow-lg overflow-hidden">
      <CardHeader className="bg-gradient-to-r from-primary/10 to-secondary/10">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-primary" />
          <CardTitle>
            {planType === "Full Week Meal Plan" ? "Your 7-Day Meal Plan" : "Your Meal Recommendations"}
          </CardTitle>
        </div>
        <CardDescription>Personalized recommendations based on your preferences</CardDescription>
      </CardHeader>
      <CardContent className="pt-6">
        {displayPreference === "Both text and table" ? (
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-4 grid w-full grid-cols-2">
              <TabsTrigger value="text" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Text Format
              </TabsTrigger>
              <TabsTrigger value="table" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Table Format
              </TabsTrigger>
            </TabsList>
            <TabsContent value="text" className="space-y-4">
              <div className="prose max-w-none dark:prose-invert bg-muted/20 p-6 rounded-lg border">
                {recommendation.split("\n").map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </div>
            </TabsContent>
            <TabsContent value="table">
              {planType === "Full Week Meal Plan" ? renderWeeklyPlanTable() : renderSingleMealTable()}
            </TabsContent>
          </Tabs>
        ) : displayPreference === "Text format" ? (
          <div className="prose max-w-none dark:prose-invert bg-muted/20 p-6 rounded-lg border">
            {recommendation.split("\n").map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        ) : (
          <div>{planType === "Full Week Meal Plan" ? renderWeeklyPlanTable() : renderSingleMealTable()}</div>
        )}
      </CardContent>
    </Card>
  )
}
