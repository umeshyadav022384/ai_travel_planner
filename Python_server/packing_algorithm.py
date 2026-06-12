"""
PACKING ALGORITHM - Rule-Based Decision Tree
All logic is HERE, not in React component
"""

class PackingAlgorithm:
    
    @staticmethod
    def generate_packing_list(weather_forecast, destination, activities=None):
        """
        Generate packing list using Rule-Based Decision Tree
        
        weather_forecast = [
            {'temp': 22, 'rain': 10, 'condition': 'sunny', 'wind': 5, 'date': '2024-06-01'},
            {'temp': 20, 'rain': 80, 'condition': 'rainy', 'wind': 15, 'date': '2024-06-02'},
            {'temp': 25, 'rain': 0, 'condition': 'sunny', 'wind': 8, 'date': '2024-06-03'}
        ]
        """
        
        # Calculate overall weather patterns
        temps = [day['temp'] for day in weather_forecast]
        rains = [day['rain'] for day in weather_forecast]
        conditions = [day.get('condition', 'sunny').lower() for day in weather_forecast]
        
        avg_temp = sum(temps) / len(temps)
        max_temp = max(temps)
        min_temp = min(temps)
        max_rain = max(rains)
        has_rain = max_rain > 30
        has_heavy_rain = max_rain > 70
        has_sunny = any(c in ['sunny', 'clear'] for c in conditions)
        has_cold = any(t < 15 for t in temps)
        has_hot = any(t > 28 for t in temps)
        has_windy = any(day.get('wind', 0) > 20 for day in weather_forecast)
        
        # Initialize packing list
        packing = {
            'essentials': [],
            'weather_based': [],
            'recommended': [],
            'optional': [],
            'alerts': []
        }
        
        # ========== RULE 1: ESSENTIALS (Always include) ==========
        packing['essentials'] = [
            "📱 Phone & Charger",
            "💳 Wallet/Cash/Cards",
            "🪪 ID/Passport",
            "💊 Basic medical kit",
            "🔑 Hotel keys/cards"
        ]
        
        # ========== RULE 2: TEMPERATURE BASED (Rule-Based Decision Tree) ==========
        if has_hot:
            packing['weather_based'].append({"item": "🧴 Sunscreen SPF 50+", "reason": f"Hot weather up to {max_temp}°C"})
            packing['weather_based'].append({"item": "🧢 Wide-brim Hat", "reason": "Sun protection"})
            packing['weather_based'].append({"item": "💧 Reusable Water Bottle", "reason": "Stay hydrated"})
            packing['weather_based'].append({"item": "👕 Light cotton t-shirts", "reason": "Hot weather"})
            packing['weather_based'].append({"item": "🩳 Shorts", "reason": "Hot weather"})
            packing['alerts'].append(f"☀️ Heat alert! {max_temp}°C expected. Stay hydrated and use sunscreen.")
            
        elif has_cold:
            packing['weather_based'].append({"item": "🧥 Warm jacket", "reason": f"Cold weather down to {min_temp}°C"})
            packing['weather_based'].append({"item": "🧣 Scarf", "reason": "Warmth"})
            packing['weather_based'].append({"item": "🧤 Gloves", "reason": "Cold protection"})
            packing['weather_based'].append({"item": "🧢 Beanie hat", "reason": "Keep head warm"})
            packing['weather_based'].append({"item": "👖 Thermal layers", "reason": "Extra warmth"})
            packing['alerts'].append(f"❄️ Cold alert! {min_temp}°C expected. Pack warm layers.")
            
        else:
            # Moderate weather (15-28°C)
            packing['weather_based'].append({"item": "👕 Light t-shirts", "reason": "Comfortable temperature"})
            packing['weather_based'].append({"item": "🧥 Light jacket for evening", "reason": f"Evenings around {min_temp}°C"})
            packing['weather_based'].append({"item": "👖 Comfortable pants", "reason": "Daytime activities"})
        
        # ========== RULE 3: RAIN BASED (Rule-Based Decision Tree) ==========
        if has_heavy_rain:
            packing['weather_based'].append({"item": "☔ Sturdy Umbrella", "reason": f"Heavy rain ({max_rain}%) expected"})
            packing['weather_based'].append({"item": "🧥 Waterproof Raincoat", "reason": "Stay dry"})
            packing['weather_based'].append({"item": "👢 Waterproof boots", "reason": "Wet conditions"})
            packing['weather_based'].append({"item": "💧 Quick-dry clothes", "reason": "Rainy days"})
            packing['alerts'].append(f"🌧️ Heavy rain alert! {max_rain}% chance. Carry umbrella and raincoat.")
            
        elif has_rain:
            packing['weather_based'].append({"item": "☔ Umbrella", "reason": f"Rain possible ({max_rain}%)"})
            packing['weather_based'].append({"item": "🧥 Light rain jacket", "reason": "Light rain protection"})
            packing['alerts'].append(f"☔ Rain alert! {max_rain}% chance. Carry umbrella.")
        
        # ========== RULE 4: SUN/WIND BASED (Rule-Based Decision Tree) ==========
        if has_sunny:
            packing['weather_based'].append({"item": "🕶️ Sunglasses", "reason": "Sunny days"})
            packing['weather_based'].append({"item": "🧴 Sunscreen", "reason": "UV protection"})
        
        if has_windy:
            packing['weather_based'].append({"item": "🧥 Windbreaker jacket", "reason": "Windy conditions"})
            packing['alerts'].append("💨 Windy conditions expected. Secure loose items.")
        
        # ========== RULE 5: ACTIVITY BASED (if activities provided) ==========
        if activities:
            if 'trekking' in str(activities).lower() or 'hiking' in str(activities).lower():
                packing['recommended'].append("🥾 Hiking boots")
                packing['recommended'].append("🎒 Day backpack")
                packing['recommended'].append("🍫 Energy bars/snacks")
                packing['recommended'].append("🧴 Insect repellent")
            
            if 'beach' in str(activities).lower() or 'swimming' in str(activities).lower():
                packing['recommended'].append("🩱 Swimsuit")
                packing['recommended'].append("🧴 Waterproof phone case")
                packing['recommended'].append("🧣 Quick-dry towel")
            
            if 'photography' in str(activities).lower():
                packing['recommended'].append("📷 Camera with extra battery")
                packing['recommended'].append("🔭 Tripod")
        
        # ========== RULE 6: RECOMMENDED (Always good to have) ==========
        packing['recommended'].extend([
            "👟 Comfortable walking shoes",
            "🔋 Power bank",
            "🎒 Day backpack",
            "🧴 Hand sanitizer",
            "📖 Book/Kindle (for downtime)"
        ])
        
        # ========== RULE 7: OPTIONAL ==========
        packing['optional'] = [
            "💻 Laptop/Tablet",
            "🎧 Headphones",
            "📸 GoPro/Action camera",
            "🧘 Travel pillow",
            "🔒 Luggage lock"
        ]
        
        # ========== RULE 8: DESTINATION SPECIFIC ==========
        if destination.lower() == 'pokhara':
            packing['recommended'].append("📷 Camera (Annapurna views)")
            packing['recommended'].append("🪪 Trekking permit (if trekking)")
        elif destination.lower() == 'chitwan':
            packing['recommended'].append("🦟 Strong insect repellent")
            packing['recommended'].append("👕 Neutral color clothes (for safari)")
        elif destination.lower() == 'lumbini':
            packing['recommended'].append("🧣 Modest clothing (temples)")
        
        # Add tips
        packing['tips'] = [
            f"Average temperature: {avg_temp:.0f}°C",
            f"Pack layers for temperature variations",
            "Check weather forecast before departure"
        ]
        
        return packing