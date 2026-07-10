import os
import json
from flask import Flask, jsonify, abort, request
from dotenv import load_dotenv
import google.generativeai as genai

# Load env variables from .env file (local development fallback)
load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Configure Google Gemini API key
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

# Helper function to load restaurant data
def load_restaurants():
    data_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'data', 'restaurants.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

@app.route('/api/restaurants', methods=['GET'])
def get_restaurants():
    """Endpoint to get the list of all mock restaurants."""
    restaurants = load_restaurants()
    return jsonify(restaurants)

@app.route('/api/restaurants/<int:restaurant_id>', methods=['GET'])
def get_restaurant(restaurant_id):
    """Endpoint to get a single restaurant and its menu by ID."""
    restaurants = load_restaurants()
    restaurant = next((r for r in restaurants if r['id'] == restaurant_id), None)
    if restaurant is None:
        abort(404, description="Restaurant not found")
    return jsonify(restaurant)

@app.route('/api/recommend', methods=['POST'])
def recommend_meals():
    """
    Select 3 empathetic food recommendations based on city, weather, and time of day using Gemini.
    """
    data = request.get_json() or {}
    city = data.get("city", "Hyderabad")
    weather = data.get("weather", "Rainy Evening (24°C)")
    time_of_day = data.get("timeOfDay", "evening")
    menu_items = data.get("menuItems", [])

    if not menu_items:
        return jsonify({"recommendations": []})

    # Prepare fallback data in case Gemini fails or is not configured
    def get_fallback_recommendations():
        morning_kws = ['dosa', 'idli', 'coffee', 'latte', 'chai', 'breakfast', 'sandwich', 'waffle', 'toast', 'pav']
        afternoon_kws = ['biryani', 'rice', 'korma', 'chicken', 'bath', 'haleem', 'meals', 'pizza', 'burger']
        
        filtered = []
        for item in menu_items:
            name_lower = item['name'].lower()
            is_morning = any(kw in name_lower for kw in morning_kws)
            is_afternoon = any(kw in name_lower for kw in afternoon_kws)
            
            if time_of_day == "morning" and is_morning:
                filtered.append(item)
            elif time_of_day == "afternoon" and is_afternoon:
                filtered.append(item)
            elif time_of_day not in ["morning", "afternoon"] and not is_morning:
                filtered.append(item)

        if len(filtered) < 3:
            seen = {x['name'] for x in filtered}
            for item in menu_items:
                if len(filtered) < 3 and item['name'] not in seen:
                    filtered.append(item)
                    seen.add(item['name'])
        
        top_3 = filtered[:3]
        
        recs = []
        for x in top_3:
            recs.append({
                "name": x["name"],
                "restaurantName": x["restaurantName"],
                "restaurantId": x["restaurantId"],
                "price": x["price"],
                "ai_rationale": f"Since it's a {weather} in {city} at this {time_of_day} hour, this warm {x['name']} from {x['restaurantName']} is selected as your absolute comfort meal."
            })
        return recs

    api_key_check = os.environ.get("GEMINI_API_KEY")
    if not api_key_check:
        return jsonify({"recommendations": get_fallback_recommendations()})

    try:
        # Build prompt listing unique menu items to save token usage
        unique_items = {}
        for item in menu_items:
            if item["name"] not in unique_items:
                unique_items[item["name"]] = {
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "price": item["price"],
                    "restaurantName": item["restaurantName"],
                    "restaurantId": item["restaurantId"]
                }
        
        items_list = list(unique_items.values())
        
        prompt = f"""
You are the AI Empathy Recommendation Engine for Swiggy HungerBites.
Based on the current weather condition "{weather}" and time of day "{time_of_day}" in the city of "{city}", select exactly 3 comfort meals from the provided menu list that will bring maximum culinary joy.

For each selected meal, generate a short, highly-empathetic, mouth-watering explanation (1-2 sentences) of why this meal is perfect for the user right now, matching the weather and time.

Provide your response in JSON format. The response must be a JSON object containing a "recommendations" array. Each item in the array must contain:
1. "name": the exact name of the selected dish.
2. "restaurantName": the exact name of the restaurant.
3. "restaurantId": the exact ID of the restaurant (integer).
4. "price": the price of the item (number).
5. "ai_rationale": your custom empathetic explanation.

Menu list of candidates:
{json.dumps(items_list)}
"""

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        result = json.loads(response.text)
        return jsonify(result)
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return jsonify({"recommendations": get_fallback_recommendations()})

if __name__ == '__main__':
    # Running Flask app on localhost, port 5000 in debug mode
    app.run(host='127.0.0.1', port=5000, debug=True)
