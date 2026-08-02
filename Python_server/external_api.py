# Python_server/external_api.py

import os
import requests
import json
import re
from datetime import datetime

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")


# ==========================================
# HELPER: Get location ID from city name (MULTIPLE METHODS)
# ==========================================

def get_location_id(city_name):
    """
    Convert a city name to a numeric locationId using Travel Advisor API.
    Tries multiple methods to find the location ID.
    """
    if not RAPIDAPI_KEY:
        print("⚠️ RAPIDAPI_KEY not configured")
        return None
    
    # Method 1: Auto-complete endpoint
    url = "https://travel-advisor.p.rapidapi.com/locations/v2/auto-complete"
    querystring = {
        "query": city_name,
        "lang": "en_US",
        "units": "km"
    }
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "travel-advisor.p.rapidapi.com"
    }
    
    try:
        print(f"🔍 Looking up location ID for: {city_name}")
        
        # Try auto-complete first
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        print(f"📡 Auto-complete status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Try different response structures
            results = []
            
            # Structure 1: Typeahead_autocomplete
            auto_complete = data.get("data", {}).get("Typeahead_autocomplete", {})
            results = auto_complete.get("results", [])
            
            # Structure 2: data.data
            if not results:
                results = data.get("data", [])
                if not isinstance(results, list):
                    results = []
            
            # Structure 3: data.results
            if not results:
                results = data.get("results", [])
            
            print(f"📊 Found {len(results)} results")
            
            if results:
                # Try to find location_id in first result
                first_result = results[0]
                
                # Check detailsV2
                details_v2 = first_result.get("detailsV2", {})
                location_id = details_v2.get("locationId")
                
                # Check result_object
                if not location_id:
                    result_obj = first_result.get("result_object", {})
                    location_id = result_obj.get("location_id")
                
                # Check direct fields
                if not location_id:
                    location_id = first_result.get("location_id") or first_result.get("id") or first_result.get("locationId")
                
                if location_id:
                    print(f"✅ Found location ID: {location_id} for {city_name}")
                    return location_id
                
                # Search through all results for matching name
                city_lower = city_name.lower()
                for item in results:
                    item_name = item.get("name", "").lower()
                    details = item.get("detailsV2", {})
                    names = details.get("names", {})
                    name2 = names.get("name", "").lower()
                    
                    if city_lower in item_name or city_lower in name2 or item_name == city_lower:
                        location_id = details.get("locationId") or item.get("location_id") or item.get("id")
                        if location_id:
                            print(f"✅ Found location ID: {location_id} for {city_name}")
                            return location_id
        
        # Method 2: Try locations/search endpoint
        print(f"🔄 Trying alternative endpoint for {city_name}...")
        search_url = "https://travel-advisor.p.rapidapi.com/locations/search"
        search_params = {
            "query": city_name,
            "limit": "5",
            "offset": "0",
            "lang": "en_US",
            "currency": "USD"
        }
        search_response = requests.get(search_url, headers=headers, params=search_params, timeout=10)
        print(f"📡 Search status: {search_response.status_code}")
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            search_results = search_data.get("data", [])
            
            for item in search_results[:5]:
                obj = item.get("result_object", {})
                location_id = obj.get("location_id")
                if location_id:
                    print(f"✅ Found location ID via search: {location_id} for {city_name}")
                    return location_id
        
        # Method 3: Try with "Nepal" suffix
        print(f"🔄 Trying with 'Nepal' suffix...")
        nepal_response = requests.get(
            url, 
            headers=headers, 
            params={"query": f"{city_name}, Nepal", "lang": "en_US", "units": "km"},
            timeout=10
        )
        
        if nepal_response.status_code == 200:
            nepal_data = nepal_response.json()
            auto_complete = nepal_data.get("data", {}).get("Typeahead_autocomplete", {})
            results = auto_complete.get("results", [])
            
            if results:
                first_result = results[0]
                details_v2 = first_result.get("detailsV2", {})
                location_id = details_v2.get("locationId")
                if location_id:
                    print(f"✅ Found location ID with Nepal suffix: {location_id} for {city_name}")
                    return location_id
        
        print(f"⚠️ Could not find location ID for {city_name}")
        return None
        
    except Exception as e:
        print(f"❌ Location ID fetch error: {e}")
        import traceback
        traceback.print_exc()
        return None


# ==========================================
# WEATHER API
# ==========================================

def get_weather(location):
    try:
        if not OPENWEATHER_API_KEY:
            return "⚠️ Weather API key not configured."

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": location, "appid": OPENWEATHER_API_KEY, "units": "metric"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200:
            return f"⚠️ Could not find weather information for {location}."

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["description"]

        return (
            f" Weather in {location}\n"
            f" Temperature: {temp}°C\n"
            f" Feels Like: {feels_like}°C\n"
            f" Humidity: {humidity}%\n"
            f" Condition: {condition}"
        )
    except Exception as e:
        print("Weather Error:", str(e))
        return "⚠️ Unable to fetch weather information right now."


# ==========================================
# TRAVEL RECOMMENDATIONS
# ==========================================

def get_travel_recommendations(location):
    try:
        if not RAPIDAPI_KEY:
            return "⚠️ RapidAPI key not configured."
        url = "https://travel-advisor.p.rapidapi.com/locations/v2/auto-complete"
        querystring = {"query": location, "lang": "en_US", "units": "km"}
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "travel-advisor.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        if response.status_code != 200:
            print("Travel API Error:", response.text)
            return f"⚠️ Unable to fetch travel recommendations for {location}."

        data = response.json()
        auto_complete = data.get("data", {}).get("Typeahead_autocomplete", {})
        results = auto_complete.get("results", [])
        
        if not results:
            return f"No places found in {location}."

        places = []
        for item in results[:10]:
            details = item.get("detailsV2", {})
            names = details.get("names", {})
            place_name = names.get("name") or item.get("name")
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


# ==========================================
# HELPER: Get coordinates
# ==========================================

def get_coordinates(city_name):
    """Convert city name to latitude/longitude using Trueway Geocoding."""
    if not RAPIDAPI_KEY:
        return None, None
    
    url = "https://trueway-geocoding.p.rapidapi.com/Geocode"
    querystring = {"address": f"{city_name}, Nepal", "language": "en"}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "trueway-geocoding.p.rapidapi.com"
    }
    
    try:
        print(f"🔍 Getting coordinates for: {city_name}")
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        print(f"📡 Geocode status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Geocode error: {response.text}")
            return None, None
        
        data = response.json()
        results = data.get("results", [])
        
        if results:
            location = results[0].get("location", {})
            lat = location.get("lat")
            lng = location.get("lng")
            if lat and lng:
                print(f"✅ Found coordinates: {lat}, {lng} for {city_name}")
                return lat, lng
        
        print(f"⚠️ No coordinates found for {city_name}")
        return None, None
        
    except Exception as e:
        print(f"❌ Geocode error: {e}")
        return None, None


