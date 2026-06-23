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


import os
import requests

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")


# ==========================================
# WEATHER API
# ==========================================
def get_weather(location):
    try:
        if not OPENWEATHER_API_KEY:
            return "⚠️ Weather API key not configured."

        url = "https://api.openweathermap.org/data/2.5/weather"

        params = {
            "q": location,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200:
            return f"⚠️ Could not find weather information for {location}."

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["description"]

        return (
            f"🌤 Weather in {location}\n"
            f"🌡 Temperature: {temp}°C\n"
            f"🤗 Feels Like: {feels_like}°C\n"
            f"💧 Humidity: {humidity}%\n"
            f"☁️ Condition: {condition}"
        )

    except Exception as e:
        print("Weather Error:", str(e))
        return "⚠️ Unable to fetch weather information right now."


# ==========================================
# TRAVEL RECOMMENDATION API
# ==========================================
def get_travel_recommendations(location):
    try:

        if not RAPIDAPI_KEY:
            return "⚠️ RapidAPI key not configured."

        url = "https://travel-advisor.p.rapidapi.com/locations/search"

        querystring = {
            "query": location,
            "limit": "10",
            "offset": "0",
            "lang": "en_US",
            "currency": "USD"
        }

        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "travel-advisor.p.rapidapi.com"
        }

        response = requests.get(
            url,
            headers=headers,
            params=querystring,
            timeout=15
        )

        if response.status_code != 200:
            print("Travel API Error:", response.text)
            return f"⚠️ Unable to fetch travel recommendations for {location}."

        data = response.json()

        results = data.get("data", [])

        if not results:
            return f"No places found in {location}."

        places = []

        for item in results:

            obj = item.get("result_object", {})

            place_name = obj.get("name")

            if place_name and place_name not in places:
                places.append(place_name)

        if not places:
            return f"No tourist attractions found in {location}."

        response_text = f"🏞 Recommended places in {location}:\n\n"

        for place in places[:10]:
            response_text += f"• {place}\n"

        return response_text

    except Exception as e:
        print("Travel API Error:", str(e))
        return "⚠️ Unable to fetch travel recommendations right now."