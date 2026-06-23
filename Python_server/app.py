import os, random, traceback, numpy as np, re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from chatbot_utils import load_chatbot_resources, bag_of_words
import chatbot_utils

from external_api import get_weather, get_travel_recommendations
from algorithm import generate_itinerary, load_attractions
from packing_algorithm import PackingAlgorithm  

# ---------------------------
# Improved Regex Extraction
# ---------------------------
def extract_location(user_message):
    """
    Extracts location names from user queries for weather/travel intents.
    Handles variations like 'weather in', 'temperature of', 'travel to',
    'recommend place(s) in', 'best hotel in', etc.
    """
    location_pattern = re.compile(
        r"(?:weather in|temperature of|forecast for|travel to|recommend place in|recommend places in|best hotel in|suggest place in|suggest places in)\s+([A-Za-z\s]+)",
        re.IGNORECASE
    )
    match = location_pattern.search(user_message)
    return match.group(1).strip() if match else None

# Flask App Setup
load_dotenv()
app = Flask(__name__)
CORS(app)
print("🔄 Loading chatbot resources...")
load_chatbot_resources()
print("✅ Chatbot resources loaded successfully")

# Health Check
@app.route('/api/ml/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK', 'service': 'ML Server'})

# ---------------------------
# Chat Endpoint
@app.route('/api/ml/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"reply": "Please send a message."})

        print("User message:", user_message)

        # Predict intent using model
        bow = bag_of_words(user_message, chatbot_utils.words)

        res = chatbot_utils.chat_model.predict(
            np.array([bow]),
            verbose=0
        )[0]

        predicted_index = np.argmax(res)
        confidence = float(res[predicted_index])

        print("Confidence:", confidence)

        # Confidence too low
        if confidence < 0.50:
            return jsonify({
                "reply": "Sorry, I didn't understand that. Could you rephrase?"
            })

        predicted_tag = chatbot_utils.classes[predicted_index]

        print("Predicted Tag:", predicted_tag)

        # WEATHER INTENT
        if predicted_tag == "get_weather":

            location = extract_location(user_message)

            if not location:
                return jsonify({
                    "reply": "Please specify a location."
                })

            weather_result = get_weather(location)

            return jsonify({
                "reply": weather_result
            })

        # TRAVEL RECOMMENDATION INTENT
        elif predicted_tag == "get_travel_recommendations":

            location = extract_location(user_message)

            if not location:
                return jsonify({
                    "reply": "Please specify a location."
                })

            travel_result = get_travel_recommendations(location)

            return jsonify({
                "reply": travel_result
            })
        
        # DATASET RESPONSE
        else:

            for intent in chatbot_utils.knowledge_base:

                if intent["tag"] == predicted_tag:

                    response = random.choice(
                        intent["responses"]
                    )

                    return jsonify({
                        "reply": response
                    })

            return jsonify({
                "reply": "Sorry, I don't have information on that."
            })

    except Exception as e:
        traceback.print_exc()

        return jsonify({
            "reply": "Error processing your request."
        })

# Itinerary Endpoint
@app.route('/api/ml/generate', methods=['POST'])
def generate():
    data = request.json
    destination = data.get('destination')
    preferences = data.get('preferences', {})
    days = data.get('days', 3)
    budget = int(data.get('budget', 500))
    daily_budget = budget // days
    itinerary = generate_itinerary(destination, preferences, days, daily_budget)
    return jsonify({'success': True, 'destination': destination, 'days': days,
                    'dailyActivities': itinerary, 'totalCost': budget})

# ---------------------------
# Attractions Endpoint
# ---------------------------
@app.route('/api/ml/attractions', methods=['GET'])
def get_attractions():
    city = request.args.get('city')
    attractions = load_attractions()
    if city:
        attractions = [a for a in attractions if a['city'].lower() == city.lower()]
    return jsonify({'attractions': attractions})

# ---------------------------
# Packing Endpoint
# ---------------------------
@app.route('/api/ml/packing', methods=['POST'])
def get_packing_list():
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

# ---------------------------
# Run Server
# ---------------------------
if __name__ == '__main__':
    print("🚀 Starting ML Server on port 5000...")
    app.run(port=5000, debug=True)
