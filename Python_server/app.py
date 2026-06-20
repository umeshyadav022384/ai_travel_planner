import os, random, traceback, numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from chatbot_utils import load_chatbot_resources, bag_of_words
import chatbot_utils

from external_api import get_weather, get_travel_recommendations
from algorithm import generate_itinerary, load_attractions
from packing_algorithm import PackingAlgorithm  

load_dotenv()
app = Flask(__name__)
CORS(app)
print("🔄 Loading chatbot resources...")
load_chatbot_resources()
print("✅ Chatbot resources loaded successfully")
print("Words:", len(chatbot_utils.words))
print("Classes:", len(chatbot_utils.classes))
print("Intents:", len(chatbot_utils.knowledge_base))


@app.route('/api/ml/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK', 'service': 'ML Server'})

@app.route('/api/ml/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"reply": "Please send a message."})

        print("User message:", user_message)

        # Weather intent
        if "weather" in user_message.lower() or "temperature" in user_message.lower():
            # Extract location (default to Pokhara if not specified)
            if "pokhara" in user_message.lower():
                location = "Pokhara"
            else:
                # crude split, you can improve with NLP
                location = user_message.split("in")[-1].strip()
            bot_response = get_weather(location)

        # Travel recommendations intent
        elif "travel" in user_message.lower() or "recommend" in user_message.lower():
            if "pokhara" in user_message.lower():
                location = "Pokhara"
            else:
                location = user_message.split("to")[-1].strip()
            bot_response = get_travel_recommendations(location)

        # ML model intent prediction
        else:
            bow = bag_of_words(user_message, chatbot_utils.words)
            res = chatbot_utils.chat_model.predict(np.array([bow]), verbose=0)[0]
            results = [[i, r] for i, r in enumerate(res) if r > 0.1]
            results.sort(key=lambda x: x[1], reverse=True)

            print("Prediction vector:", res)
            print("Filtered results:", results)

            predicted_tag = chatbot_utils.classes[results[0][0]] if results else None
            bot_response = ""

            if predicted_tag:
                for intent in chatbot_utils.knowledge_base:
                    if intent['tag'] == predicted_tag:
                        bot_response = random.choice(intent['responses'])
                        break

            if not bot_response:
                bot_response = "Sorry, I don't have information on that yet."

        return jsonify({"reply": bot_response})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"reply": "Error processing your request."})



# Existing itinerary and packing endpoints
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

@app.route('/api/ml/attractions', methods=['GET'])
def get_attractions():
    city = request.args.get('city')
    attractions = load_attractions()
    if city:
        attractions = [a for a in attractions if a['city'].lower() == city.lower()]
    return jsonify({'attractions': attractions})

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

if __name__ == '__main__':
    print("🚀 Starting ML Server on port 5000...")
    app.run(port=5000, debug=True)
