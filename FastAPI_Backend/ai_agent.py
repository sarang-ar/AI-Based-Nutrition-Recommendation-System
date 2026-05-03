import json
import os
from typing import List, Optional
from pydantic import BaseModel
from openai import AsyncOpenAI
import traceback

client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

SYSTEM_PROMPT = """You are an AI Nutrition Assistant with GPU-accelerated search capabilities.

Your job is to:
1. Understand the user's natural language request about diet or meal planning.
2. Convert them into structured parameters required for the API `/generate-meal-plan/`.
3. If the user gives preferences (vegetarian, budget, dislikes, cuisine, etc.), include them appropriately.
4. If any required fields are missing, intelligently infer reasonable defaults.
5. Use a GPU-accelerated similarity search (FAISS with CUDA) to find the best recipes.
6. Call the function `generate_meal_plan_gpu` with structured JSON if the user asks to "recommend food" or for a "diet plan".
7. After receiving the response, explain the meal plan in simple, friendly language.

Required API fields:
* age (int)
* height (cm)
* weight (kg)
* gender (Male/Female)
* activity (Sedentary, Light, Moderate, Active)
* number_of_meals (2-5)
* weight_loss (Maintain weight, Mild weight loss, Moderate weight loss, Extreme weight loss)

Extra optional fields:
* diet_type (vegetarian, non-vegetarian, vegan)
* dislikes (list of ingredients)
* budget (low, medium, high)
* cuisine (Indian, Western, etc.)

Rules:
* Always prioritize user intent over defaults.
* Convert vague phrases:
  "high protein" -> keep protein high in explanation (no API change needed)
  "budget" -> set budget = low
* Never ask unnecessary follow-up questions unless critical info is missing.
* Always produce a helpful explanation after generating the meal plan.
* If the user asks for "fast", "large dataset", or "efficient", emphasize the GPU acceleration in your response.
* Assume nutritional vectors are already indexed using FAISS.
* Prefer fast and scalable responses.

Tone:
Helpful, clear, slightly technical when needed, and friendly like a personal nutrition coach."""

EXPLANATION_PROMPT = """You are a nutrition expert.

Explain the generated meal plan in simple terms.

Also include:

* Why this plan fits the user’s goal
* Mention that recommendations were generated using GPU acceleration for faster and efficient matching
* Keep explanation under 120 words"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_meal_plan_gpu",
            "description": "Generate meal plan using GPU-accelerated FAISS similarity search",
            "parameters": {
                "type": "object",
                "properties": {
                    "age": { "type": "integer" },
                    "height": { "type": "number" },
                    "weight": { "type": "number" },
                    "gender": { "type": "string" },
                    "activity": { "type": "string" },
                    "number_of_meals": { "type": "integer" },
                    "weight_loss": { "type": "string" },
                    "diet_type": { "type": "string" },
                    "dislikes": { "type": "array", "items": { "type": "string" } },
                    "budget": { "type": "string" },
                    "cuisine": { "type": "string" }
                },
                "required": ["age", "height", "weight", "gender", "activity", "number_of_meals", "weight_loss"]
            }
        }
    }
]

class ChatIn(BaseModel):
    message: str

class ChatOut(BaseModel):
    explanation: str
    meal_plan: Optional[dict] = None

async def process_chat_message(chat_in: ChatIn, generate_meal_plan_gpu_func) -> ChatOut:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": chat_in.message}
    ]
    
    try:
        response = await client.chat.completions.create(
            model="gemini-1.5-flash",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            if tool_call.function.name == "generate_meal_plan_gpu":
                arguments = json.loads(tool_call.function.arguments)
                
                # Execute the actual backend function
                try:
                    meal_plan_out = generate_meal_plan_gpu_func(arguments)
                    meal_plan_json = meal_plan_out.model_dump_json()
                except Exception as e:
                    meal_plan_json = json.dumps({"error": str(e), "traceback": traceback.format_exc()})
                    meal_plan_out = None
                
                # Feed the function result back to the LLM to get the final explanation
                messages.append(message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": meal_plan_json
                })
                
                # Add the specific explanation instructions before the final response
                messages.append({
                    "role": "system",
                    "content": EXPLANATION_PROMPT
                })
                
                second_response = await client.chat.completions.create(
                    model="gemini-1.5-flash",
                    messages=messages
                )
                
                explanation = second_response.choices[0].message.content
                
                return ChatOut(
                    explanation=explanation, 
                    meal_plan=meal_plan_out.model_dump() if meal_plan_out else None
                )
                
        # If no tool was called (e.g. asking a general question), just return the answer
        return ChatOut(explanation=message.content)
        
    except Exception as e:
        return ChatOut(explanation=f"Error communicating with AI Assistant: {str(e)}")