# ==========================================
# SEARCH HOTELS (WORKS FOR ALL CITIES)
# ==========================================

def search_hotels(location, check_in=None, check_out=None, guests=2):
    """
    Search hotels using Travel Advisor API with multiple fallback methods.
    Works for all 13 cities in Nepal.
    """
    try:
        if not RAPIDAPI_KEY:
            print("⚠️ RAPIDAPI_KEY not configured")
            return []

        # Step 1: Get location ID
        location_id = get_location_id(location)
        
        # Step 2: Try various hotel search methods
        hotels = []
        
        # Method A: Search with location ID
        if location_id:
            print(f"🔍 Searching hotels with location ID: {location_id}")
            hotels = search_hotels_by_location_id(location_id, location)
        
        # Method B: Search by coordinates
        if not hotels:
            print(f"🔄 Trying coordinate-based search...")
            lat, lng = get_coordinates(location)
            if lat and lng:
                hotels = search_hotels_by_latlng(lat, lng, location)
        
        # Method C: Search with location name
        if not hotels:
            print(f"🔄 Trying name-based search...")
            hotels = search_hotels_by_name(location)
        
        return hotels
        
    except Exception as e:
        print(f"❌ Hotel API Error: {e}")
        import traceback
        traceback.print_exc()
        return []


def search_hotels_by_location_id(location_id, location_name):
    """Search hotels using location ID."""
    try:
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "travel-advisor.p.rapidapi.com"
        }
        
        # Try different endpoints
        endpoints = [
            f"https://travel-advisor.p.rapidapi.com/hotels/list?locationId={location_id}&limit=15&currency=USD&lang=en_US",
            f"https://travel-advisor.p.rapidapi.com/locations/search?query={location_name}&limit=15&offset=0&lang=en_US&currency=USD"
        ]
        
        for url in endpoints:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("data", [])
                    
                    hotels = []
                    for item in results[:15]:
                        obj = item.get("result_object", {})
                        name = obj.get("name", "")
                        result_type = obj.get("type", "").lower()
                        
                        # Check if it's a hotel
                        is_hotel = (
                            "hotel" in name.lower() or 
                            "resort" in name.lower() or 
                            "lodge" in name.lower() or
                            "hotel" in result_type or
                            "resort" in result_type
                        )
                        
                        if is_hotel and name:
                            hotel = {
                                "name": name,
                                "rating": obj.get("rating", "N/A"),
                                "price": obj.get("price", "Contact for pricing"),
                                "address": obj.get("address", "Address not available"),
                                "latitude": obj.get("latitude", 0),
                                "longitude": obj.get("longitude", 0),
                                "distance": obj.get("distance", "N/A"),
                                "phone": obj.get("phone", "N/A"),
                                "review_count": obj.get("review_count", 0)
                            }
                            hotels.append(hotel)
                            print(f"  🏨 Found hotel: {name}")
                    
                    if hotels:
                        print(f"✅ Found {len(hotels)} hotels via location ID")
                        return hotels
            except:
                continue
        
        return []
    except Exception as e:
        print(f"❌ Location ID hotel search error: {e}")
        return []


