from flask import Flask, request, jsonify
from flask_cors import CORS
from algorithm import generate_itinerary, load_attractions
from packing_algorithm import PackingAlgorithm  
app = Flask(__name__)
CORS(app)

# Health check endpoint
@app.route('/api/ml/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK', 'service': 'ML Server'})

@app.route('/api/ml/generate', methods=['POST'])
def generate():
    print("🔥🔥🔥 /api/ml/generate endpoint was called! 🔥🔥🔥")

    data = request.json
    print("Received data:", data)

    destination = data.get('destination')
    preferences = data.get('preferences', {})
    days = data.get('days', 3)
    budget = int(data.get('budget', 500))

    print("Destination:", destination)
    print("Days:", days)
    print("Budget:", budget)

    daily_budget = budget // days

    itinerary = generate_itinerary(destination, preferences, days, daily_budget)

    print("Generated itinerary days:", len(itinerary))

    return jsonify({
        'success': True,
        'destination': destination,
        'days': days,
        'dailyActivities': itinerary,
        'totalCost': budget
    })

# Attractions endpoint
@app.route('/api/ml/attractions', methods=['GET'])
def get_attractions():
    city = request.args.get('city')
    attractions = load_attractions()
    
    if city:
        attractions = [a for a in attractions if a['city'].lower() == city.lower()]
    
    return jsonify({'attractions': attractions})

# ✅ NEW: Packing list endpoint (Fixes the 404 error)
@app.route('/api/ml/packing', methods=['POST'])
def get_packing_list():
    try:
        data = request.json
        weather_data = data.get('weatherData', {})
        destination = data.get('destination', '')
        activities = data.get('activities', [])
        preferences = data.get('preferences', {})
        
        # Convert weather data format for packing algorithm
        weather_forecast = []
        for day in weather_data.get('days', []):
            weather_forecast.append({
                'temp': day.get('tempmax', 25),
                'rain': day.get('precip', 0),
                'condition': day.get('conditions', 'sunny').lower(),
                'wind': day.get('windspeed', 10),
                'date': day.get('datetime', '')
            })
        
        # Call packing algorithm
        packing_result = PackingAlgorithm.generate_packing_list(
            weather_forecast=weather_forecast,
            destination=destination,
            activities=activities
        )
        
        # Calculate weather summary
        has_rain = any(day.get('rain', 0) > 30 for day in weather_forecast)
        max_temp = max([day.get('temp', 0) for day in weather_forecast]) if weather_forecast else 25
        min_temp = min([day.get('temp', 100) for day in weather_forecast]) if weather_forecast else 15
        
        return jsonify({
            'success': True,
            'packingList': packing_result,
            'weatherSummary': {
                'hasRain': has_rain,
                'maxTemp': max_temp,
                'minTemp': min_temp
            }
        })
    except Exception as e:
        print(f"Error in packing endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting ML Server on port 5000...")
    app.run(port=5000, debug=True)