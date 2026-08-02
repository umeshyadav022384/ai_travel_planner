# Python_server/algorithm.py

import json
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from math import radians, sin, cos, sqrt, atan2
import os
import random
import re
import time

# ✅ Import shared Gemini instance
from gemini_integration import gemini

# ==========================================
# DESCRIPTION CACHE
# ==========================================

_description_cache = {}

# ==========================================
# HELPER: Format cuisine list nicely
# ==========================================

def format_cuisine(cuisine_data):
    """Convert cuisine list to a readable string"""
    if not cuisine_data:
        return ""
    if isinstance(cuisine_data, list):
        names = []
        for c in cuisine_data:
            if isinstance(c, dict):
                names.append(c.get('name', ''))
            elif isinstance(c, str):
                names.append(c)
        filtered = [n for n in names if n]
        if filtered:
            return ", ".join(filtered)
    elif isinstance(cuisine_data, str):
        return cuisine_data
    return ""


# ==========================================
# HELPER: Get attraction description from dataset
# ==========================================

def get_attraction_description(activity):
    """Get description from dataset, with fallback"""
    description = activity.get('description', '')
    if description and len(description) > 10:
        return description
    
    name = activity.get('name', '')
    destination = activity.get('city', '')
    
    fallbacks = [
        f"✨ Discover the enchanting {name} in {destination}, a place where ancient history and natural beauty come together.",
        f"🏛️ Step into the rich cultural heritage of {destination} at {name}, a landmark that has stood the test of time.",
        f"🌿 Experience the serene beauty of {name}, a hidden gem in {destination} that offers a perfect escape.",
        f"🕉️ Immerse yourself in the spiritual atmosphere of {name}, a sacred site in {destination} for centuries.",
        f"🏔️ Marvel at the breathtaking views and rich history of {name}, one of {destination}'s treasured attractions."
    ]
    return random.choice(fallbacks)


# ==========================================
# HELPER: Calculate centroid of places
# ==========================================

def calculate_centroid(places):
    """Calculate average lat/lng from a list of places"""
    lats = []
    lngs = []
    for p in places:
        lat = p.get('lat', 0)
        lng = p.get('lng', 0)
        if lat and lng:
            try:
                lats.append(float(lat))
                lngs.append(float(lng))
            except (ValueError, TypeError):
                continue
    if lats:
        return sum(lats) / len(lats), sum(lngs) / len(lngs)
    return 0, 0


# ==========================================
# HELPER: Find nearest restaurant to a location
# ==========================================

def find_nearest_restaurants(restaurants, target_lat, target_lng, count=1):
    """Find the nearest restaurants to a target location"""
    if not restaurants or target_lat == 0:
        return []
    
    with_distance = []
    for r in restaurants:
        r_lat = r.get('latitude', 0) or r.get('lat', 0)
        r_lng = r.get('longitude', 0) or r.get('lng', 0)
        if r_lat and r_lng:
            try:
                r_lat = float(r_lat)
                r_lng = float(r_lng)
                dist = haversine(target_lat, target_lng, r_lat, r_lng)
                with_distance.append((dist, r))
            except (ValueError, TypeError):
                continue
    
    if with_distance:
        with_distance.sort(key=lambda x: x[0])
        return [r for _, r in with_distance[:count]]
    return []


# ==========================================
# HELPER: Safely extract price (with cap)
# ==========================================

def safe_extract_price(price_value, max_price=500):
    """Safely extract price with a maximum cap"""
    if price_value is None:
        return 0
    
    # If it's already a number
    if isinstance(price_value, (int, float)):
        if price_value > max_price:
            return 0  # Treat as free if price is unreasonably high
        return int(price_value)
    
    # If it's a string, try to extract
    if isinstance(price_value, str):
        # Try to extract numbers
        numbers = re.findall(r'\d+', price_value)
        if numbers:
            price = int(numbers[0])
            if price > max_price:
                return 0
            return price
    
    return 0


# ==========================================
# LOAD ATTRACTIONS
# ==========================================

