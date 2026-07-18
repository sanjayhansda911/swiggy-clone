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

    def get_fallback_recommendations():
        morning_kws = ['dosa', 'idli', 'coffee', 'latte', 'chai', 'breakfast', 'sandwich', 'waffle', 'toast', 'pav']
        afternoon_kws = ['biryani', 'rice', 'korma', 'chicken', 'bath', 'haleem', 'meals', 'pizza', 'burger']
        
        filtered = []
        seen = set()
        for item in menu_items:
            name_lower = item['name'].lower()
            if name_lower in seen:
                continue
            is_morning = any(kw in name_lower for kw in morning_kws)
            is_afternoon = any(kw in name_lower for kw in afternoon_kws)
            
            added = False
            if time_of_day == "morning" and is_morning:
                filtered.append(item)
                added = True
            elif time_of_day == "afternoon" and is_afternoon:
                filtered.append(item)
                added = True
            elif time_of_day not in ["morning", "afternoon"] and not is_morning:
                filtered.append(item)
                added = True

            if added:
                seen.add(name_lower)

        if len(filtered) < 3:
            seen_lower = {x['name'].lower() for x in filtered}
            for item in menu_items:
                name_l = item['name'].lower()
                if len(filtered) < 3 and name_l not in seen_lower:
                    filtered.append(item)
                    seen_lower.add(name_l)
        
        top_3 = filtered[:3]
        
        # Creative dynamic rationales based on dish name and context
        def get_creative_fallback_rationale(item_name, rest_name, city_name, weather_condition, time_period):
            name_l = item_name.lower()
            is_beverage = any(kw in name_l for kw in ['chai', 'tea', 'coffee', 'latte', 'shake', 'lassi', 'drink', 'smoothie', 'milkshake', 'beverage'])
            is_dessert = any(kw in name_l for kw in ['dessert', 'sweet', 'phirni', 'kulfi', 'cake', 'cheesecake', 'pie', 'muffin', 'halwa', 'tukda', 'gulab jamun', 'brownie'])
            is_cold = any(kw in name_l for kw in ['cold', 'iced', 'shake', 'lassi', 'smoothie', 'milkshake', 'chilled', 'kulfi', 'ice cream', 'phirni'])
            
            # Templates for morning
            if is_beverage or is_dessert:
                if is_cold:
                    templates_morning = [
                        f"Nothing beats a chilled, refreshing {item_name} from {rest_name} to start your day in {city_name}. The perfect companion for this {weather_condition}!",
                        f"Fuel your morning with this cool and creamy {item_name} from {rest_name}. Sweet and satisfying—just what you need on a {weather_condition}.",
                        f"Craving a sweet start? This signature {item_name} from {rest_name} hits all the right comforting notes for this {weather_condition}."
                    ]
                else:
                    templates_morning = [
                        f"Nothing beats a steaming cup of {item_name} from {rest_name} to start your day in {city_name}. The perfect companion for this {weather_condition}!",
                        f"Fuel your morning with this aromatic, hot {item_name} from {rest_name}. Comforting and satisfying—just what you need on a {weather_condition}.",
                        f"Craving a warm start? This signature {item_name} from {rest_name} hits all the right comforting notes for this {weather_condition}."
                    ]
            else:
                templates_morning = [
                    f"Nothing beats a fresh {item_name} from {rest_name} to kickstart your day in {city_name}. It's the ultimate companion for this {weather_condition}!",
                    f"Fuel your morning with this mouth-watering {item_name} from {rest_name}. Hot, crispy, and satisfying—just what you need on a {weather_condition}.",
                    f"Craving a cozy breakfast? This signature {item_name} from {rest_name} hits all the right comfort notes for this {weather_condition}."
                ]
            
            # Templates for afternoon
            if is_beverage or is_dessert:
                if is_cold:
                    templates_afternoon = [
                        f"Cool down this afternoon with a chilled {item_name} from {rest_name}. It is perfect for a sweet refresh during this {weather_condition}.",
                        f"This legendary {item_name} from {rest_name} is the ultimate refreshing treat—guaranteed comfort for a {weather_condition} in {city_name}.",
                        f"Beat the mid-day heat with a cool, creamy {item_name} from {rest_name}. The flavors are ideal for this {weather_condition} hour."
                    ]
                else:
                    templates_afternoon = [
                        f"Warm up this afternoon with a freshly brewed {item_name} from {rest_name}. It is perfect for a rich refresh during this {weather_condition}.",
                        f"This rich {item_name} from {rest_name} is brewed to perfection—guaranteed comfort for a {weather_condition} in {city_name}.",
                        f"Beat the mid-day slump with a hot cup of {item_name} from {rest_name}. The aromatic flavors are ideal for this {weather_condition} hour."
                    ]
            else:
                templates_afternoon = [
                    f"Treat yourself to this delicious {item_name} from {rest_name}. It is perfect for a satisfying lunch during this {weather_condition}.",
                    f"This legendary {item_name} from {rest_name} is slow-cooked to perfection—guaranteed comfort food for a {weather_condition} in {city_name}.",
                    f"Beat the mid-day slump with {item_name} from {rest_name}. The warm, rich flavors are ideal for this {weather_condition} hour."
                ]
            
            # Templates for evening
            if is_beverage or is_dessert:
                if is_cold:
                    templates_evening = [
                        f"Treat yourself to a chilled, comforting {item_name} from {rest_name}. Perfect for a cozy {weather_condition} evening in {city_name}.",
                        f"There's nothing quite like {rest_name}'s creamy, refreshing {item_name} to satisfy your sweet cravings during this {weather_condition} evening.",
                        f"A sweet serving of {item_name} from {rest_name} is the ultimate treat to close out this {weather_condition} hour."
                    ]
                else:
                    templates_evening = [
                        f"Wind down your day with a steaming, comforting cup of {item_name} from {rest_name}. Perfect for a cozy {weather_condition} evening in {city_name}.",
                        f"There's nothing quite like {rest_name}'s hot, aromatic {item_name} to warm you up during this {weather_condition} evening.",
                        f"A soothing cup of {item_name} from {rest_name} is the ultimate warm comfort to close out this {weather_condition} hour."
                    ]
            else:
                templates_evening = [
                    f"Wind down your day with the comforting flavors of {item_name} from {rest_name}. Perfect for a cozy {weather_condition} dinner in {city_name}.",
                    f"There's nothing quite like {rest_name}'s hot, flavorful {item_name} to warm you up during this {weather_condition} evening.",
                    f"A delicious plate of {item_name} from {rest_name} is the ultimate comfort meal to close out this {weather_condition} hour."
                ]
            
            # Select templates bucket
            if time_period == "morning":
                templates = templates_morning
            elif time_period == "afternoon":
                templates = templates_afternoon
            else:
                templates = templates_evening
                
            # Select template deterministically using name character sum hash
            name_hash = sum(ord(c) for c in item_name)
            return templates[name_hash % len(templates)]

        recs = []
        for x in top_3:
            recs.append({
                "name": x["name"],
                "restaurantName": x["restaurantName"],
                "restaurantId": x["restaurantId"],
                "price": x["price"],
                "ai_rationale": get_creative_fallback_rationale(x["name"], x["restaurantName"], city, weather, time_of_day)
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

@app.route('/api/voice-parse', methods=['POST'])
def voice_parse():
    """
    Parse a voice checkout transcript using Gemini NLU or a local rule-based fallback.
    """
    data = request.get_json() or {}
    text = data.get("text", "")
    menu_items = data.get("menuItems", [])

    if not text or not menu_items:
        return jsonify({
            "action": "ERROR",
            "items": [],
            "speech_response": "I didn't hear anything. Could you please try again?",
            "clarification_options": None
        })

    # Local fallback logic in case Gemini is not configured or fails
    def local_fallback_voice_parse():
        query = text.lower().strip()
        number_map = {
            "one": 1, "a": 1, "an": 1, "single": 1, "1": 1,
            "two": 2, "double": 2, "couple": 2, "2": 2,
            "three": 3, "triple": 3, "3": 3,
            "four": 4, "4": 4, "five": 5, "5": 5
        }
        
        import re
        parts = re.split(r'\b(?:and|plus)\b|,', query)
        parsed_items = []
        
        for part in parts:
            clean_part = part.strip()
            if not clean_part:
                continue
                
            quantity = 1
            words = clean_part.split()
            for idx in range(min(len(words), 3)):
                word = words[idx]
                if word in number_map:
                    quantity = number_map[word]
                    clean_part = clean_part.replace(word, "").strip()
                    break
            
            best_match = None
            best_score = 0
            for item in menu_items:
                item_name_lower = item["name"].lower()
                score = 0
                if clean_part in item_name_lower:
                    score += 150
                else:
                    item_words = item_name_lower.split()
                    for w in item_words:
                        if len(w) > 2 and w in clean_part:
                            score += 40
                if score > best_score and score >= 30:
                    best_score = score
                    best_match = item
            
            if best_match:
                parsed_items.append({
                    "name": best_match["name"],
                    "quantity": quantity,
                    "restaurantId": best_match["restaurantId"],
                    "restaurantName": best_match["restaurantName"]
                })
        
        if parsed_items:
            item_desc = ", ".join([f"{x['quantity']}x {x['name']}" for x in parsed_items])
            speech = f"Sure! Adding {item_desc} to your cart."
            return {
                "action": "ADD_TO_CART",
                "items": [{"name": x["name"], "quantity": x["quantity"], "restaurantId": x["restaurantId"], "modifiers": []} for x in parsed_items],
                "speech_response": speech,
                "clarification_options": None
            }
        else:
            return {
                "action": "ERROR",
                "items": [],
                "speech_response": f"I couldn't match any items for '{text}' in our menu. Could you please specify a dish?",
                "clarification_options": None
            }

    api_key_check = os.environ.get("GEMINI_API_KEY")
    if not api_key_check:
        return jsonify(local_fallback_voice_parse())

    try:
        # Build prompt listing menu items
        prompt = f"""
You are Milo, the intelligent AI NLU parser for Swiggy HungerBites voice assistant.
Your job is to analyze the user's spoken voice command and map it to specific menu items from the restaurant database.

User Voice Command: "{text}"

Available Menu Items:
{json.dumps(menu_items)}

Instructions:
1. Identify all dishes the user wants to order.
2. For each identified dish, match it to the most relevant dish in the "Available Menu Items" list. Look for semantic matches, abbreviations, or correct restaurants if specified in the text.
3. Extract the requested quantity (default is 1 if not specified).
4. Extract any customization modifiers (e.g., "extra cheese", "no onion", "spicy", "double shot", "less sugar", "chilled", "eggless") requested for the dish under the "modifiers" field as a list of strings.
5. If a dish matches multiple candidate options in different restaurants and the user did NOT specify which restaurant, set action to "CLARIFY" and list the ambiguous matches in "clarification_options".
6. Otherwise, if successfully matched, set action to "ADD_TO_CART" and fill "items" with:
   - "name": the exact name of the selected dish in the database.
   - "quantity": the integer quantity.
   - "restaurantId": the integer restaurant ID.
   - "modifiers": a list of strings representing extracted customization options.
7. Generate a friendly, conversational audio confirmation message under "speech_response" confirming what was added (including customizations if specified), or asking a clarification question if action is "CLARIFY".

Respond in JSON format. The response must be a JSON object with:
- "action": "ADD_TO_CART" or "CLARIFY" or "ERROR"
- "items": [{"name": str, "quantity": int, "restaurantId": int, "modifiers": [str]}]
- "speech_response": str
- "clarification_options": [{"name": str, "restaurantName": str, "restaurantId": int, "price": float}] or null
"""

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        result = json.loads(response.text)
        return jsonify(result)
        
    except Exception as e:
        print(f"Gemini Voice Parse Error: {e}")
        return jsonify(local_fallback_voice_parse())


if __name__ == '__main__':
    # Running Flask app on localhost, port 5000 in debug mode
    app.run(host='127.0.0.1', port=5000, debug=True)
