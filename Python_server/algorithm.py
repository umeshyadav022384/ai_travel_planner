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
    
    if isinstance(price_value, (int, float)):
        if price_value > max_price:
            return 0
        return int(price_value)
    
    if isinstance(price_value, str):
        numbers = re.findall(r'\d+', price_value)
        if numbers:
            price = int(numbers[0])
            if price > max_price:
                return 0
            return price
    
    return 0


# ==========================================
# ATTRACTION VALUE SCORING
# ==========================================

def calculate_attraction_score(attraction, user_preferences):
    """
    Calculate a value score for an attraction based on multiple factors.
    Score range: 0 to 1 (higher is better)
    """
    
    # 1. Interest Match Score (35%)
    features = ['art', 'history', 'nature', 'food', 'adventure']
    interest_match = 0
    total_weight = 0
    
    for feature in features:
        user_value = user_preferences.get(feature, 5)
        attraction_value = attraction.get(feature, 5)
        diff = abs(user_value - attraction_value) / 10.0
        weight = user_value / 10.0
        interest_match += (1 - diff) * weight
        total_weight += weight
    
    if total_weight > 0:
        interest_match = interest_match / total_weight
    else:
        interest_match = 0.5
    
    # 2. Rating Score (20%)
    rating = attraction.get('rating', 3.0)
    rating_score = rating / 5.0
    
    # 3. Time Efficiency Score (15%)
    time_hours = attraction.get('time_hours', 2)
    time_score = max(0.2, 1 - (time_hours / 6))
    
    # 4. Budget Efficiency Score (15%)
    price = safe_extract_price(attraction.get('price_foreigners', 0))
    if price == 0:
        budget_score = 1.0
    else:
        budget_score = max(0.1, 1 - (price / 300))
    
    # 5. Uniqueness Score (10%)
    uniqueness_score = attraction.get('uniqueness', 0.5)
    
    # 6. Seasonal Availability (5%)
    availability_score = 1.0
    
    total_score = (
        0.35 * interest_match +
        0.20 * rating_score +
        0.15 * time_score +
        0.15 * budget_score +
        0.10 * uniqueness_score +
        0.05 * availability_score
    )
    
    return min(1.0, max(0.0, total_score))


# ==========================================
# TIME-BASED SELECTION WITH MEALS
# ==========================================

