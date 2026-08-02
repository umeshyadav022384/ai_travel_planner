# Python_server/app.py

import os
import random
import traceback
import numpy as np
import re
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from chatbot_utils import (
    load_chatbot_resources, 
    predict_intent, 
    get_response,
    fuzzy_city_match,
    get_city_info,
    format_city_info,
    format_attractions,
    format_hotels,
    format_food,
    format_transport,
    format_shopping,
    detect_query_type,
    get_city_response_by_type,
    get_unknown_response
)
import chatbot_utils

from external_api import get_weather, get_travel_recommendations, search_restaurants, search_hotels
from algorithm import generate_itinerary, load_attractions
from packing_algorithm import PackingAlgorithm  

from gemini_integration import gemini

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def extract_location(user_message):
    """Extract location from user message - IMPROVED"""
    user_lower = user_message.lower()
    
    # List of all cities
    cities = ["kathmandu", "pokhara", "lumbini", "chitwan", "bhaktapur", "lalitpur", 
              "everest", "annapurna", "mustang", "manang", "janakpur", "gorkha", "syangja", "nepal"]
    
    # 1. Direct city mention
    for city in cities:
        if city in user_lower:
            return city.title()
    
    # 2. Pattern matching for "weather in X", "weather of X", "temperature of X"
    patterns = [
        r'(?:weather|temperature|climate|forecast)\s+(?:in|of|for)\s+([a-zA-Z\s]+)',
        r'(?:in|of|for)\s+([a-zA-Z\s]+)\s+(?:weather|temperature|climate|forecast)',
        r'what(?:\'s|s| is)?\s+the\s+(?:weather|temperature)\s+(?:in|of|for)\s+([a-zA-Z\s]+)',
        r'how\s+is\s+the\s+(?:weather|temperature)\s+(?:in|of|for)\s+([a-zA-Z\s]+)',
        r'weather\s+(?:in|of|for)\s+([a-zA-Z\s]+)',
        r'temperature\s+(?:in|of|for)\s+([a-zA-Z\s]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_lower)
        if match:
            location = match.group(1).strip()
            # Check if extracted location matches a city
            for city in cities:
                if city in location.lower():
                    return city.title()
            return location.title()
    
    # 3. Last resort - try to find any city name
    for city in cities:
        if city in user_lower:
            return city.title()
    
    return None


def extract_city_from_message(user_message):
    cities = ["kathmandu", "pokhara", "lumbini", "chitwan", "bhaktapur", "lalitpur", 
              "everest", "annapurna", "mustang", "manang", "janakpur", "gorkha", "syangja", "nepal"]
    user_lower = user_message.lower()
    for city in cities:
        if city in user_lower:
            return city.title()
    match = re.search(r'in\s+([a-zA-Z]+)', user_lower)
    if match:
        city = match.group(1).lower()
        if city in cities:
            return city.title()
    return None


def extract_city_from_intent(intent_tag):
    cities = ["nepal", "kathmandu", "pokhara", "lumbini", "chitwan", "bhaktapur", "lalitpur", 
              "everest", "annapurna", "mustang", "manang", "janakpur", "gorkha", "syangja"]
    for city in cities:
        if city in intent_tag.lower():
            return city.title()
    return None


def load_chatbot_data():
    try:
        with open('chatbot_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("chatbot_data.json not found")
        return None
    except json.JSONDecodeError:
        print("chatbot_data.json is empty or has invalid JSON")
        return None

chatbot_data = load_chatbot_data()


# ==========================================
# FLASK APP SETUP
# ==========================================

load_dotenv()
app = Flask(__name__)
CORS(app)

print("Loading chatbot resources...")
load_chatbot_resources()
print("Chatbot resources loaded successfully")

if chatbot_data:
    print(f"Loaded {len(chatbot_data.get('cities', []))} cities from chatbot_data.json")
else:
    print("chatbot_data.json not found - using fallback responses")


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route('/api/ml/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OK', 
        'service': 'ML Server',
        'model_loaded': chatbot_utils.chat_model is not None,
        'cities_loaded': len(chatbot_data.get('cities', [])) if chatbot_data else 0,
        'gemini_available': gemini.model is not None
    })


# ==========================================
# CHAT ENDPOINT - COMPLETELY FIXED
# ==========================================

@app.route('/api/ml/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"reply": "Please send a message."})
        
        print(f"User: {user_message}")
        
        # ==========================================
        # STEP 1: Use chatbot_utils.get_response()
        # ==========================================
        response, intent_tag, confidence = get_response(user_message)
        print(f"Intent: {intent_tag}, Confidence: {confidence:.2f}")
        
        # ==========================================
        # STEP 2: Handle WEATHER intent
        # ==========================================
        if intent_tag == "get_weather":
            # Extract location using improved function
            location = extract_location(user_message)
            
            # If not found, try fuzzy match
            if not location:
                location = fuzzy_city_match(user_message)
            
            # If still not found, try to find any city
            if not location:
                cities = ["kathmandu", "pokhara", "lumbini", "chitwan", "bhaktapur", "lalitpur", 
                         "everest", "annapurna", "mustang", "manang", "janakpur", "gorkha", "syangja"]
                for city in cities:
                    if city in user_message.lower():
                        location = city.title()
                        break
            
            if not location:
                return jsonify({"reply": "Please specify a location for weather information. For example: 'weather in Kathmandu' or 'temperature of Pokhara'"})
            
            weather_result = get_weather(location)
            return jsonify({"reply": weather_result})
        
        # ==========================================
        # STEP 3: Handle TRAVEL RECOMMENDATIONS
        # ==========================================
        elif intent_tag == "get_travel_recommendations":
            location = extract_location(user_message)
            if not location:
                location = fuzzy_city_match(user_message)
            if not location:
                return jsonify({"reply": "Please specify a location for recommendations."})
            travel_result = get_travel_recommendations(location)
            return jsonify({"reply": travel_result})
        
        # ==========================================
        # STEP 4: If response is None, use fallback
        # ==========================================
        if response is None:
            # Try fuzzy match as final fallback
            city_name = fuzzy_city_match(user_message)
            if city_name:
                city_info = get_city_info(city_name)
                if city_info:
                    query_type = detect_query_type(user_message)
                    response = get_city_response_by_type(city_info, query_type, user_message)
                    if response:
                        return jsonify({"reply": response})
            
            reply = get_unknown_response(user_message)
            return jsonify({"reply": reply})
        
        # ==========================================
        # STEP 5: Return response
        # ==========================================
        return jsonify({"reply": response})
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({"reply": "Error processing your request."})


# ==========================================
# GENERATE ITINERARY ENDPOINT
# ==========================================

@app.route('/api/ml/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        destination = data.get('destination')
        preferences = data.get('preferences', {})
        days = data.get('days', 3)
        budget_type = data.get('budget_type', 'per_day')
        budget = int(data.get('budget', 500))
        use_gemini = data.get('use_gemini', True)

        if budget_type == 'per_day':
            daily_budget = budget
            total_budget = budget * days
        else:
            daily_budget = budget // days
            total_budget = budget

        print(f"Budget Type: {budget_type}")
        print(f"Daily Budget: ${daily_budget}")
        print(f"Total Budget: ${total_budget}")

        restaurants = []
        hotels = []

        try:
            print(f"Fetching restaurants for {destination}...")
            restaurants = search_restaurants(destination, limit=5)
            print(f"Found {len(restaurants)} restaurants")
        except Exception as e:
            print(f"Restaurant fetch failed: {e}")

        try:
            print(f"Fetching hotels for {destination}...")
            hotels = search_hotels(destination)
            print(f"Found {len(hotels)} hotels")
        except Exception as e:
            print(f"Hotel fetch failed: {e}")

        itinerary = generate_itinerary(
            destination, preferences, days, daily_budget,
            restaurants=restaurants,
            hotels=hotels
        )

        weather_forecast = []
        weather_summary = None

        try:
            weather_result = get_weather(destination)
            print(f"Weather result: {weather_result}")

            if weather_result and "Sorry" not in weather_result:
                import re
                temp_match = re.search(r'Temperature: ([\d.]+)°C', weather_result)
                condition_match = re.search(r'Condition: (.+)', weather_result)

                temp = round(float(temp_match.group(1))) if temp_match else 25
                condition = condition_match.group(1).lower() if condition_match else 'sunny'

                for i in range(days):
                    weather_forecast.append({
                        'temp': temp + i,
                        'rain': 0,
                        'condition': condition,
                        'wind': 10,
                        'date': f'2024-01-{i+1:02d}'
                    })
                weather_summary = {
                    'hasRain': False,
                    'maxTemp': temp + days - 1,
                    'minTemp': temp
                }
            else:
                for i in range(days):
                    weather_forecast.append({
                        'temp': 25 + i,
                        'rain': 0,
                        'condition': 'sunny',
                        'wind': 10,
                        'date': f'2024-01-{i+1:02d}'
                    })
                weather_summary = {'hasRain': False, 'maxTemp': 25 + days, 'minTemp': 25}
        except Exception as e:
            print(f"Weather fetch failed: {e}")
            for i in range(days):
                weather_forecast.append({
                    'temp': 25 + i,
                    'rain': 0,
                    'condition': 'sunny',
                    'wind': 10,
                    'date': f'2024-01-{i+1:02d}'
                })
            weather_summary = {'hasRain': False, 'maxTemp': 25 + days, 'minTemp': 25}

        packing_result = None
        try:
            packing_result = PackingAlgorithm.generate_packing_list(
                weather_forecast=weather_forecast,
                destination=destination,
                activities=[]
            )
        except Exception as e:
            print(f"Packing list generation failed: {e}")

        daily_costs = []
        total_cost = 0
        for day in itinerary:
            day_cost = day.get('day_cost', 0)
            daily_costs.append(day_cost)
            total_cost += day_cost

        enhanced = None
        gemini_used = False

        if use_gemini and gemini and gemini.model:
            try:
                print("Enhancing itinerary with Gemini...")
                
                has_restaurants = restaurants and len(restaurants) > 0
                has_hotels = hotels and len(hotels) > 0
                
                if has_restaurants or has_hotels:
                    enhanced = gemini.enhance_itinerary(
                        itinerary_data=itinerary,
                        destination=destination,
                        days=days,
                        preferences=preferences,
                        weather_forecast=weather_forecast,
                        daily_costs=daily_costs,
                        restaurants=restaurants,
                        hotels=hotels
                    )
                    
                    if enhanced:
                        gemini_used = True
                        print("Itinerary enhanced with Gemini")
                    else:
                        print("Gemini enhancement returned empty. Using technical itinerary.")
                else:
                    print("No restaurant/hotel data available for Gemini enhancement.")
                    
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg:
                    print("Gemini rate limited. Please wait 60 seconds.")
                elif 'RESOURCE_EXHAUSTED' in error_msg:
                    print("Gemini quota exhausted. Please try again later.")
                else:
                    print(f"Gemini enhancement failed: {e}")

        return jsonify({
            'success': True,
            'destination': destination,
            'days': days,
            'dailyActivities': itinerary,
            'dailyCosts': daily_costs,
            'totalCost': total_cost,
            'budget': budget,
            'dailyBudget': daily_budget,
            'totalBudget': total_budget,
            'budgetType': budget_type,
            'weatherForecast': weather_forecast,
            'weatherSummary': weather_summary,
            'enhanced': enhanced,
            'gemini_used': gemini_used,
            'packingList': packing_result,
            'restaurants': restaurants,
            'hotels': hotels
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'errorType': 'SERVER_ERROR',
            'message': 'Failed to generate itinerary. Please try again.'
        })


# ==========================================
# ATTRACTIONS ENDPOINT
# ==========================================

@app.route('/api/ml/attractions', methods=['GET'])
def get_attractions():
    try:
        city = request.args.get('city')
        attractions = load_attractions()
        if city:
            attractions = [a for a in attractions if a.get('city', '').lower() == city.lower()]
        return jsonify({'attractions': attractions})
    except Exception as e:
        return jsonify({'attractions': [], 'error': str(e)})


# ==========================================
# PACKING ENDPOINT
# ==========================================

@app.route('/api/ml/packing', methods=['POST'])
def get_packing_list():
    try:
        data = request.json
        weather_data = data.get('weatherData', {})
        destination = data.get('destination', '')
        activities = data.get('activities', [])

        weather_forecast = []
        for day in weather_data.get('days', []):
            weather_forecast.append({
                'temp': day.get('tempmax', 25),
                'rain': day.get('precip', 0),
                'condition': day.get('conditions', 'sunny').lower(),
                'wind': day.get('windspeed', 10),
                'date': day.get('datetime', '')
            })

        packing_result = PackingAlgorithm.generate_packing_list(
            weather_forecast=weather_forecast,
            destination=destination,
            activities=activities
        )

        return jsonify({'success': True, 'packingList': packing_result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==========================================
# RUN SERVER
# ==========================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Starting ML Server on port 5000...")
    print("="*60)
    app.run(port=5000, debug=True, host='0.0.0.0')