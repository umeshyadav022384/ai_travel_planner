import json
import pickle
import nltk
import numpy as np
import os
import random
import re
from tensorflow import keras
from tensorflow.keras.preprocessing.sequence import pad_sequences
from nltk.stem import WordNetLemmatizer

# ==========================================
# GLOBALS
# ==========================================
chat_model = None
tokenizer = None
classes = []
knowledge_base = []
city_data = {}
lemmatizer = None
max_len = None

# ==========================================
# NON-NEPAL COUNTRIES LIST
# ==========================================
NON_NEPAL_COUNTRIES = [
    'france', 'india', 'china', 'usa', 'uk', 'united kingdom', 'australia', 
    'canada', 'germany', 'italy', 'spain', 'japan', 'russia',
    'brazil', 'mexico', 'egypt', 'turkey', 'greece', 'portugal',
    'switzerland', 'netherlands', 'belgium', 'sweden', 'norway',
    'denmark', 'finland', 'ireland', 'new zealand', 'singapore',
    'malaysia', 'indonesia', 'thailand', 'vietnam', 'south korea',
    'pakistan', 'bangladesh', 'sri lanka', 'myanmar', 'afghanistan',
    'iran', 'iraq', 'israel', 'saudi arabia', 'uae',
    'south africa', 'kenya', 'nigeria', 'ghana', 'morocco',
    'argentina', 'chile', 'colombia', 'peru', 'venezuela'
]


