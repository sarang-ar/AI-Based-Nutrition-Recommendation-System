import os
import re
from contextlib import asynccontextmanager
from typing import Annotated, List, Literal, Optional

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import DEFAULT_N_NEIGHBORS, MEALS_CALORIES_PERC, WEIGHT_LOSS_PLANS
from image_finder import get_image_url
from model import output_recommended_recipes, recommend
from nutrition import build_nutrition_vector, calculate_bmi, calculate_bmr, calculate_tdee
from ai_agent import ChatIn, ChatOut, process_chat_message

# Absolute path so the app works regardless of working directory.
_DATASET_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'Data', 'dataset.csv'
)
_FOOD_DATASET_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'FoodData', 'FoodData_Central_csv_2020-04-29', 'food.csv'
)

dataset: Optional[pd.DataFrame] = None
food_dataset: Optional[pd.DataFrame] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global dataset, food_dataset
    if dataset is None:
        # Pre-process ingredient strings into frozensets once at startup.
        # Enables fast set-based filtering in extract_ingredient_filtered_data()
        # instead of scanning every row with a compound regex on each request.
        dataset = pd.read_csv(_DATASET_PATH, compression='gzip')
        dataset['_ingredients_parsed'] = dataset['RecipeIngredientParts'].apply(
            lambda x: frozenset(s.lower() for s in re.findall(r'"([^"]*)"', x))
        )
    if food_dataset is None:
        try:
            food_dataset = pd.read_csv(_FOOD_DATASET_PATH)
        except Exception as e:
            print(f"Failed to load food dataset: {e}")
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost",
        "http://localhost:80",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------------------------------------------------------
# Shared models
# ---------------------------------------------------------------------------

class Recipe(BaseModel):
    Name: str
    CookTime: str
    PrepTime: str
    TotalTime: str
    RecipeIngredientParts: list[str]
    Calories: float
    FatContent: float
    SaturatedFatContent: float
    CholesterolContent: float
    SodiumContent: float
    CarbohydrateContent: float
    FiberContent: float
    SugarContent: float
    ProteinContent: float
    RecipeInstructions: list[str]
    image_url: Optional[str] = None


# ---------------------------------------------------------------------------
# /predict/ — custom nutrition-based recommendation
# ---------------------------------------------------------------------------

class Params(BaseModel):
    n_neighbors: int = DEFAULT_N_NEIGHBORS
    return_distance: bool = False


class PredictionIn(BaseModel):
    nutrition_input: Annotated[list[float], Field(min_length=9, max_length=9)]
    ingredients: list[str] = []
    params: Optional[Params] = None


class PredictionOut(BaseModel):
    output: Optional[List[Recipe]] = None


# ---------------------------------------------------------------------------
# /generate-meal-plan/ — automatic meal plan from personal data
# ---------------------------------------------------------------------------

class PersonData(BaseModel):
    age: int
    height: float               # cm
    weight: float               # kg
    gender: Literal["Male", "Female"]
    activity: str               # must be a key in ACTIVITY_MULTIPLIERS
    number_of_meals: Literal[2, 3, 4, 5]  # Prompt specifies 2-5
    weight_loss: str            # must be a key in WEIGHT_LOSS_PLANS
    diet_type: Optional[str] = None
    dislikes: Optional[List[str]] = None
    budget: Optional[str] = None
    cuisine: Optional[str] = None


class MealRecommendation(BaseModel):
    meal_name: str
    recipes: List[Recipe]


class MealPlanOut(BaseModel):
    bmi: float
    bmr: float
    maintain_calories: float    # TDEE (no weight-loss adjustment)
    target_calories: float      # TDEE × weight-loss factor
    meals: List[MealRecommendation]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    return {"health_check": "OK"}


@app.post("/predict/", response_model=PredictionOut)
def predict(prediction_input: PredictionIn):
    params = (
        prediction_input.params.model_dump()
        if prediction_input.params
        else {"n_neighbors": DEFAULT_N_NEIGHBORS, "return_distance": False}
    )
    recommendation_dataframe = recommend(
        dataset,
        prediction_input.nutrition_input,
        prediction_input.ingredients,
        params,
    )
    output = output_recommended_recipes(recommendation_dataframe)
    if output:
        for recipe in output:
            recipe['image_url'] = get_image_url(recipe['Name'])
    return {"output": output}


@app.post("/generate-meal-plan/", response_model=MealPlanOut)
def generate_meal_plan(person: PersonData):
    bmi = calculate_bmi(person.weight, person.height)
    bmr = calculate_bmr(person.weight, person.height, person.age, person.gender)
    maintain_calories = calculate_tdee(bmr, person.activity)
    factor = WEIGHT_LOSS_PLANS[person.weight_loss]["factor"]
    target_calories = maintain_calories * factor

    meals = []
    for meal_name, perc in MEALS_CALORIES_PERC[person.number_of_meals].items():
        vector = build_nutrition_vector(target_calories * perc, meal_name)
        recs = recommend(
            dataset, vector, [],
            {"n_neighbors": DEFAULT_N_NEIGHBORS, "return_distance": False},
        )
        recipes = output_recommended_recipes(recs) if recs is not None else []
        for recipe in recipes:
            recipe['image_url'] = get_image_url(recipe['Name'])
        meals.append(MealRecommendation(
            meal_name=meal_name,
            recipes=recipes,
        ))

    return MealPlanOut(
        bmi=bmi,
        bmr=round(bmr, 2),
        maintain_calories=round(maintain_calories),
        target_calories=round(target_calories),
        meals=meals,
    )


@app.post("/chat-meal-plan/", response_model=ChatOut)
async def chat_meal_plan(chat_in: ChatIn):
    def _run_meal_plan(args: dict):
        # We handle any missing required parameters gracefully using defaults just in case
        person_data = PersonData(
            age=args.get("age", 25),
            height=args.get("height", 170.0),
            weight=args.get("weight", 70.0),
            gender=args.get("gender", "Male"),
            activity=args.get("activity", "Light"),
            number_of_meals=args.get("number_of_meals", 3),
            weight_loss=args.get("weight_loss", "Maintain weight"),
            diet_type=args.get("diet_type"),
            dislikes=args.get("dislikes"),
            budget=args.get("budget"),
            cuisine=args.get("cuisine"),
        )
        return generate_meal_plan(person_data)
        
    return await process_chat_message(chat_in, _run_meal_plan)


# ---------------------------------------------------------------------------
# /search-food/ — search USDA food datasets
# ---------------------------------------------------------------------------

class FoodSearchOut(BaseModel):
    fdc_id: int
    description: str

@app.get("/search-food/", response_model=List[FoodSearchOut])
def search_food(query: str, limit: int = 10):
    if food_dataset is None:
        return []
    mask = food_dataset['description'].str.contains(query, case=False, na=False)
    results = food_dataset[mask].head(limit)
    return [{"fdc_id": row['fdc_id'], "description": row['description']} for _, row in results.iterrows()]