def select_by_time(attractions, available_hours, user_preferences):
    """
    Select attractions within time limit, considering meals and travel.
    Returns: selected, skipped, total_time, time_breakdown
    """
    if not attractions or available_hours <= 0:
        return [], [], 0, {'attractions': 0, 'meals': 0, 'travel': 0}
    
    # Reserve time for fixed activities
    BREAKFAST_TIME = 0.5
    LUNCH_TIME = 0.5
    DINNER_TIME = 0.5
    MEAL_TIME = BREAKFAST_TIME + LUNCH_TIME + DINNER_TIME
    TRAVEL_TIME = 0.5
    FIXED_TIME = MEAL_TIME + TRAVEL_TIME
    
    available_attraction_time = available_hours - FIXED_TIME
    
    if available_attraction_time < 0.5:
        BREAKFAST_TIME = 0.25
        LUNCH_TIME = 0.25
        DINNER_TIME = 0.25
        MEAL_TIME = 0.75
        TRAVEL_TIME = 0.25
        FIXED_TIME = MEAL_TIME + TRAVEL_TIME
        available_attraction_time = available_hours - FIXED_TIME
        
        if available_attraction_time < 0.5:
            available_attraction_time = max(0.5, available_hours * 0.3)
    
    print(f"⏰ Time breakdown: Attractions: {available_attraction_time:.1f}h, "
          f"Meals: {MEAL_TIME:.1f}h, Travel: {TRAVEL_TIME:.1f}h")
    
    scored_attractions = []
    for attr in attractions:
        score = calculate_attraction_score(attr, user_preferences)
        scored_attractions.append({
            'attraction': attr,
            'score': score,
            'time_hours': attr.get('time_hours', 2)
        })
    
    scored_attractions.sort(key=lambda x: x['score'], reverse=True)
    
    selected = []
    skipped = []
    total_attraction_time = 0
    
    # ⭐ Select attractions within time limit
    for item in scored_attractions:
        attr_time = item['time_hours']
        if total_attraction_time + attr_time <= available_attraction_time:
            selected.append(item['attraction'])
            total_attraction_time += attr_time
        else:
            skipped.append(item['attraction'])
    
    # ⭐ CRITICAL: If no attractions selected, ALL are skipped
    if len(selected) == 0 and len(scored_attractions) > 0:
        print(f"⚠️ No attractions fit in {available_attraction_time:.1f}h, all {len(scored_attractions)} attractions are skipped")
        skipped = [item['attraction'] for item in scored_attractions]
    
    total_active_time = total_attraction_time + MEAL_TIME
    
    time_breakdown = {
        'attractions': total_attraction_time,
        'breakfast': BREAKFAST_TIME,
        'lunch': LUNCH_TIME,
        'dinner': DINNER_TIME,
        'meals': MEAL_TIME,
        'travel': TRAVEL_TIME,
        'total': total_active_time,
        'available': available_hours,
        'remaining': available_hours - total_active_time,
        'meal_breakdown': {
            'breakfast': BREAKFAST_TIME,
            'lunch': LUNCH_TIME,
            'dinner': DINNER_TIME
        }
    }
    
    return selected, skipped, total_active_time, time_breakdown


# ==========================================
# PRIORITY-BASED SELECTION
# ==========================================

def priority_select_attractions(attractions, user_preferences, max_attractions=None):
    if not attractions:
        return [], []
    
    scored = []
    for attr in attractions:
        score = calculate_attraction_score(attr, user_preferences)
        scored.append({'attraction': attr, 'score': score})
    
    scored.sort(key=lambda x: x['score'], reverse=True)
    
    if max_attractions:
        selected = [item['attraction'] for item in scored[:max_attractions]]
        skipped = [item['attraction'] for item in scored[max_attractions:]]
    else:
        selected = [item['attraction'] for item in scored]
        skipped = []
    
    return selected, skipped


# ==========================================
# ENHANCED TSP WITH PRIORITIES
# ==========================================

def tsp_with_priorities(attractions, start_point=None):
    if len(attractions) <= 1:
        return attractions
    
    unvisited = attractions.copy()
    
    if start_point and start_point in unvisited:
        route = [start_point]
        unvisited.remove(start_point)
    else:
        scored = []
        for attr in unvisited:
            score = attr.get('priority_score', attr.get('rating', 4.0) / 5.0)
            scored.append((score, attr))
        scored.sort(key=lambda x: x[0], reverse=True)
        route = [scored[0][1]]
        unvisited.remove(scored[0][1])
    
    while unvisited:
        last = route[-1]
        lat1 = last.get('lat', 0)
        lng1 = last.get('lng', 0)
        
        best_idx = 0
        best_score = -float('inf')
        
        for i, attraction in enumerate(unvisited):
            lat2 = attraction.get('lat', 0)
            lng2 = attraction.get('lng', 0)
            dist = haversine(lat1, lng1, lat2, lng2)
            
            value = attraction.get('priority_score', attraction.get('rating', 4.0) / 5.0)
            
            max_dist = 50
            dist_score = 1 - (min(dist, max_dist) / max_dist)
            combined_score = 0.4 * dist_score + 0.6 * value
            
            if combined_score > best_score:
                best_score = combined_score
                best_idx = i
        
        route.append(unvisited.pop(best_idx))
    
    return route


# ==========================================
# LOAD ATTRACTIONS
# ==========================================

