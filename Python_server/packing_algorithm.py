"""
PACKING ALGORITHM - Rule-Based Decision Tree
"""

class PackingAlgorithm:
    
    @staticmethod
    def generate_packing_list(weather_forecast, destination, activities=None):
        """
        Generate packing list using Rule-Based Decision Tree
        """
        # If no weather data, return default
        if not weather_forecast:
            return {
                'essentials': ["📱 Phone & Charger", "💳 Wallet/Cash/Cards", "🪪 ID/Passport"],
                'weather_based': [],
                'recommended': ["👟 Comfortable walking shoes"],
                'optional': [],
                'alerts': [],
                'tips': ["Check weather forecast before departure"]
            }
        
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
            'alerts': [],
            'tips': []
        }
        
        # RULE 1: ESSENTIALS (Always include)
        packing['essentials'] = [
            "📱 Phone & Charger",
            "💳 Wallet/Cash/Cards",
            "🪪 ID/Passport",
            "💊 Basic medical kit",
            "🔑 Hotel keys/cards"
        ]
        
        # RULE 2: TEMPERATURE BASED
        if has_hot:
            packing['weather_based'].append({"item": "🧴 Sunscreen SPF 50+", "reason": f"Hot weather up to {max_temp}°C"})
            packing['weather_based'].append({"item": "🧢 Wide-brim Hat", "reason": "Sun protection"})
            packing['weather_based'].append({"item": "💧 Reusable Water Bottle", "reason": "Stay hydrated"})
            packing['weather_based'].append({"item": "👕 Light cotton t-shirts", "reason": "Hot weather"})
            packing['alerts'].append(f"☀️ Heat alert! {max_temp}°C expected. Stay hydrated.")
        elif has_cold:
            packing['weather_based'].append({"item": "🧥 Warm jacket", "reason": f"Cold weather down to {min_temp}°C"})
            packing['weather_based'].append({"item": "🧣 Scarf", "reason": "Warmth"})
            packing['alerts'].append(f"❄️ Cold alert! {min_temp}°C expected. Pack warm layers.")
        else:
            packing['weather_based'].append({"item": "👕 Light t-shirts", "reason": "Comfortable temperature"})
            packing['weather_based'].append({"item": "🧥 Light jacket for evening", "reason": f"Evenings around {min_temp}°C"})
        
        # RULE 3: RAIN BASED
        if has_heavy_rain:
            packing['weather_based'].append({"item": "☔ Sturdy Umbrella", "reason": f"Heavy rain ({max_rain}%) expected"})
            packing['weather_based'].append({"item": "🧥 Waterproof Raincoat", "reason": "Stay dry"})
            packing['alerts'].append(f"🌧️ Heavy rain alert! {max_rain}% chance.")
        elif has_rain:
            packing['weather_based'].append({"item": "☔ Umbrella", "reason": f"Rain possible ({max_rain}%)"})
            packing['alerts'].append(f"☔ Rain alert! {max_rain}% chance.")
        
        # RULE 4: SUN/WIND BASED
        if has_sunny:
            packing['weather_based'].append({"item": "🕶️ Sunglasses", "reason": "Sunny days"})
        
        if has_windy:
            packing['weather_based'].append({"item": "🧥 Windbreaker jacket", "reason": "Windy conditions"})
        
        # RULE 5: ACTIVITY BASED
        if activities:
            activities_str = str(activities).lower()
            if 'trekking' in activities_str or 'hiking' in activities_str:
                packing['recommended'].append("🥾 Hiking boots")
                packing['recommended'].append("🎒 Day backpack")
        
        # RULE 6: RECOMMENDED
        packing['recommended'].extend([
            "👟 Comfortable walking shoes",
            "🔋 Power bank",
            "🧴 Hand sanitizer"
        ])
        
        # RULE 7: DESTINATION SPECIFIC
        if destination and destination.lower() == 'pokhara':
            packing['recommended'].append("📷 Camera (Annapurna views)")
        
        # Tips
        packing['tips'] = [
            f"Average temperature: {avg_temp:.0f}°C",
            "Pack layers for temperature variations",
            "Check weather forecast before departure"
        ]
        
        return packing