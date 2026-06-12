from flask import Flask, request, jsonify
from flask_cors import CORS
from algorithm import generate_itinerary, load_attractions

app = Flask(__name__)
CORS(app)

@app.route('/api/ml/generate', methods=['POST'])
def generate():
    data = request.json
    destination = data.get('destination')
    preferences = data.get('preferences', {})
    days = data.get('days', 3)
    budget = data.get('budget', 500)
    
    daily_budget = budget // days
    
    itinerary = generate_itinerary(destination, preferences, days, daily_budget)
    
    return jsonify({
        'success': True,
        'destination': destination,
        'days': days,
        'dailyActivities': itinerary,
        'totalCost': budget
    })

@app.route('/api/ml/attractions', methods=['GET'])
def get_attractions():
    city = request.args.get('city')
    attractions = load_attractions()
    
    if city:
        attractions = [a for a in attractions if a['city'].lower() == city.lower()]
    
    return jsonify({'attractions': attractions})

if __name__ == '__main__':
    print("🚀 Starting ML Server on port 5000...")
    app.run(port=5000, debug=True)