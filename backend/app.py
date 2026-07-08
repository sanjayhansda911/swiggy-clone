import os
import json
from flask import Flask, jsonify, abort

app = Flask(__name__, static_folder='../frontend', static_url_path='')

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
    # Return basic info of all restaurants
    return jsonify(restaurants)

@app.route('/api/restaurants/<int:restaurant_id>', methods=['GET'])
def get_restaurant(restaurant_id):
    """Endpoint to get a single restaurant and its menu by ID."""
    restaurants = load_restaurants()
    restaurant = next((r for r in restaurants if r['id'] == restaurant_id), None)
    if restaurant is None:
        abort(404, description="Restaurant not found")
    return jsonify(restaurant)

if __name__ == '__main__':
    # Running Flask app on localhost, port 5000 in debug mode
    app.run(host='127.0.0.1', port=5000, debug=True)
