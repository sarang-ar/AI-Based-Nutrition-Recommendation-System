import { useState, useRef, useEffect } from "react";
import { Loader2, Send, Bot, User, ChefHat } from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { MealPlan } from "@/types/recipe";
import RecipeCard from "@/components/RecipeCard";
import BMIDisplay from "@/components/BMIDisplay";
import CaloriesDisplay from "@/components/CaloriesDisplay";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";

type Message = {
  role: "user" | "assistant";
  content: string;
  mealPlan?: MealPlan | null;
};

export default function ChatMealPlan() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I am your AI Nutrition Assistant 🥦. Tell me about your dietary goals, preferences (like vegetarian or budget-friendly), and physical details (age, weight, height, activity level). I'll generate a personalized meal plan for you!",
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8080/chat-meal-plan/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: data.explanation,
          mealPlan: data.meal_plan
        }
      ]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: "Oops! Something went wrong while generating your meal plan. Please make sure the backend server is running and your API key is correct."
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container flex h-[calc(100vh-4rem)] flex-col py-6">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
          <ChefHat className="h-6 w-6" />
        </div>
        <div>
          <h1 className="font-display text-2xl font-bold text-foreground">AI Nutrition Assistant</h1>
          <p className="text-sm text-muted-foreground">Chat to generate your perfect meal plan</p>
        </div>
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden shadow-md" style={{ boxShadow: "var(--shadow-card)" }}>
        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          <div className="flex flex-col gap-6 pb-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
                  {msg.role === "user" ? <User className="h-5 w-5" /> : <Bot className="h-5 w-5 text-primary" />}
                </div>
                <div className={`flex max-w-[85%] flex-col gap-3 ${msg.role === "user" ? "items-end" : "items-start"}`}>
                  <div className={`rounded-2xl px-5 py-3 shadow-sm ${msg.role === "user" ? "bg-primary text-primary-foreground rounded-tr-sm" : "bg-muted/50 text-foreground rounded-tl-sm border"}`}>
                    <ReactMarkdown className="prose prose-sm dark:prose-invert max-w-none">
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                  
                  {/* Render Meal Plan if it exists */}
                  {msg.mealPlan && (
                    <div className="w-full animate-fade-in space-y-6 rounded-xl border bg-card p-5 shadow-sm mt-2">
                      <div className="grid gap-4 sm:grid-cols-2">
                        <BMIDisplay bmi={msg.mealPlan.bmi} />
                        <CaloriesDisplay maintainCalories={msg.mealPlan.maintain_calories} />
                      </div>
                      
                      <div className="space-y-6">
                        {msg.mealPlan.meals.map((meal) => (
                          <div key={meal.meal_name}>
                            <h3 className="mb-3 font-display text-lg font-semibold capitalize text-primary flex items-center gap-2">
                              {meal.meal_name}
                            </h3>
                            <div className="grid gap-3 sm:grid-cols-2">
                              {meal.recipes.map((recipe) => (
                                <RecipeCard key={recipe.Name} recipe={recipe} />
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex gap-4 flex-row">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                  <Bot className="h-5 w-5 text-primary" />
                </div>
                <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm border bg-muted/50 px-5 py-4 text-foreground shadow-sm">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  <span className="text-sm animate-pulse">Thinking & generating plan...</span>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="border-t bg-background p-4">
          <form onSubmit={handleSend} className="mx-auto flex max-w-4xl items-center gap-3">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="E.g., I'm a 25yo male, 75kg, looking for a high protein vegetarian diet..."
              className="flex-1 rounded-full px-5 py-6 shadow-sm focus-visible:ring-primary"
              disabled={loading}
            />
            <Button 
              type="submit" 
              size="icon" 
              className="h-12 w-12 shrink-0 rounded-full shadow-sm transition-transform hover:scale-105 active:scale-95"
              disabled={!input.trim() || loading}
            >
              <Send className="h-5 w-5" />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
