# NutriPlan
Senior Design Project 

NutriPlan — Project Statement

Overview

NutriPlan is a meal planning system that automatically generates a weekly meal plan optimized for user budget, nutritional targets (calories and macronutrients), and available grocery products and prices.

The system integrates recipe data, nutrition information, and grocery product data to produce realistic meal plans and shopping lists.

Instead of manually searching for recipes, calculating nutrition, and estimating grocery costs, NutriPlan automatically selects meals that meet nutritional goals, ensures the grocery list fits within a user’s budget, and generates a complete weekly shopping list.

The goal of the project is to build a system that produces practical meal plans that are both nutritionally appropriate and financially realistic.

Core Functionality

NutriPlan performs several major operations.

1. Collect User Preferences

Users provide basic constraints such as weekly grocery budget, daily calorie target, and dietary preferences. These constraints guide the meal planning process.

2. Retrieve Candidate Recipes

The system retrieves recipes from a recipe API. Each recipe includes ingredients, nutrition data, cooking instructions, and serving sizes. These recipes form the candidate pool for meal planning.

3. Normalize Ingredients

Recipe ingredient strings often vary in format. For example: “2 tbsp olive oil”, “olive oil”, or “extra virgin olive oil”.

The system converts these into canonical ingredient names using an ingredient normalization layer.

Example normalization:

extra virgin olive oil → olive oil
ground cinnamon → cinnamon

This step ensures consistent matching between recipes and grocery products.

4. Match Ingredients to Retail Products

Each normalized ingredient is mapped to real grocery products from a retail product dataset, such as a Target grocery dataset.

Example mapping:

ingredient: olive oil

matches:

* Target Brand Olive Oil
* 365 Organic Olive Oil
* Filippo Berio Olive Oil

The system selects the cheapest available option.

5. Compute Nutrition

Using nutrition data sources such as USDA nutrition data, the system calculates calories, protein, carbohydrates, and fat for each recipe. This allows the system to evaluate whether meals meet the user's nutritional targets.

6. Generate a Meal Plan

The meal planning algorithm selects meals from the recipe pool such that total calories are close to the user’s target, meals meet dietary restrictions, and ingredient costs stay within the weekly budget.

The output is a weekly meal plan.

Example:

Monday
Breakfast: Oatmeal with berries
Lunch: Chicken salad
Dinner: Salmon with rice

7. Generate a Shopping List

The system aggregates ingredients across the entire meal plan. These ingredients are converted into a shopping list of grocery products with pricing.

Example:

Chicken breast — $8.50
Rice — $3.20
Broccoli — $4.00
Olive oil — $6.25

The system also calculates the total grocery cost.

System Inputs

Users provide a small set of parameters that define the meal planning constraints.

Inputs include:

Budget — Maximum weekly grocery spending
Daily Calories — Target daily caloric intake
Diet Type — Dietary preference such as standard or vegetarian
Optional Preferences — Ingredient exclusions or macro preferences

Example input:

budget: 75
daily_calories: 2200
diet: standard

System Outputs

NutriPlan produces three primary outputs.

1. Weekly Meal Plan

A structured meal schedule for the week.

Example:

Monday
Breakfast: Oatmeal with fruit
Lunch: Chicken salad
Dinner: Salmon with rice

2. Nutrition Summary

Total nutritional intake for the generated plan.

Example:

weekly_calories: 15400
avg_daily_calories: 2200
protein: 140
carbs: 250
fat: 70

3. Grocery Shopping List

A list of grocery items required for the week with prices and a computed total.

Example:

Chicken breast — 2 lb — $8.50
Rice — 1 bag — $3.20
Broccoli — 2 heads — $4.00

Total cost: $42.75

Data Sources

NutriPlan integrates multiple data sources.

Recipe API (Spoonacular) — Provides recipes and ingredient lists
USDA Nutrition Database — Provides nutrition information
Target Grocery Dataset — Provides real grocery product prices
Ingredient Normalization Layer — Standardizes ingredient names

System Pipeline

The NutriPlan backend processes data through the following pipeline:

User Input
(budget, calories, diet)

↓

Recipe Pool
(from recipe API)

↓

Ingredient Normalization
(clean ingredient system)

↓

Retail Product Matching
(Target grocery dataset)

↓

Nutrition + Cost Calculation

↓

Meal Plan Optimizer

↓

Weekly Meal Plan

↓

Shopping List + Total Cost

Expected Value

NutriPlan helps users plan affordable weekly meals, meet nutritional goals, save time on meal planning, and automatically generate complete grocery lists.

By combining recipes, nutrition data, and real grocery prices, NutriPlan produces meal plans that are both nutritionally sound and financially realistic.