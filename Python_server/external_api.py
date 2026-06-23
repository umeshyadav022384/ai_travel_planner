import os
import requests

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

def get_weather(location):
    if not OPENWEATHER_API_KEY:
        return "⚠️ Weather API key not set."

    url = f"http://api.openweathermap.org/data/2.5/weather?q={location},np&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)

    try:
        data = response.json()
        if response.status_code == 200 and "main" in data:
            temp = data["main"]["temp"]
            condition = data["weather"][0]["description"]
            return f"Weather in {location}: {temp}°C, {condition}"
        else:
            return f"⚠️ Error fetching weather: {data.get('message', 'Unknown error')}"
    except Exception as e:
        return f"⚠️ Exception occurred: {str(e)}"

def get_travel_recommendations(city):
    api_key = os.environ.get("RAPIDAPI_KEY")
    url = f"https://travel-api.example.com/recommendations?city={city}&apikey={api_key}"
    response = requests.get(url).json()

    if "recommendations" in response:
        # Take top 3 and format nicely
        recs = response["recommendations"][:3]
        formatted = "\n".join([f"• {place}" for place in recs])
        return f"Top places to visit in {city}:\n{formatted}"
    else:
        return f"⚠️ Sorry, I couldn’t fetch travel recommendations for {city}."