def load_attractions():
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
                    price = attraction.get('price_foreigners', 0)
                    attraction['price_foreigners'] = safe_extract_price(price)
                    if 'time_hours' not in attraction:
                        attraction['time_hours'] = 2
                    all_attractions.append(attraction)
            
            print(f"✅ Loaded {len(all_attractions)} total attractions")
            return all_attractions
    
    print("❌ No dataset file found!")
    return []


# ==========================================
# KNN RECOMMEND
# ==========================================

def knn_recommend(destination, preferences, n_recommendations=15):
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
    slots = []
    base_hour = 9
    base_minute = 0
    
    for i in range(activity_count):
        hour = base_hour + (i * 1)
        minute = base_minute + (i * 30)
        
        if minute >= 60:
            hour += minute // 60
            minute = minute % 60
        
        if hour >= 12:
            ampm = "PM"
            display_hour = hour - 12 if hour > 12 else hour
        else:
            ampm = "AM"
            display_hour = hour if hour > 0 else 12
        
        display_hour = 12 if display_hour == 0 else display_hour
        time_str = f"{display_hour:02d}:{minute:02d} {ampm}"
        slots.append(time_str)
    
    return slots


# ==========================================
# PARSE TIME TO MINUTES
# ==========================================

def parse_time_to_minutes(time_str):
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
    cache_key = f"overview_{destination}_{days}_{str(preferences)}"
    if cache_key in _description_cache:
        print(f"✅ Using cached overview for {destination}")
        return _description_cache[cache_key]
    
    if not gemini or not gemini.model:
        print(f"⚠️ Gemini not available for {destination} overview")
        return None
    
    try:
        overview = gemini.generate_trip_overview(destination, days, preferences, attractions_count)
        if overview:
            _description_cache[cache_key] = overview
            print(f"✅ Generated trip overview with Gemini")
            return overview
    except Exception as e:
        print(f"⚠️ Gemini overview error: {e}")
    
    print(f"ℹ️ Using simple fallback overview for {destination}")
    return f"Welcome to {destination}, Nepal! Your {days}-day adventure awaits. Explore {attractions_count} amazing attractions in this beautiful country. 🌄"


# ==========================================
# ⭐ COMPLETELY UPDATED MAIN GENERATION FUNCTION
# ==========================================