def load_attractions():
    """Load attractions from JSON file"""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'datasets', 'nepal_attractions.json'),
        os.path.join(os.path.dirname(__file__), 'nepal_attractions.json'),
        'datasets/nepal_attractions.json'
    ]
    
    for file_path in possible_paths:
        if os.path.exists(file_path):
            print(f"✅ Found dataset at: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_attractions = []
            for city_data in data['cities']:
                for attraction in city_data['attractions']:
                    attraction['city'] = city_data['city']
                    # ✅ Fix: Safely parse price_foreigners
                    price = attraction.get('price_foreigners', 0)
                    attraction['price_foreigners'] = safe_extract_price(price)
                    all_attractions.append(attraction)
            
            print(f"✅ Loaded {len(all_attractions)} total attractions")
            return all_attractions
    
    print("❌ No dataset file found!")
    return []


# ==========================================
# KNN RECOMMEND
# ==========================================

def knn_recommend(destination, preferences, n_recommendations=15):
    """Find attractions similar to user preferences using KNN"""
    all_attractions = load_attractions()
    
    if len(all_attractions) == 0:
        print("❌ No attractions loaded!")
        return []
    
    filtered = [a for a in all_attractions if a['city'].lower() == destination.lower()]
    
    print(f"📊 Found {len(filtered)} attractions for {destination}")
    
    if len(filtered) == 0:
        print(f"⚠️ No attractions found for {destination}")
        return []
    
    feature_cols = ['art', 'history', 'nature', 'food', 'adventure']
    user_vector = [[
        preferences.get('art', 5),
        preferences.get('history', 5),
        preferences.get('nature', 5),
        preferences.get('food', 5),
        preferences.get('adventure', 5)
    ]]
    
    attraction_vectors = [[
        a.get('art', 5), a.get('history', 5), a.get('nature', 5), 
        a.get('food', 5), a.get('adventure', 5)
    ] for a in filtered]
    
    n_neighbors = min(n_recommendations, len(filtered))
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
    knn.fit(attraction_vectors)
    distances, indices = knn.kneighbors(user_vector)
    
    recommendations = []
    for idx in indices[0]:
        recommendations.append(filtered[idx])
    
    return recommendations


# ==========================================
# K-MEANS CLUSTER
# ==========================================

def kmeans_cluster(attractions, n_clusters=3):
    """Group attractions into clusters with balanced size"""
    if len(attractions) == 0:
        return {}
    
    if len(attractions) <= n_clusters:
        clusters = {}
        for i, attr in enumerate(attractions):
            cluster_idx = i % n_clusters
            if cluster_idx not in clusters:
                clusters[cluster_idx] = []
            clusters[cluster_idx].append(attr)
        return clusters
    
    if len(attractions) < n_clusters * 2:
        clusters = {}
        sorted_attractions = sorted(attractions, key=lambda x: x.get('rating', 0), reverse=True)
        for i, attr in enumerate(sorted_attractions):
            cluster_idx = i % n_clusters
            if cluster_idx not in clusters:
                clusters[cluster_idx] = []
            clusters[cluster_idx].append(attr)
        print(f"📊 Distributed {len(attractions)} attractions evenly across {n_clusters} clusters")
        return clusters
    
    feature_cols = ['art', 'history', 'nature', 'food', 'adventure']
    features = [[a.get(c, 5) for c in feature_cols] for a in attractions]
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features)
    
    clusters = {}
    for i, attraction in enumerate(attractions):
        label = labels[i]
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(attraction)
    
    min_size = 2
    small_clusters = [k for k, v in clusters.items() if len(v) < min_size]
    
    if small_clusters:
        print(f"⚠️ Found {len(small_clusters)} clusters with < {min_size} attractions. Redistributing...")
        small_attractions = []
        for k in small_clusters:
            small_attractions.extend(clusters.pop(k))
        
        if small_attractions:
            other_clusters = list(clusters.keys())
            for i, attr in enumerate(small_attractions):
                target = other_clusters[i % len(other_clusters)]
                clusters[target].append(attr)
    
    return clusters


# ==========================================
# KNAPSACK OPTIMIZE
# ==========================================