def search_hotels_by_latlng(lat, lng, location_name):
    """Search hotels by coordinates."""
    try:
        url = "https://travel-advisor.p.rapidapi.com/hotels/list-by-latlng"
        querystring = {
            "latitude": str(lat),
            "longitude": str(lng),
            "limit": "15",
            "currency": "USD",
            "distance": "20"  # 20km radius
        }
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "travel-advisor.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        print(f"📡 Hotels by lat/lng status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("data", [])
            
            hotels = []
            for item in results[:15]:
                name = item.get("name", "")
                if name and any(word in name.lower() for word in ["hotel", "resort", "lodge", "inn"]):
                    hotel = {
                        "name": name,
                        "rating": item.get("rating", "N/A"),
                        "price": item.get("price", "Contact for pricing"),
                        "address": item.get("address", "Address not available"),
                        "latitude": item.get("latitude", 0),
                        "longitude": item.get("longitude", 0),
                        "distance": item.get("distance", "N/A"),
                        "phone": item.get("phone", "N/A"),
                        "review_count": item.get("review_count", 0)
                    }
                    hotels.append(hotel)
                    print(f"  🏨 Found hotel via lat/lng: {name}")
            
            if hotels:
                print(f"✅ Found {len(hotels)} hotels via lat/lng")
                return hotels
        
        return []
    except Exception as e:
        print(f"❌ Lat/lng hotel search error: {e}")
        return []


def search_hotels_by_name(location_name):
    """Search hotels by name using general search."""
    try:
        url = "https://travel-advisor.p.rapidapi.com/locations/search"
        querystring = {
            "query": f"hotel {location_name}",
            "limit": "15",
            "offset": "0",
            "lang": "en_US",
            "currency": "USD"
        }
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "travel-advisor.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        print(f"📡 Name-based search status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("data", [])
            
            hotels = []
            for item in results[:15]:
                obj = item.get("result_object", {})
                name = obj.get("name", "")
                
                if name and "hotel" in name.lower():
                    hotel = {
                        "name": name,
                        "rating": obj.get("rating", "N/A"),
                        "price": obj.get("price", "Contact for pricing"),
                        "address": obj.get("address", "Address not available"),
                        "latitude": obj.get("latitude", 0),
                        "longitude": obj.get("longitude", 0),
                        "distance": obj.get("distance", "N/A"),
                        "phone": obj.get("phone", "N/A"),
                        "review_count": obj.get("review_count", 0)
                    }
                    hotels.append(hotel)
                    print(f"  🏨 Found hotel via name search: {name}")
            
            if hotels:
                print(f"✅ Found {len(hotels)} hotels via name search")
                return hotels
        
        return []
    except Exception as e:
        print(f"❌ Name-based hotel search error: {e}")
        return []


# ==========================================
# SEARCH RESTAURANTS (WORKS FOR ALL CITIES)
# ==========================================

def search_restaurants(location, cuisine_type=None, limit=5):
    """
    Search restaurants using Travel Advisor API with multiple methods.
    Works for all 13 cities in Nepal.
    """
    try:
        if not RAPIDAPI_KEY:
            print("⚠️ RAPIDAPI_KEY not configured")
            return []

        # Step 1: Get location ID
        location_id = get_location_id(location)
        
        # Step 2: Try various restaurant search methods
        restaurants = []
        
        # Method A: Search with location ID
        if location_id:
            print(f"🔍 Searching restaurants with location ID: {location_id}")
            restaurants = search_restaurants_by_location_id(location_id, location, limit)
        
        # Method B: Search by coordinates
        if not restaurants:
            print(f"🔄 Trying coordinate-based restaurant search...")
            lat, lng = get_coordinates(location)
            if lat and lng:
                restaurants = search_restaurants_by_latlng(lat, lng, limit)
        
        # Method C: Search with location name
        if not restaurants:
            print(f"🔄 Trying name-based restaurant search...")
            restaurants = search_restaurants_by_name(location, limit)
        
        return restaurants
        
    except Exception as e:
        print(f"❌ Restaurant API Error: {e}")
        import traceback
        traceback.print_exc()
        return []