def generate_itinerary(destination, preferences, days, daily_budget, 
                       restaurants=None, hotels=None, 
                       time_mode="no_limit", available_hours=6):
    """
    Generate itinerary with proper time calculation and skipped attractions tracking.
    """
    print(f"🔍 generate_itinerary CALLED!")
    print(f"Destination: {destination}, Days: {days}, Daily Budget: ${daily_budget}")
    print(f"⏰ Time Mode: {time_mode}, Available Hours: {available_hours}")

    # STEP 1: KNN RECOMMENDATION
    recommended = knn_recommend(destination, preferences, n_recommendations=15)
    if len(recommended) == 0:
        return []

    # STEP 2: CALCULATE ATTRACTION SCORES
    for attr in recommended:
        attr['priority_score'] = calculate_attraction_score(attr, preferences)
    
    # STEP 3: APPLY TIME CONSTRAINT
    hours_per_day = available_hours
    
    if time_mode == "total":
        hours_per_day = available_hours / days if days > 0 else available_hours
        print(f"⏰ Total hours: {available_hours}, Per day: {hours_per_day:.1f}h")
    elif time_mode == "per_day":
        print(f"⏰ Per day hours: {available_hours}h")
    else:
        hours_per_day = 24
        print(f"⏰ No time limit - Full day")

    # STEP 4: K-MEANS CLUSTERING
    clusters = kmeans_cluster(recommended, n_clusters=days)
    print(f"📊 K-Means created {len(clusters)} clusters")
    
    for k, v in clusters.items():
        print(f"   Cluster {k+1}: {len(v)} attractions")

    # STEP 5: GET COSTS FROM API
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

    hotel_cost = get_real_hotel_cost(hotels, daily_budget)
    if hotel_cost:
        HOTEL_COST = hotel_cost
        print(f"🏨 Real hotel cost from API: ${HOTEL_COST}")
    else:
        HOTEL_COST = int(daily_budget * 0.3)
        print(f"🏨 Using fallback hotel cost: ${HOTEL_COST}")

    # STEP 6: SORT RESTAURANTS
    sorted_restaurants = []
    if restaurants and len(restaurants) > 0:
        sorted_restaurants = sorted(restaurants, key=lambda x: x.get('rating', 0) if isinstance(x.get('rating'), (int, float)) else 0, reverse=True)
        print(f"🍽️ Found {len(sorted_restaurants)} restaurants")

    # STEP 7: SELECT BEST HOTEL
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
                    continue
        
        if with_distance:
            with_distance.sort(key=lambda x: x[0])
            best_hotel = with_distance[0][1]
            print(f"🏨 Best hotel: {best_hotel.get('name')} (distance: {with_distance[0][0]:.2f}km)")

    # STEP 8: GENERATE TRIP OVERVIEW
    total_attractions = sum(len(v) for v in clusters.values())
    trip_overview = generate_trip_overview_with_gemini(destination, days, preferences, total_attractions)
    
    # STEP 9: BUILD ITINERARY
    itinerary = []
    day_costs = []
    total_cost = 0
    num_restaurants = len(sorted_restaurants)

    # Rotate restaurants for variety
    if sorted_restaurants:
        rotated_restaurants = []
        for i in range(days):
            start_idx = i % len(sorted_restaurants)
            rotated = sorted_restaurants[start_idx:] + sorted_restaurants[:start_idx]
            rotated_restaurants.append(rotated)

    for cluster_idx in range(days):
        # Get candidate activities
        if cluster_idx in clusters and len(clusters[cluster_idx]) > 0:
            candidate_activities = clusters[cluster_idx]
        else:
            candidate_activities = recommended[cluster_idx * 2:(cluster_idx + 1) * 2 + 1] or recommended[:3]

        # ==========================================
        # ⭐ APPLY TIME CONSTRAINT WITH PROPER CALCULATION
        # ==========================================
        if time_mode != "no_limit":
            selected_attractions, skipped_attractions, total_active_time, time_breakdown = select_by_time(
                candidate_activities, 
                hours_per_day, 
                preferences
            )
            
            # Extract meal times from breakdown
            meal_breakdown = time_breakdown.get('meal_breakdown', {})
            breakfast_hours = meal_breakdown.get('breakfast', 0.5)
            lunch_hours = meal_breakdown.get('lunch', 0.5)
            dinner_hours = meal_breakdown.get('dinner', 0.5)
            travel_hours = time_breakdown.get('travel', 0.5)
            
            print(f"⏰ Day {cluster_idx+1}: "
                  f"Attractions: {time_breakdown['attractions']:.1f}h, "
                  f"Meals: {time_breakdown['meals']:.1f}h, "
                  f"Travel: {time_breakdown['travel']:.1f}h, "
                  f"Total: {time_breakdown['total']:.1f}h")
        else:
            # No time limit - use all attractions
            selected_attractions = candidate_activities
            skipped_attractions = []
            total_active_time = sum(a.get('time_hours', 2) for a in selected_attractions)
            
            breakfast_hours = 1.0
            lunch_hours = 1.0
            dinner_hours = 1.5
            travel_hours = 0.5
            
            time_breakdown = {
                'attractions': total_active_time,
                'meals': 3.5,
                'travel': 0.5,
                'total': total_active_time + 3.5,
                'available': 24,
                'remaining': 24 - (total_active_time + 3.5),
                'meal_breakdown': {
                    'breakfast': 1.0,
                    'lunch': 1.0,
                    'dinner': 1.5
                }
            }
        
        # Budget after fixed costs
        fixed_cost = BREAKFAST_COST + LUNCH_COST + DINNER_COST + HOTEL_COST
        activities_budget = daily_budget - fixed_cost
        if activities_budget < 0:
            activities_budget = 0

        # Use knapsack to pick best activities
        daily_activities, activity_cost = knapsack_optimize(selected_attractions, activities_budget)
        if not daily_activities:
            free_activities = [a for a in selected_attractions if int(a.get('price_foreigners', 0)) == 0]
            if free_activities:
                daily_activities = free_activities[:2]
            else:
                daily_activities = selected_attractions[:2]
            activity_cost = sum(int(a.get('price_foreigners', 0)) for a in daily_activities)

        # Fixed costs may be 0 if no restaurants/hotels
        actual_breakfast = BREAKFAST_COST if sorted_restaurants else 0
        actual_lunch = LUNCH_COST if sorted_restaurants else 0
        actual_dinner = DINNER_COST if sorted_restaurants else 0
        actual_hotel = HOTEL_COST if hotels else 0
        
        day_cost = activity_cost + actual_breakfast + actual_lunch + actual_dinner + actual_hotel
        
        # ⭐ Use Enhanced TSP with Priorities
        optimized_route = tsp_with_priorities(daily_activities)

        # Generate time slots for activities
        activity_slots = generate_activity_time_slots(len(optimized_route))
        
        # Calculate centroid of THIS DAY's attractions
        day_centroid_lat, day_centroid_lng = calculate_centroid(optimized_route)

        # Find restaurants nearest to today's centroid
        nearest_restaurants = []
        if sorted_restaurants and day_centroid_lat != 0:
            day_restaurants = rotated_restaurants[cluster_idx] if sorted_restaurants else sorted_restaurants
            nearest_restaurants = find_nearest_restaurants(day_restaurants, day_centroid_lat, day_centroid_lng, count=min(3, num_restaurants))

        # ==========================================
        # BUILD ACTIVITIES WITH PROPER TIME SLOTS
        # ==========================================
        temp_activities = []
        
        # 1. Breakfast
        breakfast_time = "08:30 AM"
        
        if sorted_restaurants and len(nearest_restaurants) > 0:
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
            'time': breakfast_time,
            'title': breakfast_title,
            'description': breakfast_desc,
            'cost': actual_breakfast,
            'duration': 0.5,
            'time_hours': 0.5,
            'lat': 0,
            'lng': 0,
            'rating': 4.0,
            'is_meal': True
        })

        # 2. Attractions
        for i, activity in enumerate(optimized_route):
            slot = activity_slots[i] if i < len(activity_slots) else "Flexible"
            time_hours = activity.get('time_hours', 1)
            
            description = get_attraction_description(activity)
            temp_activities.append({
                'time': slot,
                'title': activity.get('name', 'Attraction'),
                'description': description,
                'location': activity.get('city', destination),
                'cost': int(activity.get('price_foreigners', 0)),
                'duration': time_hours,
                'time_hours': time_hours,
                'lat': activity.get('lat', 0),
                'lng': activity.get('lng', 0),
                'rating': activity.get('rating', 4.0),
                'priority_score': activity.get('priority_score', 0.5)
            })

        # 3. Lunch
        lunch_time = "12:30 PM"
        
        if sorted_restaurants and len(nearest_restaurants) > 1:
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
            'time': lunch_time,
            'title': lunch_title,
            'description': lunch_desc,
            'cost': actual_lunch,
            'duration': 0.5,
            'time_hours': 0.5,
            'lat': 0,
            'lng': 0,
            'rating': 4.0,
            'is_meal': True
        })

        # 4. Dinner
        dinner_time = "07:00 PM"
        
        if sorted_restaurants and len(nearest_restaurants) > 2:
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
            'time': dinner_time,
            'title': dinner_title,
            'description': dinner_desc,
            'cost': actual_dinner,
            'duration': 0.5,
            'time_hours': 0.5,
            'lat': 0,
            'lng': 0,
            'rating': 4.0,
            'is_meal': True
        })

        # 5. Hotel
        hotel_time = "09:00 PM"
        if best_hotel:
            hotel_name = best_hotel.get('name', 'Recommended Hotel')
            hotel_title = f"Stay at {hotel_name}"
            hotel_desc = f"Comfortable accommodation at {hotel_name}."
        else:
            hotel_title = f"Stay at Recommended Hotel"
            hotel_desc = f"Comfortable accommodation for the night in {destination}."

        temp_activities.append({
            'time': hotel_time,
            'title': hotel_title,
            'description': hotel_desc,
            'cost': actual_hotel,
            'duration': 0,
            'time_hours': 0,
            'lat': 0,
            'lng': 0,
            'rating': 4.0,
            'is_hotel': True
        })

        # Sort activities by time
        temp_activities.sort(key=lambda x: parse_time_to_minutes(x['time']))
        
        day_activities = temp_activities

        # ⭐ Build day data with complete time info
        day_data = {
            'day': cluster_idx + 1,
            'activities': day_activities,
            'day_cost': day_cost,
            'activity_cost': activity_cost,
            'breakfast_cost': actual_breakfast,
            'lunch_cost': actual_lunch,
            'dinner_cost': actual_dinner,
            'hotel_cost': actual_hotel,
            'budget_used': day_cost,
            'budget_remaining': daily_budget - day_cost,
            'overview': trip_overview if cluster_idx == 0 else None,
            'time_info': {
                'time_available': hours_per_day,
                'time_used': time_breakdown['total'],
                'time_remaining': time_breakdown['remaining'],
                'attraction_time': time_breakdown['attractions'],
                'meal_time': time_breakdown['meals'],
                'travel_time': time_breakdown['travel'],
                'meal_breakdown': time_breakdown.get('meal_breakdown', {})
            }
        }
        
        # ⭐ FIX: Add skipped attractions - ALWAYS add if time_mode is not no_limit
        if time_mode != "no_limit":
            # Get all skipped attractions from the cluster
            all_cluster_attractions = clusters.get(cluster_idx, [])
            
            # If selected_attractions is empty, ALL cluster attractions are skipped
            if len(selected_attractions) == 0 and len(all_cluster_attractions) > 0:
                skipped_attractions = all_cluster_attractions.copy()
                print(f"  📝 Day {cluster_idx+1}: No attractions fit, all {len(skipped_attractions)} attractions are skipped")
            
            # Add skipped attractions to day_data
            if skipped_attractions:
                day_data['skipped_attractions'] = [
                    {
                        'name': a.get('name', 'Unknown'), 
                        'time_hours': a.get('time_hours', 2),
                        'score': calculate_attraction_score(a, preferences)
                    } 
                    for a in skipped_attractions
                ]
                print(f"  📝 Day {cluster_idx+1}: {len(day_data['skipped_attractions'])} attractions skipped")
            else:
                day_data['skipped_attractions'] = []
        
        itinerary.append(day_data)
        day_costs.append(day_cost)
        total_cost += day_cost

    # ⭐ Print summary
    print("\n📊 ATTRACTION TIME SUMMARY:")
    for day in itinerary:
        print(f"  Day {day['day']}:")
        for activity in day.get('activities', []):
            if not activity.get('is_meal') and not activity.get('is_hotel'):
                print(f"    - {activity['title']}: {activity.get('time_hours', 'N/A')}h")
        if day.get('skipped_attractions'):
            print(f"    ⚠️ Skipped: {len(day.get('skipped_attractions', []))} attractions")

    print(f"\n✅ Generated itinerary for {len(itinerary)} days")
    print(f"💰 Daily costs: {day_costs}")
    print(f"💰 Total cost: {total_cost}")
    return itinerary