# ==========================================
# LOAD CHATBOT RESOURCES
# ==========================================
def load_chatbot_resources():
    global chat_model, tokenizer, classes, knowledge_base, city_data, lemmatizer, max_len

    if chat_model is not None and tokenizer is not None and classes and knowledge_base:
        print("Resources already loaded")
        return

    print("="*60)
    print("LOADING CHATBOT RESOURCES")
    print("="*60)

    try:
        nltk.download('punkt', quiet=True)
        nltk.download('wordnet', quiet=True)
        nltk.download('omw-1.4', quiet=True)
    except:
        print("NLTK download failed")

    lemmatizer = WordNetLemmatizer()

    # Load Model
    if os.path.exists('chat_model.keras'):
        try:
            chat_model = keras.models.load_model('chat_model.keras')
            print("Loaded model: chat_model.keras")
            model_loaded = True
        except Exception as e:
            print(f"Failed to load chat_model.keras: {e}")
            model_loaded = False
    else:
        print("chat_model.keras not found!")
        raise FileNotFoundError("No trained model found. Please run train.py")

    # Get max sequence length from model
    try:
        max_len = chat_model.input_shape[1]
        print(f"Max sequence length: {max_len}")
    except:
        max_len = 10
        print(f"Using default max_len: {max_len}")

    # Load Tokenizer
    try:
        with open('tokenizer.pickle', 'rb') as f:
            tokenizer = pickle.load(f)
        print("Loaded tokenizer")
    except FileNotFoundError:
        print("tokenizer.pickle not found!")
        raise

    # Load Classes
    try:
        with open('classes.pickle', 'rb') as f:
            classes = pickle.load(f)
        print(f"Loaded classes: {len(classes)} intents")
    except FileNotFoundError:
        print("classes.pickle not found!")
        raise

    # Load Intents from intent.json
    knowledge_base = []
    if os.path.exists('intent.json'):
        try:
            with open('intent.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, dict) and 'intents' in data:
                    knowledge_base = data['intents']
                elif isinstance(data, list):
                    knowledge_base = data
            print(f"Loaded {len(knowledge_base)} intents from intent.json")
        except Exception as e:
            print(f"Failed to load intent.json: {e}")
    
    if not knowledge_base:
        print("No intents file found!")
        raise FileNotFoundError("No intents file found")

    # Load City Data
    city_data = {}
    if os.path.exists('chatbot_data.json'):
        try:
            with open('chatbot_data.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, dict) and 'cities' in data:
                    city_data = data
                elif isinstance(data, list):
                    city_data = {'cities': data}
                else:
                    city_data = data
            print(f"Loaded {len(city_data.get('cities', []))} cities from chatbot_data.json")
        except Exception as e:
            print(f"Failed to load chatbot_data.json: {e}")
    else:
        print("No city data file found")

    print("="*60)
    print("ALL RESOURCES LOADED SUCCESSFULLY!")
    print(f"   Model: {'Loaded' if chat_model else 'Failed'}")
    print(f"   Tokenizer: {'Loaded' if tokenizer else 'Failed'}")
    print(f"   Classes: {len(classes)}")
    print(f"   Intents: {len(knowledge_base)}")
    print(f"   Cities: {len(city_data.get('cities', [])) if city_data else 0}")
    print("="*60)


# ==========================================
# FUZZY CITY MATCH
# ==========================================

def fuzzy_city_match(user_message):
    """Find city even with typos using advanced fuzzy matching"""
    cities = ["kathmandu", "pokhara", "lumbini", "chitwan", "bhaktapur", "lalitpur", "everest", "annapurna", "mustang", "manang", "janakpur", "gorkha", "syangja"]
    
    user_lower = user_message.lower().strip()
    
    # 1. Direct match
    for city in cities:
        if city in user_lower:
            return city.title()
    
    # 2. Common typos mapping
    typo_map = {
        "kathmandi": "kathmandu",
        "katmandu": "kathmandu",
        "katmandhu": "kathmandu",
        "pokra": "pokhara",
        "pokhar": "pokhara",
        "pokahra": "pokhara",
        "lumbinii": "lumbini",
        "chitwan": "chitwan",
        "bhaktapur": "bhaktapur",
        "lalitpur": "lalitpur",
        "mustang": "mustang",
        "manang": "manang",
        "janakpur": "janakpur",
        "gorkha": "gorkha",
        "syangja": "syangja",
        "everst": "everest",
        "annapurna": "annapurna"
    }
    
    for typo, correct in typo_map.items():
        if typo in user_lower:
            return correct.title()
    
    # 3. Prefix matching (first 4-5 characters match)
    for city in cities:
        if len(user_lower) >= 4 and len(city) >= 4:
            if user_lower[:4] == city[:4]:
                return city.title()
            if user_lower[:3] == city[:3] and len(user_lower) <= len(city) + 3:
                return city.title()
    
    # 4. Check if city appears as substring
    for city in cities:
        if city in user_lower.replace(' ', ''):
            return city.title()
    
    return None


# ==========================================
# CHECK IF QUERY IS ABOUT NEPAL
# ==========================================

def is_about_nepal(user_message):
    """Check if the query is about Nepal or a Nepali city"""
    user_lower = user_message.lower()
    
    # Check for non-Nepal countries
    for country in NON_NEPAL_COUNTRIES:
        if country in user_lower:
            return False
    
    # Check for Nepal cities
    nepal_terms = ['nepal', 'kathmandu', 'pokhara', 'lumbini', 'chitwan', 'bhaktapur', 'lalitpur', 'everest', 'annapurna', 'mustang', 'manang', 'janakpur', 'gorkha', 'syangja','himalaya', 'himalayas', 'sagarmatha']
    
    for term in nepal_terms:
        if term in user_lower:
            return True
    
    # If no Nepal terms and no other country, default to True
    # (it might be a general question about Nepal)
    return True


# ==========================================
# EXTRACT CITY FROM ANY QUERY
# ==========================================

def extract_city_from_query(user_message):
    """Extract city name from any query - handles various patterns"""
    user_lower = user_message.lower()
    
    # ==========================================
    # FIRST: Check for non-Nepal countries
    # ==========================================
    for country in NON_NEPAL_COUNTRIES:
        if country in user_lower:
            return None  # Not a Nepal city
    
    # ==========================================
    # THEN: Check for Nepal cities
    # ==========================================
    cities = ["kathmandu", "pokhara", "lumbini", "chitwan", "bhaktapur", "lalitpur", "everest", "annapurna", "mustang", "manang", "janakpur", "gorkha", "syangja"]
    
    # 1. Direct mention
    for city in cities:
        if city in user_lower:
            return city.title()
    
    # 2. Pattern: "in [city]"
    match = re.search(r'in\s+([a-zA-Z]+)', user_lower)
    if match:
        city = match.group(1).lower()
        for c in cities:
            if c in city or city in c:
                return c.title()
    
    # 3. Pattern: "of [city]" or "for [city]"
    match = re.search(r'(?:of|for)\s+([a-zA-Z]+)', user_lower)
    if match:
        city = match.group(1).lower()
        for c in cities:
            if c in city or city in c:
                return c.title()
    
    # 4. Try fuzzy match
    return fuzzy_city_match(user_message)


# ==========================================
# DETECT QUERY TYPE - COMPLETELY UPDATED
# ==========================================

def detect_query_type(user_message):
    """Detect what type of information the user is asking for"""
    user_lower = user_message.lower()
    
    # ==========================================
    # STEP 0: FIX COMMON TYPOS FIRST
    # ==========================================
    typo_fixes = {
        'shooping': 'shopping',
        'shoping': 'shopping', 
        'shopng': 'shopping',
        'soping': 'shopping',
        'restraunt': 'restaurant',
        'resturent': 'restaurant',
        'resturant': 'restaurant',
        'attration': 'attraction',
        'attractions': 'attractions',
        'accomodation': 'accommodation',
        'accomidation': 'accommodation',
        'monestry': 'monastery',
        'monastry': 'monastery',
        'whis': 'what',
        'whic': 'which',
        'wats': 'whats',
        'wut': 'what',
        'teh': 'the'
    }
    
    for typo, correct in typo_fixes.items():
        user_lower = user_lower.replace(typo, correct)
    
    # ==========================================
    # STEP 1: Check for HOTEL related keywords
    # ==========================================
    hotel_keywords = ['hotel', 'stay', 'accommodation', 'lodge', 'resort', 'guest house', 'recommend hotel', 'recommend hotels', 'best hotel', 'where to stay', 'stay in', 'book a hotel', 'hotel recommendation', 'hotel options', 'room', 'rooms']
    if any(word in user_lower for word in hotel_keywords):
        return 'hotels'
    
    # ==========================================
    # STEP 2: Check for WEATHER
    # ==========================================
    weather_keywords = ['weather', 'temperature', 'rain', 'rainy', 'forecast', 'humidity', 'climate']
    if any(word in user_lower for word in weather_keywords):
        return 'weather'
    
    # ==========================================
    # STEP 3: Check for ATTRACTIONS
    # ==========================================
    attraction_keywords = [
        'attraction', 'attractions', 'sight', 'sights', 'tourist', 
        'monument', 'temple', 'temples', 'stupas', 'stupa', 'palace',
        'durbar square', 'things to do', 'what to see', 
        'top places', 'must see', 'famous place', 'best place', 'best places',
        'must visit place', 'must visit', 'popular place', 'place to visit',
        'where should i go', 'recommend place', 'recommend best place',
        'best tourist spot', 'best spots', 'best attraction'
    ]
    if any(keyword in user_lower for keyword in attraction_keywords):
        return 'attractions'
    
    # ==========================================
    # STEP 4: Check for BEST TIME
    # ==========================================
    time_keywords = ['best time', 'when to visit', 'season', 'month to visit']
    if any(keyword in user_lower for keyword in time_keywords):
        return 'best_time'
    
    # ==========================================
    # STEP 5: Check for FOOD
    # ==========================================
    food_keywords = [
        'food', 'eat', 'restaurant', 'cuisine', 'dish', 'meal',
        'dinner', 'lunch', 'momo', 'dal bhat', 'what to eat',
        'where to eat', 'local food', 'best food'
    ]
    if any(keyword in user_lower for keyword in food_keywords):
        return 'food'
    
    # ==========================================
    # STEP 6: Check for TRANSPORT
    # ==========================================
    transport_keywords = [
        'transport', 'reach', 'go', 'bus', 'flight', 'travel', 
        'road', 'way', 'how to get', 'how to reach', 'transportation'
    ]
    if any(keyword in user_lower for keyword in transport_keywords):
        return 'transport'
    
    # ==========================================
    # STEP 7: Check for SHOPPING (UPDATED)
    # ==========================================
    shopping_keywords = [
        'shop', 'shopping', 'buy', 'bargain', 'bazaar',
        'market', 'souvenir', 'purchase', 'gift', 
        'what to buy', 'where to shop', 'shop for',
        'shopping place', 'shop in', 'buy in',
        'souvenir shop', 'gift shop', 'local market',
        'handicraft', 'handicrafts', 'craft', 'crafts',
        'pashmina', 'singing bowl', 'thangka', 'wood carving',
        'metal craft', 'pottery'
    ]
    if any(keyword in user_lower for keyword in shopping_keywords):
        return 'shopping'
    
    # ==========================================
    # STEP 8: Check for CAPITAL
    # ==========================================
    if 'capital' in user_lower:
        return 'capital'
    
    # ==========================================
    # STEP 9: Check for ALTITUDE
    # ==========================================
    altitude_keywords = ['altitude', 'height', 'elevation']
    if any(keyword in user_lower for keyword in altitude_keywords):
        return 'altitude'
    
    # ==========================================
    # STEP 10: Check for POPULATION
    # ==========================================
    population_keywords = ['population', 'people', 'live']
    if any(keyword in user_lower for keyword in population_keywords):
        return 'population'
    
    # ==========================================
    # STEP 11: Check for HISTORY
    # ==========================================
    history_keywords = ['history', 'historical', 'past', 'origin']
    if any(keyword in user_lower for keyword in history_keywords):
        return 'history'
    
    # ==========================================
    # STEP 12: Check for CULTURE
    # ==========================================
    culture_keywords = ['culture', 'tradition', 'festival', 'custom', 'ethnic']
    if any(keyword in user_lower for keyword in culture_keywords):
        return 'culture'
    
    # ==========================================
    # STEP 13: Default
    # ==========================================
    return 'general'


# ==========================================
# TEXT PROCESSING FUNCTIONS
# ==========================================

def clean_up_sentence(sentence):
    if lemmatizer is None:
        load_chatbot_resources()
    sentence_words = nltk.word_tokenize(sentence)
    return [lemmatizer.lemmatize(word.lower()) for word in sentence_words]


def text_to_sequence(text):
    """Convert text to sequence for LSTM prediction"""
    if tokenizer is None:
        load_chatbot_resources()
    
    text = text.lower().strip()
    seq = tokenizer.texts_to_sequences([text])
    padded = pad_sequences(seq, maxlen=max_len, padding='post', truncating='post')
    return padded


# ==========================================
# PREDICTION FUNCTION
# ==========================================

def predict_intent(user_message):
    """Predict intent using LSTM model"""
    if chat_model is None:
        load_chatbot_resources()
    
    padded_seq = text_to_sequence(user_message)
    res = chat_model.predict(padded_seq, verbose=0)[0]
    predicted_index = np.argmax(res)
    confidence = float(res[predicted_index])
    predicted_tag = classes[predicted_index]
    
    return predicted_tag, confidence


# ==========================================
# VALIDATE INTENT
# ==========================================

def is_valid_intent(predicted_tag, user_message):
    if predicted_tag in ['get_weather', 'get_travel_recommendations']:
        return True
    
    cities = ["kathmandu", "pokhara", "lumbini", "chitwan", "bhaktapur", "lalitpur", "everest", "annapurna", "mustang", "manang", "janakpur", "gorkha", "syangja"]
    
    user_lower = user_message.lower()
    
    for city in cities:
        if city in user_lower:
            city_keywords = ['attraction', 'hotel', 'food', 'transport', 'shopping', 'info']
            if any(keyword in predicted_tag for keyword in city_keywords):
                city_info = get_city_info(city)
                if city_info:
                    return True
                else:
                    return False
    
    match = re.search(r'to\s+([a-zA-Z]+)', user_lower)
    if match:
        dest = match.group(1).lower()
        if dest in cities:
            city_info = get_city_info(dest)
            if city_info:
                return True
    
    for intent in knowledge_base:
        if intent.get('tag') == predicted_tag:
            return True
    
    return False


# ==========================================
# UNKNOWN RESPONSE - NO EMOJIS
# ==========================================

def get_unknown_response(user_message):
    cities = ["kathmandu", "pokhara", "lumbini", "chitwan", "bhaktapur", "lalitpur", "everest", "annapurna", "mustang", "manang", "janakpur", "gorkha", "syangja"]
    
    city_mentioned = None
    for city in cities:
        if city in user_message.lower():
            city_mentioned = city.title()
            break
    
    response = "I do not have answer in dataset.\n\n"
    
    if city_mentioned:
        response += f"I can help you with {city_mentioned}:\n"
        response += "- Attractions\n"
        response += "- Hotels\n"
        response += "- Food\n"
        response += "- Transport\n"
        response += "- Shopping\n\n"
        response += f"Try asking:\n"
        response += f"- 'top attractions in {city_mentioned}'\n"
        response += f"- 'best hotels in {city_mentioned}'\n"
        response += f"- 'food in {city_mentioned}'\n"
        response += f"- 'how to reach {city_mentioned}'"
    else:
        response += "I can help you with Nepal travel information:\n"
        response += "- Attractions (e.g., 'top attractions in Kathmandu')\n"
        response += "- Hotels (e.g., 'best hotels in Pokhara')\n"
        response += "- Food (e.g., 'food in Lumbini')\n"
        response += "- Transport (e.g., 'how to reach Chitwan')\n"
        response += "- Shopping (e.g., 'shopping in Bhaktapur')\n\n"
        response += "Try asking about a specific city or topic!"
    
    return response


# ==========================================
# CITY DATA HELPER FUNCTIONS
# ==========================================

def get_city_info(city_name):
    if not city_data or 'cities' not in city_data:
        load_chatbot_resources()
    
    for city in city_data.get('cities', []):
        if city.get('city', '').lower() == city_name.lower():
            return city
    return None


def extract_city_from_intent(intent_tag):
    cities = ["kathmandu", "pokhara", "lumbini", "chitwan", "bhaktapur", "lalitpur", "everest", "annapurna", "mustang", "manang", "janakpur", "gorkha", "syangja"]
    
    for city in cities:
        if city in intent_tag.lower():
            return city.title()
    return None


# ==========================================
# FORMAT CITY RESPONSE - NO EMOJIS
# ==========================================

def get_city_response_by_type(city_info, query_type, user_message=None):
    """Get city response based on detected query type - No emojis"""
    city_name = city_info.get('city', 'Unknown')
    info = city_info.get('info', {})
    
    if query_type == 'weather':
        return None
    
    elif query_type == 'best_time':
        best_time = info.get('best_time', 'Not specified')
        return f"""Best Time to Visit {city_name}
{'-' * 40}
Best Time: {best_time}

Why visit during this time:
- Pleasant weather with clear skies
- Comfortable temperatures for sightseeing
"""
    
    elif query_type == 'capital':
        return f"{city_name} is a city in Nepal. It is not a country, so it doesn't have a capital.\n\nDid you mean: 'What is the capital of Nepal?' (Answer: Kathmandu)"
    
    elif query_type == 'attractions':
        return format_attractions(city_info, user_message)
    
    elif query_type == 'hotels':
        return format_hotels(city_info, user_message)
    
    elif query_type == 'food':
        return format_food(city_info, user_message)
    
    elif query_type == 'transport':
        return format_transport(city_info, user_message)
    
    elif query_type == 'shopping':
        return format_shopping(city_info, user_message)
    
    elif query_type == 'altitude':
        return f"Altitude of {city_name}\n{'-' * 40}\n{info.get('altitude', 'Not specified')}"
    
    elif query_type == 'population':
        return f"Population of {city_name}\n{'-' * 40}\n{info.get('population', 'Not specified')}"
    
    elif query_type == 'history':
        history = info.get('history', 'History information not available')
        return f"History of {city_name}\n{'-' * 40}\n{history}"
    
    elif query_type == 'culture':
        culture = info.get('culture', 'Culture information not available')
        return f"Culture of {city_name}\n{'-' * 40}\n{culture}"
    
    else:
        return format_city_info(city_info, user_message)


# ==========================================
# MAIN GET CITY RESPONSE
# ==========================================

def get_city_response(city_name, intent_tag, user_message=None):
    if not city_name:
        return None
    
    city_info = get_city_info(city_name)
    if not city_info:
        return None
    
    query_type = detect_query_type(user_message) if user_message else 'general'
    return get_city_response_by_type(city_info, query_type, user_message)


# ==========================================
# FORMAT CITY INFO - NO EMOJIS
# ==========================================

def format_city_info(city, user_message=None):
    info = city.get('info', {})
    city_name = city.get('city', 'Unknown')
    
    return f"""
{city_name}
{'-' * 40}
{info.get('description', 'Information not available')}

Best Time: {info.get('best_time', 'Not specified')}
Altitude: {info.get('altitude', 'Not specified')}
Population: {info.get('population', 'Not specified')}
Popularity: {info.get('popularity', 'N/A')}/100
"""


def format_attractions(city, user_message=None):
    attractions = city.get('attractions', [])
    if not attractions:
        return f"No attractions found for {city['city']}"
    
    city_name = city.get('city', 'Unknown')
    sorted_attractions = sorted(attractions, key=lambda x: x.get('rating', 0), reverse=True)
    
    count = 5
    if user_message:
        query_lower = user_message.lower()
        match = re.search(r'top\s+(\d+)', query_lower)
        if match:
            count = int(match.group(1))
            count = min(count, 10)
            count = max(count, 1)
        elif 'best' in query_lower or 'recommend' in query_lower or 'suggest' in query_lower:
            count = 3
    
    top_attractions = sorted_attractions[:count]
    
    result = f"Top Attractions in {city_name}\n"
    result += "-" * 40 + "\n\n"
    
    for i, attr in enumerate(top_attractions, 1):
        name = attr.get('name', 'Unknown')
        description = attr.get('description', '')
        entry_fee = attr.get('entry_fee', 'Free')
        rating = attr.get('rating', 'N/A')
        best_time = attr.get('best_time', 'N/A')
        
        result += f"{i}. {name}\n"
        if description:
            result += f"   Description: {description[:100]}...\n"
        result += f"   Entry Fee: {entry_fee}\n"
        result += f"   Rating: {rating}/5.0\n"
        result += f"   Best Time: {best_time}\n\n"
    
    return result


def format_hotels(city, user_message=None):
    hotels = city.get('hotels', [])
    if not hotels:
        return f"No hotels found for {city['city']}"
    
    city_name = city.get('city', 'Unknown')
    sorted_hotels = sorted(hotels, key=lambda x: x.get('rating', 0), reverse=True)
    
    luxury = [h for h in sorted_hotels if h.get('type') == 'luxury']
    mid = [h for h in sorted_hotels if h.get('type') == 'mid']
    budget = [h for h in sorted_hotels if h.get('type') == 'budget']
    
    result = f"Hotels in {city_name}\n"
    result += "-" * 40 + "\n\n"
    
    result += "TOP RECOMMENDATIONS:\n"
    
    if luxury:
        best = max(luxury, key=lambda x: x.get('rating', 0))
        result += f"\nBest Luxury: {best.get('name')}\n"
        result += f"   Price: {best.get('price')}\n"
        result += f"   Location: {best.get('location', 'N/A')}\n"
        result += f"   Rating: {best.get('rating', 'N/A')}/5.0\n"
    
    if mid:
        best = max(mid, key=lambda x: x.get('rating', 0))
        result += f"\nBest Mid-Range: {best.get('name')}\n"
        result += f"   Price: {best.get('price')}\n"
        result += f"   Location: {best.get('location', 'N/A')}\n"
        result += f"   Rating: {best.get('rating', 'N/A')}/5.0\n"
    
    if budget:
        best = max(budget, key=lambda x: x.get('rating', 0))
        result += f"\nBest Budget: {best.get('name')}\n"
        result += f"   Price: {best.get('price')}\n"
        result += f"   Location: {best.get('location', 'N/A')}\n"
        result += f"   Rating: {best.get('rating', 'N/A')}/5.0\n"
    
    result += "\nAll Hotels (sorted by rating):\n"
    result += "-" * 40 + "\n"
    
    for hotel in sorted_hotels[:8]:
        name = hotel.get('name', 'Unknown')
        hotel_type = hotel.get('type', 'N/A')
        price = hotel.get('price', 'Contact for pricing')
        rating = hotel.get('rating', 'N/A')
        location = hotel.get('location', 'N/A')
        
        result += f"\n- {name}\n"
        result += f"  Type: {hotel_type}\n"
        result += f"  Price: {price}\n"
        result += f"  Location: {location}\n"
        result += f"  Rating: {rating}/5.0\n"
    
    return result


def format_food(city, user_message=None):
    food = city.get('food', {})
    if not food:
        return f"No food information found for {city['city']}"
    
    city_name = city.get('city', 'Unknown')
    
    result = f"Food in {city_name}\n"
    result += "-" * 40 + "\n\n"
    
    must_try = food.get('must_try', [])
    if must_try:
        result += "Must Try Dishes:\n"
        for item in must_try[:6]:
            result += f"  - {item}\n"
        result += "\n"
    
    restaurants = food.get('popular_restaurants', [])
    if restaurants:
        result += "Popular Restaurants:\n"
        for rest in restaurants[:5]:
            result += f"\n  - {rest.get('name', 'Unknown')}\n"
            result += f"    Cuisine: {rest.get('cuisine', 'N/A')}\n"
            result += f"    Price: {rest.get('price_range', 'N/A')}\n"
            result += f"    Location: {rest.get('location', 'N/A')}\n"
    
    return result


def format_transport(city, user_message=None):
    transport = city.get('transport', {})
    if not transport:
        return f"No transport information found for {city['city']}"
    
    city_name = city.get('city', 'Unknown')
    
    origin = None
    if user_message:
        user_lower = user_message.lower()
        match = re.search(r'from\s+([a-zA-Z]+)', user_lower)
        if match:
            origin = match.group(1).title()
    
    if origin and origin.lower() != 'kathmandu':
        return f"""Transport from {origin} to {city_name}
{'-' * 40}

I only have transport information from Kathmandu to {city_name}.

Please ask: 'transport to {city_name} from Kathmandu'
"""
    
    result = f"Transport to {city_name}\n"
    result += "-" * 40 + "\n\n"
    
    for key, value in transport.items():
        if key != 'to_attractions':
            display_key = key.replace('_', ' ').title()
            result += f"- {display_key}: {value}\n"
    
    return result


def format_shopping(city, user_message=None):
    shopping = city.get('shopping', [])
    if not shopping:
        return f"No shopping information found for {city['city']}"
    
    city_name = city.get('city', 'Unknown')
    
    result = f"Shopping in {city_name}\n"
    result += "-" * 40 + "\n\n"
    
    for item in shopping[:10]:
        result += f"- {item.get('item', 'Unknown')}\n"
        result += f"  Available at: {item.get('place', 'local markets')}\n\n"
    
    return result


# ==========================================
# FALLBACK RESPONSE
# ==========================================

def get_static_response(intent_tag):
    for intent in knowledge_base:
        if intent.get('tag') == intent_tag:
            responses = intent.get('responses', [])
            if responses:
                return random.choice(responses)
    return None


# ==========================================
# VALIDATE CAPITAL QUERY
# ==========================================

def validate_capital_query(user_message, predicted_tag):
    """Validate that capital query is about Nepal, not another country"""
    user_lower = user_message.lower()
    
    if predicted_tag == "nepal_capital":
        # Check if user mentioned a non-Nepal country
        for country in NON_NEPAL_COUNTRIES:
            if country in user_lower:
                return False  # Not about Nepal
        return True
    
    return True


# ==========================================
# MAIN RESPONSE FUNCTION
# ==========================================

def get_response(user_message):
    """
    MAIN FUNCTION: Get response for user message
    """
    if chat_model is None or tokenizer is None or not classes:
        load_chatbot_resources()
    
    # Fix common typos
    fixed_message = user_message.lower()
    typo_fixes = {
        'whis': 'what',
        'whic': 'which',
        'whichh': 'which',
        'wats': 'whats',
        'wut': 'what',
        'teh': 'the',
        'time is good': 'best time',
        'good time': 'best time',
        'which time': 'what time'
    }
    
    for typo, correct in typo_fixes.items():
        fixed_message = fixed_message.replace(typo, correct)
    
    print(f"Fixed message: {fixed_message}")
    
    # ==========================================
    # STEP 1: Check if it's about a non-Nepal country
    # ==========================================
    for country in NON_NEPAL_COUNTRIES:
        if country in fixed_message:
            print(f"Query about non-Nepal country: {country}")
            return get_unknown_response(user_message), "unknown", 0.5
    
    # ==========================================
    # STEP 2: Check if it's a WEATHER query
    # ==========================================
    weather_keywords = ['weather', 'temperature', 'rain', 'rainy', 'forecast', 'humidity', 'climate']
    hotel_keywords = ['hotel', 'stay', 'accommodation', 'lodge', 'resort', 'guest house', 'recommend hotel', 'recommend hotels', 'best hotel', 'where to stay', 'stay in', 'book a hotel', 'hotel recommendation', 'hotel options']
    attraction_keywords = ['attraction', 'sight', 'tourist', 'monument', 'temple', 'stupas', 'palace']
    food_keywords = ['food', 'eat', 'restaurant', 'cuisine', 'dish', 'meal']
    
    is_weather = any(keyword in fixed_message for keyword in weather_keywords)
    is_hotel = any(keyword in fixed_message for keyword in hotel_keywords)
    is_attraction = any(keyword in fixed_message for keyword in attraction_keywords)
    is_food = any(keyword in fixed_message for keyword in food_keywords)
    
    if is_weather and not is_hotel and not is_attraction and not is_food:
        city_name = extract_city_from_query(user_message)
        if not city_name:
            city_name = fuzzy_city_match(user_message)
        if city_name:
            print(f"Weather request for: {city_name}")
            return None, "get_weather", 0.95
        else:
            return get_unknown_response(user_message), "unknown", 0.5

    if is_hotel and not is_weather and not is_attraction and not is_food:
        city_name = extract_city_from_query(user_message)
        if not city_name:
            city_name = fuzzy_city_match(user_message)
        if city_name:
            print(f"Hotel recommendation request for: {city_name}")
            return None, "get_hotel_recommendations", 0.95
        else:
            return get_unknown_response(user_message), "unknown", 0.5
    
    # ==========================================
    # STEP 3: Check for city using FUZZY LOGIC
    # ==========================================
    city_name = extract_city_from_query(user_message)
    if not city_name:
        city_name = fuzzy_city_match(user_message)
    
    if city_name:
        city_info = get_city_info(city_name)
        if city_info:
            print(f"City found: {city_name}")
            query_type = detect_query_type(fixed_message)
            print(f"Query type: {query_type}")
            
            if query_type == 'weather':
                return None, "get_weather", 0.95
            
            response = get_city_response_by_type(city_info, query_type, user_message)
            if response:
                if query_type == 'hotels':
                    return None, "get_hotel_recommendations", 0.95
                return response, f"{city_name}_{query_type}", 0.95
            else:
                return get_unknown_response(user_message), "unknown", 0.5
        else:
            # City found but no data - return unknown
            return get_unknown_response(user_message), "unknown", 0.5
    
    # ==========================================
    # STEP 4: Use LSTM
    # ==========================================
    predicted_tag, confidence = predict_intent(user_message)
    print(f"LSTM Prediction: {predicted_tag} (Confidence: {confidence:.2f})")
    
    if confidence < 0.50:
        predicted_tag, confidence = predict_intent(fixed_message)
        print(f"LSTM Prediction (fixed): {predicted_tag} (Confidence: {confidence:.2f})")
    
    if confidence < 0.50:
        return get_unknown_response(user_message), "unknown", confidence
    
    # ==========================================
    # STEP 5: Validate the intent is for NEPAL
    # ==========================================
    # Check if it's a capital query about a non-Nepal country
    if predicted_tag == "nepal_capital":
        if not validate_capital_query(user_message, predicted_tag):
            return get_unknown_response(user_message), "unknown", 0.5
    
    if not is_valid_intent(predicted_tag, user_message):
        return get_unknown_response(user_message), "unknown", confidence
    
    # Handle special intents
    if predicted_tag in ["get_weather", "get_travel_recommendations", "get_hotel_recommendations"]:
        return None, predicted_tag, confidence
    
    # Try to extract city from intent
    city_name = extract_city_from_intent(predicted_tag)
    if city_name:
        city_info = get_city_info(city_name)
        if city_info:
            query_type = detect_query_type(fixed_message)
            
            if query_type == 'weather':
                return None, "get_weather", confidence
            
            response = get_city_response_by_type(city_info, query_type, user_message)
            if response:
                return response, predicted_tag, confidence
    
    # Get static response
    static_response = get_static_response(predicted_tag)
    if static_response:
        return static_response, predicted_tag, confidence
    
    return get_unknown_response(user_message), "unknown", confidence


# ==========================================
# TEST FUNCTION
# ==========================================

def test_chatbot():
    """Test the chatbot with sample queries"""
    print("\n" + "="*60)
    print("TESTING CHATBOT")
    print("="*60)
    
    test_queries = [
        # Working queries
        "weather of pokhara",
        "best hotel in kathmandu",
        "top attractions in lumbini",
        "what is the capital of nepal",
        
        # Non-Nepal queries (should return "I don't have information")
        "what is the capital of france",
        "what is the capital of india",
        "population of china",
        "who is the president of usa",
        
        # Shopping queries with typos
        "shooping i should do in pokhara",
        "shoping in kathmandu",
        "what to buy in bhaktapur",
        "shopping places in lalitpur",
        
        # Confusing queries
        "tell me about kathmandu and pokhara",
        "hotel and food in chitwan",
        "Kathmandu or Pokhara",
        "wethr in kthmandu",
        "bst hotel in phkara",
    ]
    
    for query in test_queries:
        print(f"\nYou: {query}")
        response, intent, confidence = get_response(query)
        if response:
            print(f"Bot: {response[:200]}...")
        else:
            print(f"Bot: (Special intent - {intent})")
        print(f"Intent: {intent}, Confidence: {confidence:.2f}")
        print("-"*40)


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    load_chatbot_resources()
    test_chatbot()
    
    print("\n" + "="*60)
    print("INTERACTIVE CHAT MODE")
    print("="*60)
    print("Type 'quit' to exit")
    print("="*60)
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Bot: Goodbye!")
            break
        
        if user_input.strip() == '':
            print("Bot: Please say something!")
            continue
        
        response, intent, confidence = get_response(user_input)
        if response:
            print(f"Bot: {response}")
        else:
            print(f"Bot: (Special intent detected - {intent})")
        print(f"Intent: {intent}, Confidence: {confidence:.2f}")