def search_restaurants_by_location_id(location_id, location_name, limit=5):
    """Search restaurants using location ID."""
    try:
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "travel-advisor.p.rapidapi.com"
        }
        
        url = f"https://travel-advisor.p.rapidapi.com/locations/search?query={location_name}&limit=20&offset=0&lang=en_US&currency=USD"
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get("data", [])
            
            restaurants = []
            for item in results[:limit + 5]:
                obj = item.get("result_object", {})
                name = obj.get("name", "")
                result_type = obj.get("type", "").lower()
                
                # Check if it's a restaurant
                is_restaurant = any(t in result_type for t in ["restaurant", "eat", "food", "cafe", "bar", "pub"])
                if is_restaurant or "restaurant" in name.lower():
                    restaurant = {
                        "name": name,
                        "rating": obj.get("rating", "N/A"),
                        "price_range": obj.get("price_range", "$$"),
                        "cuisine": obj.get("cuisine", "N/A"),
                        "address": obj.get("address", "Address not available"),
                        "latitude": obj.get("latitude", 0),
                        "longitude": obj.get("longitude", 0),
                        "distance": obj.get("distance", "N/A"),
                        "phone": obj.get("phone", "N/A"),
                        "review_count": obj.get("review_count", 0)
                    }
                    restaurants.append(restaurant)
                    print(f"  🍽️ Found restaurant: {name}")
                    if len(restaurants) >= limit:
                        break
            
            if restaurants:
                print(f"✅ Found {len(restaurants)} restaurants via location ID")
                return restaurants
        
        return []
    except Exception as e:
        print(f"❌ Location ID restaurant search error: {e}")
        return []


def search_restaurants_by_latlng(lat, lng, limit=5):
    """Search restaurants by coordinates."""
    try:
        url = "https://travel-advisor.p.rapidapi.com/restaurants/list-by-latlng"
        querystring = {
            "latitude": str(lat),
            "longitude": str(lng),
            "limit": str(limit + 5),
            "currency": "USD",
            "distance": "20"  # 20km radius
        }
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "travel-advisor.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        print(f"📡 Restaurants by lat/lng status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("data", [])
            
            restaurants = []
            for item in results[:limit]:
                restaurant = {
                    "name": item.get("name", "Unknown Restaurant"),
                    "rating": item.get("rating", "N/A"),
                    "price_range": item.get("price_range", "$$"),
                    "cuisine": item.get("cuisine", "N/A"),
                    "address": item.get("address", "Address not available"),
                    "latitude": item.get("latitude", 0),
                    "longitude": item.get("longitude", 0),
                    "distance": item.get("distance", "N/A"),
                    "phone": item.get("phone", "N/A"),
                    "review_count": item.get("review_count", 0)
                }
                restaurants.append(restaurant)
                print(f"  🍽️ Found restaurant via lat/lng: {restaurant['name']}")
            
            if restaurants:
                print(f"✅ Found {len(restaurants)} restaurants via lat/lng")
                return restaurants
        
        return []
    except Exception as e:
        print(f"❌ Lat/lng restaurant search error: {e}")
        return []


def search_restaurants_by_name(location_name, limit=5):
    """Search restaurants by name using general search."""
    try:
        url = "https://travel-advisor.p.rapidapi.com/locations/search"
        querystring = {
            "query": location_name,
            "limit": str(limit + 5),
            "offset": "0",
            "lang": "en_US",
            "currency": "USD"
        }
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "travel-advisor.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        print(f"📡 Name-based restaurant search status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("data", [])
            
            restaurants = []
            for item in results[:limit + 5]:
                obj = item.get("result_object", {})
                name = obj.get("name", "")
                
                if name and any(t in name.lower() for t in ["restaurant", "cafe", "bar", "pub", "kitchen", "dining"]):
                    restaurant = {
                        "name": name,
                        "rating": obj.get("rating", "N/A"),
                        "price_range": obj.get("price_range", "$$"),
                        "cuisine": obj.get("cuisine", "N/A"),
                        "address": obj.get("address", "Address not available"),
                        "latitude": obj.get("latitude", 0),
                        "longitude": obj.get("longitude", 0),
                        "distance": obj.get("distance", "N/A"),
                        "phone": obj.get("phone", "N/A"),
                        "review_count": obj.get("review_count", 0)
                    }
                    restaurants.append(restaurant)
                    print(f"  🍽️ Found restaurant via name: {name}")
                    if len(restaurants) >= limit:
                        break
            
            if restaurants:
                print(f"✅ Found {len(restaurants)} restaurants via name search")
                return restaurants
        
        return []
    except Exception as e:
        print(f"❌ Name-based restaurant search error: {e}")
        return []