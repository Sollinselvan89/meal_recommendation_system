"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Settings, Key, Save, Check } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

export default function ApiKeySettings() {
  const { toast } = useToast()
  const [openAIKey, setOpenAIKey] = useState("")
  const [spoonacularKey, setSpoonacularKey] = useState("")
  const [isSaved, setIsSaved] = useState(false)

  const saveKeys = () => {
    // In a real app, you'd store these securely
    // For this demo, we'll just use localStorage
    if (openAIKey) {
      localStorage.setItem("openai_api_key", openAIKey)
      // In a real app, you'd set this in an environment variable
      // This is just for demonstration
      ;(window as any).OPENAI_API_KEY = openAIKey
    }

    if (spoonacularKey) {
      localStorage.setItem("spoonacular_api_key", spoonacularKey)
      // In a real app, you'd set this in an environment variable
      ;(window as any).SPOONACULAR_API_KEY = spoonacularKey
    }

    setIsSaved(true)
    setTimeout(() => setIsSaved(false), 2000)

    toast({
      title: "Settings saved",
      description: "Your API keys have been saved successfully.",
      variant: "default",
    })
  }

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon" className="bg-white/80 backdrop-blur-sm">
          <Settings className="h-4 w-4" />
          <span className="sr-only">Settings</span>
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Key className="h-5 w-5 text-primary" />
            API Settings
          </SheetTitle>
          <SheetDescription>Configure your API keys for the meal recommendation system.</SheetDescription>
        </SheetHeader>
        <div className="grid gap-6 py-6">
          <div className="space-y-3">
            <Label htmlFor="openai-key" className="flex items-center gap-2 font-medium">
              <Key className="h-4 w-4 text-primary" />
              OpenAI API Key
            </Label>
            <Input
              id="openai-key"
              type="password"
              placeholder="sk-..."
              value={openAIKey}
              onChange={(e) => setOpenAIKey(e.target.value)}
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground">Required for generating personalized recommendations.</p>
          </div>
          <div className="space-y-3">
            <Label htmlFor="spoonacular-key" className="flex items-center gap-2 font-medium">
              <Key className="h-4 w-4 text-primary" />
              Spoonacular API Key
            </Label>
            <Input
              id="spoonacular-key"
              type="password"
              placeholder="Enter your Spoonacular API key"
              value={spoonacularKey}
              onChange={(e) => setSpoonacularKey(e.target.value)}
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground">Used for fetching additional recipe data.</p>
          </div>
          <Button onClick={saveKeys} className="w-full flex items-center gap-2">
            {isSaved ? (
              <>
                <Check className="h-4 w-4" />
                Saved Successfully
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                Save Settings
              </>
            )}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}
