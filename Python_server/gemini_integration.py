# Python_server/gemini_integration.py

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import re
import time
import random

load_dotenv()

# ==========================================
# GLOBAL RATE LIMITER
# ==========================================

_last_gemini_call = 0
MIN_GEMINI_INTERVAL = 15  # 15 seconds between calls


class GeminiIntegration:
    def __init__(self):
        api_key = os.environ.get('GEMINI_API_KEY')
        
        if not api_key:
            print("⚠️ GEMINI_API_KEY not found")
            self.model = None
            return
        
        try:
            genai.configure(api_key=api_key)
            model_name = os.environ.get('GEMINI_MODEL', 'gemini-3.6-flash')
            self.model = genai.GenerativeModel(model_name)
            print(f"✅ Gemini initialized with {model_name}")
        except Exception as e:
            print(f"⚠️ Gemini error: {e}")
            self.model = None

    # ==========================================
    # RATE LIMITER
    # ==========================================
    
    def _wait_if_needed(self):
        """Wait if we're making too many requests per minute"""
        global _last_gemini_call
        
        now = time.time()
        time_since_last = now - _last_gemini_call
        
        if time_since_last < MIN_GEMINI_INTERVAL:
            wait_time = MIN_GEMINI_INTERVAL - time_since_last
            print(f"⏳ Gemini rate limiter: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        _last_gemini_call = time.time()

    # ==========================================
    # Generate trip overview
    # ==========================================
    
    def generate_trip_overview(self, destination, days, preferences, attractions_count):
        """Generate a warm trip overview with rate limit handling."""
        if not self.model:
            return None
        
        self._wait_if_needed()
        
        # Check if we have a cached version
        cache_key = f"overview_{destination}_{days}"
        
        try:
            pref_text = ""
            if preferences:
                pref_map = {
                    'art': 'art and culture',
                    'history': 'history and heritage', 
                    'nature': 'nature and outdoors',
                    'food': 'local cuisine and food experiences',
                    'adventure': 'adventure and outdoor activities'
                }
                prefs = [pref_map.get(k, k) for k, v in preferences.items() if v and v > 5]
                if prefs:
                    pref_text = f" with a special focus on {', '.join(prefs)}"
            
            prompt = f"""
            Write a warm, engaging, and inspiring trip overview (3-4 sentences) for a {days}-day trip to {destination}, Nepal{pref_text}.
            The itinerary includes {attractions_count} attractions.
            Make it sound like a personal welcome from a knowledgeable local guide.
            Use natural, conversational language. Be enthusiastic and inviting.
            Don't use markdown or bold text. Just plain text.
            Start with a warm welcome to {destination}.
            End with an encouraging note about the adventure ahead.
            """
            
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
                
        except Exception as e:
            if '429' in str(e):
                print(f"⏳ Gemini rate limit exceeded. Please wait 60 seconds.")
            else:
                print(f"⚠️ Gemini error: {e}")
        
        return None

    # ==========================================
    # Generate description for a single attraction
    # ==========================================
    
    def generate_description(self, activity_name, destination):
        """Generate a short description for a single attraction."""
        if not self.model:
            return None
        
        self._wait_if_needed()
        
        try:
            prompt = f"""
            Write a short, engaging description (2-3 sentences) for this attraction:
            - Name: {activity_name}
            - Location: {destination}
            Make it sound interesting and tourist-friendly. No markdown, just plain text.
            """
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            if '429' in str(e):
                print(f"⏳ Rate limited for '{activity_name}'")
            else:
                print(f"⚠️ Gemini description error: {e}")
        return None

    # ==========================================
    # Generate dinner description for a specific day
    # ==========================================
    
    def generate_dinner_description(self, destination, day_num, total_days):
        """Generate a dinner description for a specific day."""
        if not self.model:
            return None
        
        self._wait_if_needed()
        
        try:
            day_context = "beginning" if day_num == 1 else "middle" if day_num < total_days else "final"
            prompt = f"""
            Write a short, engaging dinner description for day {day_num} of a {total_days}-day trip to {destination}.
            This is the {day_context} of the trip.
            Make it sound delicious and authentic.
            2-3 sentences only. No markdown.
            """
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            if '429' in str(e):
                print(f"⏳ Rate limited for dinner description (day {day_num})")
            else:
                print(f"⚠️ Gemini dinner description error: {e}")
        return None

    # ==========================================
    # Enhance full itinerary
    # ==========================================
    
    def enhance_itinerary(self, itinerary_data, destination, days, preferences=None, weather_forecast=None, daily_costs=None, restaurants=None, hotels=None):
        """Enhance itinerary with Gemini using real data"""
        if not self.model or not itinerary_data:
            return None
        
        self._wait_if_needed()
        
        try:
            itinerary_text = self._format_itinerary_for_prompt(itinerary_data)
            
            weather_text = ""
            if weather_forecast:
                weather_text = "\nWeather Forecast:\n"
                for i, day_weather in enumerate(weather_forecast):
                    temp = round(day_weather.get('temp', 25))
                    condition = day_weather.get('condition', 'sunny')
                    rain = day_weather.get('rain', 0)
                    weather_text += f"Day {i+1}: {temp}°C, {condition}, {rain}% rain\n"
            
            cost_text = ""
            if daily_costs:
                cost_text = "\nBudget Info:\n"
                for i, cost in enumerate(daily_costs):
                    cost_text += f"Day {i+1}: ${cost} used\n"
                cost_text += f"Total: ${sum(daily_costs)}\n"
            
            restaurant_text = ""
            if restaurants:
                restaurant_text = "\nAvailable Restaurants:\n"
                for r in restaurants[:5]:
                    restaurant_text += f"- {r.get('name')}: {r.get('cuisine', 'N/A')} ({r.get('price_range', 'N/A')})\n"
            
            hotel_text = ""
            if hotels:
                hotel_text = "\nAvailable Hotels:\n"
                for h in hotels[:5]:
                    hotel_text += f"- {h.get('name')}: {h.get('rating', 'N/A')} stars, ${h.get('price', 'N/A')}\n"
            
            prompt = f"""
You are TravelPal Nepal. Enhance this {days}-day itinerary for {destination}.

{weather_text}
{cost_text}
{restaurant_text}
{hotel_text}

TECHNICAL ITINERARY:
{itinerary_text}

IMPORTANT RULES:
1. Use REAL restaurant names from the list above for meals
2. Use REAL hotel names from the list above for hotel stays
3. Keep the EXACT costs from the technical itinerary
4. Add engaging descriptions
5. Format: "🍽️ [Restaurant Name]: Try their [specific dish]"
6. Hotel: "🏨 [Hotel Name]: Amenities include..."

Return JSON:
{{
  "introduction": "Welcome to {destination}!",
  "daily_itineraries": [
    {{
      "day": 1,
      "title": "Day 1: Exploring",
      "enhanced_activities": [
        {{
          "time": "09:00 AM",
          "title": "Activity Name",
          "description": "Description with cost 💰 Free or 💰 $X"
        }},
        {{
          "time": "12:00 PM",
          "title": "Lunch at [Restaurant Name]",
          "description": "Description... 💰 $X",
          "food_tip": "🍽️ [Restaurant Name]: Try their [specific dish]"
        }},
        {{
          "time": "09:00 PM",
          "title": "Stay at [Hotel Name]",
          "description": "Hotel description... 💰 $X"
        }}
      ],
      "day_summary": "Summary..."
    }}
  ],
  "final_tips": "Practical tips"
}}

Only valid JSON, no other text.
"""
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                return None
            
            return self._parse_response(response.text)
            
        except Exception as e:
            if '429' in str(e):
                print(f"⏳ Rate limited for enhancement. Try again later.")
            else:
                print(f"⚠️ Gemini enhancement error: {e}")
            return None
    
    def _format_itinerary_for_prompt(self, itinerary_data):
        text = ""
        for day in itinerary_data:
            day_num = day.get('day', 1)
            text += f"\nDay {day_num}:\n"
            for activity in day.get('activities', []):
                time = activity.get('time', 'Flexible')
                title = activity.get('title', '')
                desc = activity.get('description', '')
                cost = activity.get('cost', 0)
                is_meal = activity.get('is_meal', False)
                is_hotel = activity.get('is_hotel', False)
                type_label = "[MEAL]" if is_meal else "[HOTEL]" if is_hotel else "[ACTIVITY]"
                text += f"  {time} {type_label} - {title}: {desc} (${cost})\n"
        return text
    
    def _parse_response(self, response_text):
        try:
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0]
            else:
                json_str = response_text
            
            data = json.loads(json_str.strip())
            
            if 'daily_itineraries' in data:
                for day in data['daily_itineraries']:
                    if 'enhanced_activities' in day:
                        for activity in day['enhanced_activities']:
                            if 'food_tip' in activity:
                                food_tip = activity['food_tip']
                                food_tip = re.sub(r'🍽️\s*🍽️', '🍽️', food_tip)
                                food_tip = ' '.join(food_tip.split())
                                activity['food_tip'] = food_tip
            
            return data
        except Exception as e:
            print(f"⚠️ Parse error: {e}")
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return None


# ==========================================
# CREATE SINGLE GLOBAL INSTANCE
# ==========================================

gemini = GeminiIntegration()