def knapsack_optimize(activities, daily_budget):
    """Select activities that maximize value within budget"""
    if len(activities) == 0:
        return [], 0
    
    for a in activities:
        a['value'] = a.get('rating', 4.0) * 10
    
    n = len(activities)
    max_budget = min(daily_budget, 500)
    
    if max_budget <= 0:
        free_activities = [a for a in activities if int(a.get('price_foreigners', 0)) == 0]
        if free_activities:
            return free_activities[:3], 0
        return activities[:2], 0
    
    dp = [[0] * (max_budget + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        cost = int(activities[i-1].get('price_foreigners', 0))
        value = activities[i-1]['value']
        for w in range(max_budget + 1):
            if cost <= w:
                dp[i][w] = max(dp[i-1][w], dp[i-1][w - cost] + value)
            else:
                dp[i][w] = dp[i-1][w]
    
    selected = []
    total_cost = 0
    w = max_budget
    for i in range(n, 0, -1):
        cost = int(activities[i-1].get('price_foreigners', 0))
        if dp[i][w] != dp[i-1][w]:
            selected.append(activities[i-1])
            total_cost += cost
            w -= cost
    
    if len(selected) == 0:
        free = [a for a in activities if int(a.get('price_foreigners', 0)) == 0]
        if free:
            selected = free[:3]
        else:
            sorted_activities = sorted(activities, key=lambda x: int(x.get('price_foreigners', 0)))
            selected = sorted_activities[:3]
        total_cost = sum(int(a.get('price_foreigners', 0)) for a in selected)
    
    return selected, total_cost


# ==========================================
# HAVERSINE & TSP
# ==========================================

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    except (ValueError, TypeError):
        return 999999
    
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def tsp_optimize(attractions):
    """Find optimal route to visit all attractions"""
    if len(attractions) <= 1:
        return attractions
    
    unvisited = attractions.copy()
    route = [unvisited.pop(0)]
    
    while unvisited:
        last = route[-1]
        best_idx = 0
        best_dist = float('inf')
        
        for i, attraction in enumerate(unvisited):
            lat1 = last.get('lat', 0)
            lng1 = last.get('lng', 0)
            lat2 = attraction.get('lat', 0)
            lng2 = attraction.get('lng', 0)
            dist = haversine(lat1, lng1, lat2, lng2)
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        
        route.append(unvisited.pop(best_idx))
    
    return route


# ==========================================
# EXTRACT PRICE
# ==========================================

def extract_price(price_str):
    if not price_str:
        return 0
    numbers = re.findall(r'\d+', str(price_str))
    if numbers:
        return int(numbers[0])
    return 0


# ==========================================
# GENERATE ACTIVITY TIME SLOTS
# ==========================================

def generate_activity_time_slots(activity_count):
    """Generate time slots for activities placed between fixed meals."""
    slots = []
    morning_slots = ["09:00 AM", "10:30 AM"]
    afternoon_slots = ["01:00 PM", "02:30 PM", "04:00 PM"]
    all_slots = morning_slots + afternoon_slots
    
    if activity_count > len(all_slots):
        extra_slots = ["05:30 PM", "06:30 PM"]
        all_slots += extra_slots
    
    return all_slots[:activity_count]


# ==========================================
# PARSE TIME TO MINUTES
# ==========================================

def parse_time_to_minutes(time_str):
    """Convert time string like '08:30 AM' to minutes since midnight"""
    try:
        parts = time_str.split()
        if len(parts) == 2:
            time_part, ampm = parts
            hour, minute = map(int, time_part.split(':'))
            if ampm.upper() == 'PM' and hour != 12:
                hour += 12
            elif ampm.upper() == 'AM' and hour == 12:
                hour = 0
            return hour * 60 + minute
    except:
        pass
    return 0


# ==========================================
# GET REAL FOOD COSTS FROM API
# ==========================================

def get_real_food_costs(restaurants):
    """Extract real food costs from restaurant data"""
    if not restaurants:
        return None
    
    costs = []
    for r in restaurants:
        price_range = r.get('price_range', '$$')
        price_str = r.get('price', '')
        if price_str:
            num_price = extract_price(price_str)
            if num_price > 0:
                costs.append({
                    'breakfast': max(5, int(num_price * 0.3)),
                    'lunch': max(8, int(num_price * 0.4)),
                    'dinner': max(12, int(num_price * 0.5))
                })
                continue
        
        if price_range == '$':
            costs.append({'breakfast': 6, 'lunch': 10, 'dinner': 14})
        elif price_range == '$$':
            costs.append({'breakfast': 10, 'lunch': 15, 'dinner': 20})
        elif price_range == '$$$':
            costs.append({'breakfast': 15, 'lunch': 25, 'dinner': 35})
        elif price_range == '$$$$':
            costs.append({'breakfast': 25, 'lunch': 40, 'dinner': 55})
        else:
            costs.append({'breakfast': 8, 'lunch': 12, 'dinner': 18})
    
    if costs:
        avg_breakfast = sum(c['breakfast'] for c in costs) // len(costs)
        avg_lunch = sum(c['lunch'] for c in costs) // len(costs)
        avg_dinner = sum(c['dinner'] for c in costs) // len(costs)
        return {'breakfast': avg_breakfast, 'lunch': avg_lunch, 'dinner': avg_dinner}
    
    return None


# ==========================================
# GET REAL HOTEL COST FROM API
# ==========================================

def get_real_hotel_cost(hotels, daily_budget):
    """Extract real hotel cost from hotel data"""
    if not hotels:
        return None
    
    costs = []
    for h in hotels:
        price = extract_price(h.get('price', '0'))
        if price > 0:
            costs.append(price)
    
    if costs:
        min_hotel = int(daily_budget * 0.25)
        max_hotel = int(daily_budget * 0.5)
        filtered = [c for c in costs if min_hotel <= c <= max_hotel]
        if filtered:
            return sum(filtered) // len(filtered)
        else:
            avg_cost = sum(costs) // len(costs)
            if avg_cost > max_hotel:
                return max_hotel
            if avg_cost < min_hotel:
                return min_hotel
            return avg_cost
    
    return None


# ==========================================
# GENERATE TRIP OVERVIEW
# ==========================================

def generate_trip_overview_with_gemini(destination, days, preferences, attractions_count):
    """Generate a beautiful trip overview using Gemini with rate limit handling."""
    
    # Check cache first
    cache_key = f"overview_{destination}_{days}_{str(preferences)}"
    if cache_key in _description_cache:
        print(f"✅ Using cached overview for {destination}")
        return _description_cache[cache_key]
    
    if not gemini or not gemini.model:
        print(f"⚠️ Gemini not available for {destination} overview")
        return None
    
    # Use the rate-limited method from gemini_integration
    try:
        overview = gemini.generate_trip_overview(destination, days, preferences, attractions_count)
        if overview:
            _description_cache[cache_key] = overview
            print(f"✅ Generated trip overview with Gemini")
            return overview
    except Exception as e:
        print(f"⚠️ Gemini overview error: {e}")
    
    # Simple fallback if Gemini fails
    print(f"ℹ️ Using simple fallback overview for {destination}")
    return f"Welcome to {destination}, Nepal! Your {days}-day adventure awaits. Explore {attractions_count} amazing attractions in this beautiful country. 🌄"


# ==========================================
# MAIN GENERATION FUNCTION
# ==========================================

def generate_itinerary(destination, preferences, days, daily_budget, restaurants=None, hotels=None):
    print(f"🔍 generate_itinerary CALLED!")
    print(f"Destination: {destination}, Days: {days}, Daily Budget: ${daily_budget}")

    recommended = knn_recommend(destination, preferences, n_recommendations=15)
    if len(recommended) == 0:
        return []

    clusters = kmeans_cluster(recommended, n_clusters=days)
    print(f"📊 K-Means created {len(clusters)} clusters")
    
    for k, v in clusters.items():
        print(f"   Cluster {k+1}: {len(v)} attractions")

    # ----- Get REAL food costs from API -----
    food_costs = get_real_food_costs(restaurants)
    if food_costs:
        BREAKFAST_COST = food_costs.get('breakfast', 10)
        LUNCH_COST = food_costs.get('lunch', 15)
        DINNER_COST = food_costs.get('dinner', 20)
        print(f"💰 Real food costs from API: Breakfast ${BREAKFAST_COST}, Lunch ${LUNCH_COST}, Dinner ${DINNER_COST}")
    else:
        BREAKFAST_COST = 8
        LUNCH_COST = 12
        DINNER_COST = 18
        print(f"💰 Using fallback food costs: Breakfast ${BREAKFAST_COST}, Lunch ${LUNCH_COST}, Dinner ${DINNER_COST}")

    # ----- Get REAL hotel cost from API -----
    hotel_cost = get_real_hotel_cost(hotels, daily_budget)
    if hotel_cost:
        HOTEL_COST = hotel_cost
        print(f"🏨 Real hotel cost from API: ${HOTEL_COST}")
    else:
        HOTEL_COST = int(daily_budget * 0.3)
        print(f"🏨 Using fallback hotel cost: ${HOTEL_COST}")

    # ----- Sort restaurants by rating -----
    sorted_restaurants = []
    if restaurants and len(restaurants) > 0:
        sorted_restaurants = sorted(restaurants, key=lambda x: x.get('rating', 0) if isinstance(x.get('rating'), (int, float)) else 0, reverse=True)
        print(f"🍽️ Found {len(sorted_restaurants)} restaurants")

    # ----- Pick best hotel (closest to attractions) -----
    best_hotel = None
    if hotels and len(hotels) > 0 and recommended:
        centroid_lat, centroid_lng = calculate_centroid(recommended)
        print(f"📍 Attraction centroid: {centroid_lat}, {centroid_lng}")
        
        with_distance = []
        for h in hotels:
            h_lat = h.get('latitude', 0) or h.get('lat', 0)
            h_lng = h.get('longitude', 0) or h.get('lng', 0)
            if h_lat and h_lng:
                try:
                    h_lat = float(h_lat)
                    h_lng = float(h_lng)
                    dist = haversine(centroid_lat, centroid_lng, h_lat, h_lng)
                    with_distance.append((dist, h))
                except (ValueError, TypeError):
                    print(f"⚠️ Invalid coordinates for hotel: {h.get('name')}")
                    continue
        
        if with_distance:
            with_distance.sort(key=lambda x: x[0])
            best_hotel = with_distance[0][1]
            print(f"🏨 Best hotel: {best_hotel.get('name')} (distance: {with_distance[0][0]:.2f}km)")

    print(f"💰 Final Food Costs - Breakfast: ${BREAKFAST_COST}, Lunch: ${LUNCH_COST}, Dinner: ${DINNER_COST}")
    print(f"🏨 Final Hotel Cost: ${HOTEL_COST}")

    # ----- GENERATE TRIP OVERVIEW (Gemini with rate limiter) -----
    total_attractions = sum(len(v) for v in clusters.values())
    trip_overview = generate_trip_overview_with_gemini(destination, days, preferences, total_attractions)
    
    # ----- BUILD ITINERARY -----
    itinerary = []
    day_costs = []
    total_cost = 0
    num_restaurants = len(sorted_restaurants)

    for cluster_idx in range(days):
        # Determine candidate activities for this day
        if cluster_idx in clusters and len(clusters[cluster_idx]) > 0:
            candidate_activities = clusters[cluster_idx]
        else:
            candidate_activities = recommended[cluster_idx * 2:(cluster_idx + 1) * 2 + 1] or recommended[:3]

        # Budget left after fixed costs
        activities_budget = daily_budget - (BREAKFAST_COST + LUNCH_COST + DINNER_COST + HOTEL_COST)
        if activities_budget < 0:
            activities_budget = 0

        # Use knapsack to pick best activities
        daily_activities, activity_cost = knapsack_optimize(candidate_activities, activities_budget)
        if not daily_activities:
            free_activities = [a for a in candidate_activities if int(a.get('price_foreigners', 0)) == 0]
            if free_activities:
                daily_activities = free_activities[:2]
            else:
                daily_activities = candidate_activities[:2]
            activity_cost = sum(int(a.get('price_foreigners', 0)) for a in daily_activities)

        day_cost = activity_cost + BREAKFAST_COST + LUNCH_COST + DINNER_COST + HOTEL_COST
        optimized_route = tsp_optimize(daily_activities)

        # Generate time slots for activities
        activity_slots = generate_activity_time_slots(len(optimized_route))
        
        # Calculate centroid of THIS DAY's attractions
        day_centroid_lat, day_centroid_lng = calculate_centroid(optimized_route)

        # Find restaurants nearest to today's centroid
        nearest_restaurants = []
        if sorted_restaurants and day_centroid_lat != 0:
            nearest_restaurants = find_nearest_restaurants(sorted_restaurants, day_centroid_lat, day_centroid_lng, count=min(3, num_restaurants))

        # Build all activities with their times
        temp_activities = []
        
        # 1. Breakfast
        if len(nearest_restaurants) > 0:
            breakfast_rest = nearest_restaurants[0]
            breakfast_name = breakfast_rest.get('name', destination)
            breakfast_cuisine = format_cuisine(breakfast_rest.get('cuisine', ''))
            breakfast_title = f"Breakfast at {breakfast_name}"
            if breakfast_cuisine:
                breakfast_desc = f"Start your day with {breakfast_cuisine} cuisine at {breakfast_name}."
            else:
                breakfast_desc = f"Start your day with a delicious breakfast at {breakfast_name}."
        else:
            breakfast_title = f"Breakfast in {destination}"
            breakfast_desc = f"Start your day with a delicious breakfast in {destination}."

        temp_activities.append({
            'time': "08:30 AM",
            'title': breakfast_title,
            'description': breakfast_desc,
            'cost': BREAKFAST_COST,
            'duration': 1,
            'lat': 0,
            'lng': 0,
            'rating': 4.0,
            'is_meal': True
        })

        # 2. Attractions - USE DATASET DESCRIPTION
        for i, activity in enumerate(optimized_route):
            slot = activity_slots[i] if i < len(activity_slots) else "Flexible"
            description = get_attraction_description(activity)
            temp_activities.append({
                'time': slot,
                'title': activity.get('name', 'Attraction'),
                'description': description,
                'location': activity.get('city', destination),
                'cost': int(activity.get('price_foreigners', 0)),
                'duration': activity.get('time_hours', 2),
                'lat': activity.get('lat', 0),
                'lng': activity.get('lng', 0),
                'rating': activity.get('rating', 4.0)
            })

        # 3. Lunch
        if len(nearest_restaurants) > 1:
            lunch_rest = nearest_restaurants[1]
            lunch_name = lunch_rest.get('name', destination)
            lunch_cuisine = format_cuisine(lunch_rest.get('cuisine', ''))
            lunch_title = f"Lunch at {lunch_name}"
            if lunch_cuisine:
                lunch_desc = f"Enjoy {lunch_cuisine} cuisine at {lunch_name}."
            else:
                lunch_desc = f"Enjoy a delicious lunch at {lunch_name}."
        else:
            lunch_title = f"Lunch - Local Cuisine"
            lunch_desc = f"Enjoy a traditional lunch in {destination}."

        temp_activities.append({
            'time': "12:30 PM",
            'title': lunch_title,
            'description': lunch_desc,
            'cost': LUNCH_COST,
            'duration': 1,
            'lat': 0,
            'lng': 0,
            'rating': 4.0,
            'is_meal': True
        })

        # 4. Dinner
        if len(nearest_restaurants) > 2:
            dinner_rest = nearest_restaurants[2]
            dinner_name = dinner_rest.get('name', destination)
            dinner_cuisine = format_cuisine(dinner_rest.get('cuisine', ''))
            dinner_title = f"Dinner at {dinner_name}"
            if dinner_cuisine:
                dinner_desc = f"Savor {dinner_cuisine} cuisine at {dinner_name}."
            else:
                dinner_desc = f"Enjoy a delicious dinner at {dinner_name}."
        else:
            dinner_title = f"Dinner in {destination}"
            dinner_desc = f"Enjoy authentic dinner in {destination}."

        temp_activities.append({
            'time': "07:00 PM",
            'title': dinner_title,
            'description': dinner_desc,
            'cost': DINNER_COST,
            'duration': 1.5,
            'lat': 0,
            'lng': 0,
            'rating': 4.0,
            'is_meal': True
        })

        # 5. Hotel - ALWAYS show hotel name even if far
        if best_hotel:
            hotel_name = best_hotel.get('name', 'Recommended Hotel')
            hotel_title = f"Stay at {hotel_name}"
            hotel_desc = f"Comfortable accommodation at {hotel_name}."
        else:
            hotel_title = f"Stay at Recommended Hotel"
            hotel_desc = f"Comfortable accommodation for the night in {destination}."

        temp_activities.append({
            'time': "09:00 PM",
            'title': hotel_title,
            'description': hotel_desc,
            'cost': HOTEL_COST,
            'duration': 8,
            'lat': 0,
            'lng': 0,
            'rating': 4.0,
            'is_hotel': True
        })

        # Sort activities by time
        temp_activities.sort(key=lambda x: parse_time_to_minutes(x['time']))
        
        day_activities = temp_activities

        itinerary.append({
            'day': cluster_idx + 1,
            'activities': day_activities,
            'day_cost': day_cost,
            'activity_cost': activity_cost,
            'breakfast_cost': BREAKFAST_COST,
            'lunch_cost': LUNCH_COST,
            'dinner_cost': DINNER_COST,
            'hotel_cost': HOTEL_COST,
            'budget_used': day_cost,
            'budget_remaining': daily_budget - day_cost,
            'overview': trip_overview if cluster_idx == 0 else None
        })
        day_costs.append(day_cost)
        total_cost += day_cost

    print(f"✅ Generated itinerary for {len(itinerary)} days")
    print(f"💰 Daily costs: {day_costs}")
    print(f"💰 Total cost: {total_cost}")
    return itinerary