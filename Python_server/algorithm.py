import json
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from math import radians, sin, cos, sqrt, atan2
import os

# ============================================
# LOAD DATASET
# ============================================

def load_attractions():
    """Load attractions from JSON file"""
    file_path = os.path.join(os.path.dirname(__file__), 'datasets', 'nepal_attractions.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Flatten attractions from all cities
    all_attractions = []
    for city_data in data['cities']:
        for attraction in city_data['attractions']:
            attraction['city'] = city_data['city']
            all_attractions.append(attraction)
    
    return all_attractions

# ============================================
# KNN - RECOMMEND SIMILAR ATTRACTIONS
# ============================================

def knn_recommend(destination, preferences, n_recommendations=5):
    """
    Find attractions similar to user preferences using KNN
    """
    all_attractions = load_attractions()
    
    # Filter attractions by destination
    filtered = [a for a in all_attractions if a['city'].lower() == destination.lower()]
    
    if len(filtered) == 0:
        return []
    
    # Create feature matrix
    feature_cols = ['art', 'history', 'nature', 'food', 'adventure']
    user_vector = [[
        preferences.get('art', 5),
        preferences.get('history', 5),
        preferences.get('nature', 5),
        preferences.get('food', 5),
        preferences.get('adventure', 5)
    ]]
    
    attraction_vectors = [[
        a['art'], a['history'], a['nature'], a['food'], a['adventure']
    ] for a in filtered]
    
    # KNN
    knn = NearestNeighbors(n_neighbors=min(n_recommendations, len(filtered)), metric='euclidean')
    knn.fit(attraction_vectors)
    distances, indices = knn.kneighbors(user_vector)
    
    recommendations = []
    for idx in indices[0]:
        recommendations.append(filtered[idx])
    
    return recommendations

# ============================================
# K-MEANS - GROUP ATTRACTIONS BY DAYS
# ============================================

def kmeans_cluster(attractions, n_clusters=3):
    """
    Group attractions into clusters (one per day)
    """
    if len(attractions) <= n_clusters:
        return {i: [attractions[i]] for i in range(len(attractions))}
    
    feature_cols = ['art', 'history', 'nature', 'food', 'adventure']
    features = [[a[c] for c in feature_cols] for a in attractions]
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features)
    
    clusters = {}
    for i, attraction in enumerate(attractions):
        label = labels[i]
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(attraction)
    
    return clusters

# ============================================
# KNAPSACK - OPTIMIZE BUDGET
# ============================================

def knapsack_optimize(activities, daily_budget):
    """
    Select activities that maximize value within budget
    """
    if len(activities) == 0:
        return []
    
    # Calculate value based on rating and preferences
    for a in activities:
        a['value'] = a['rating'] * 10
    
    n = len(activities)
    dp = [[0] * (daily_budget + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        cost = min(activities[i-1].get('price_foreigners', 500), daily_budget)
        value = activities[i-1]['value']
        for w in range(daily_budget + 1):
            if cost <= w:
                dp[i][w] = max(dp[i-1][w], dp[i-1][w - cost] + value)
            else:
                dp[i][w] = dp[i-1][w]
    
    # Find selected items
    selected = []
    w = daily_budget
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected.append(activities[i-1])
            w -= min(activities[i-1].get('price_foreigners', 500), daily_budget)
    
    return selected

# ============================================
# TSP - OPTIMIZE ROUTE
# ============================================

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def tsp_optimize(attractions):
    """
    Find optimal route to visit all attractions
    """
    if len(attractions) <= 1:
        return attractions
    
    # Greedy algorithm for TSP
    unvisited = attractions.copy()
    route = [unvisited.pop(0)]
    
    while unvisited:
        last = route[-1]
        best_idx = 0
        best_dist = float('inf')
        
        for i, attraction in enumerate(unvisited):
            dist = haversine(last['lat'], last['lng'], attraction['lat'], attraction['lng'])
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        
        route.append(unvisited.pop(best_idx))
    
    return route

# ============================================
# MAIN GENERATION FUNCTION
# ============================================

def generate_itinerary(destination, preferences, days, daily_budget):
    """
    Generate complete itinerary using all algorithms
    """
    # 1. KNN - Get recommended attractions
    recommended = knn_recommend(destination, preferences, n_recommendations=15)
    
    if len(recommended) == 0:
        return []
    
    # 2. K-Means - Group into clusters (one per day)
    clusters = kmeans_cluster(recommended, n_clusters=days)
    
    itinerary = []
    for cluster_idx in range(days):
        if cluster_idx in clusters:
            # 3. Knapsack - Optimize budget for the day
            daily_activities = knapsack_optimize(clusters[cluster_idx], daily_budget)
            
            # 4. TSP - Optimize route order
            optimized_route = tsp_optimize(daily_activities)
            
            day_activities = []
            for i, activity in enumerate(optimized_route):
                day_activities.append({
                    'time': get_time_slot(i),
                    'title': activity['name'],
                    'description': activity.get('description', 'Beautiful attraction'),
                    'location': activity.get('city', destination),
                    'cost': activity.get('price_foreigners', 0),
                    'duration': activity.get('time_hours', 2),
                    'lat': activity['lat'],
                    'lng': activity['lng']
                })
            
            itinerary.append({
                'day': cluster_idx + 1,
                'activities': day_activities
            })
        else:
            itinerary.append({
                'day': cluster_idx + 1,
                'activities': []
            })
    
    return itinerary

def get_time_slot(index):
    """Return time slot based on activity order"""
    slots = ["09:00 AM", "11:00 AM", "01:00 PM", "03:00 PM", "05:00 PM", "07:00 PM"]
    return slots[index % len(slots)]