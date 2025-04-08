import MealRecommendationForm from "@/components/meal-recommendation-form"
import { Toaster } from "@/components/ui/toaster"
import { Utensils } from "lucide-react"

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-primary/5 via-background to-secondary/5">
      <div className="container mx-auto px-4 py-12">
        <header className="mb-12 text-center">
          <div className="inline-flex items-center justify-center p-4 mb-4 bg-primary/10 rounded-full">
            <Utensils className="h-10 w-10 text-primary" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl mb-3 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Expert Meal Recommendation System
          </h1>
          <p className="mt-4 text-xl text-muted-foreground max-w-2xl mx-auto">
            Get tailored meal suggestions based on your dietary preferences, calorie requirements, and nutritional goals
          </p>
        </header>

        <div className="mx-auto max-w-4xl">
          <MealRecommendationForm />
        </div>
      </div>
      <Toaster />
    </div>
  )
}
