const Itinerary = require('../model/itinerarySchema');
const axios = require('axios');

const ML_SERVER_URL = 'http://localhost:5000';
const WEATHER_API_KEY = process.env.WEATHER_API_KEY;
// 1. Fetch weather data from external API
const getWeather = async (destination, startDate, endDate) => {
  try {
    const url = `https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/${destination}/${startDate}/${endDate}?unitGroup=metric&include=days&key=${WEATHER_API_KEY}&contentType=json`;
    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    console.error('Weather API error:', error.message);
    return null;
  }
};

// 2. Get packing list from Python ML server
const getPackingList = async (weatherData, destination, activities, preferences) => {
  try {
    console.log("📦 Calling Python packing algorithm...");
    const response = await axios.post(`${ML_SERVER_URL}/api/ml/packing`, {
      weatherData: weatherData || { days: [] },
      destination,
      activities: activities || [],
      preferences: preferences || {}
    });
    console.log("✅ Packing list received from Python");
    return response.data;
  } catch (error) {
    console.error("❌ Packing ML server error:", error.message);
    return {
      packingList: {
        essentials: ["📱 Phone", "💳 ID/Cards"],
        weather_based: ["☔ Umbrella"],
        recommended: ["👟 Comfortable shoes"],
        optional: [],
        alerts: [],
        tips: ["Check weather before packing"]
      },
      weatherSummary: { hasRain: false, maxTemp: 25, minTemp: 15 }
    };
  }
};

const generateItinerary = async (req, res) => {
  try {
    const { destination, startDate, endDate, preferences, budget, travelers } = req.body;
    
    console.log("=" .repeat(50));
    console.log("🎯 GENERATE ITINERARY CALLED");
    console.log("Destination:", destination);
    console.log("Start Date:", startDate);
    console.log("End Date:", endDate);
    console.log("Preferences:", preferences);
    console.log("=" .repeat(50));
    
    // Validate required fields
    if (!destination || !startDate || !endDate) {
      return res.status(400).json({ message: "Missing required fields" });
    }
    
    // Calculate number of days
    const start = new Date(startDate);
    const end = new Date(endDate);
    const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
    
    if (days <= 0) {
      return res.status(400).json({ message: "End date must be after start date" });
    }
    
    // 1. Fetch weather data
    const weatherData = await getWeather(destination, startDate, endDate);
    
    // 2. CALL PYTHON ML SERVER FOR ATTRACTIONS
    let dailyActivities = [];
    let mlSuccess = false;
    
    try {
      console.log("Calling Python ML for attractions at:", `${ML_SERVER_URL}/api/ml/generate`);
      
      const mlResponse = await axios.post(`${ML_SERVER_URL}/api/ml/generate`, {
        destination,
        preferences,
        days,
        budget: budget || 500
      });
      
      console.log(" ML Response Status:", mlResponse.status);
      console.log("ML Response Data:", JSON.stringify(mlResponse.data, null, 2));
      
      if (mlResponse.data && mlResponse.data.dailyActivities && mlResponse.data.dailyActivities.length > 0) {
        dailyActivities = mlResponse.data.dailyActivities;
        mlSuccess = true;
        console.log(` SUCCESS: Using ML attractions: ${dailyActivities.length} days`);
      } else {
        console.log(" ML returned empty, using fallback");
        dailyActivities = createFallbackActivities(destination, weatherData, days, startDate);
      }
    } catch (mlError) {
      console.error(" ML server error:", mlError.message);
      if (mlError.code === 'ECONNREFUSED') {
        console.error("Python server is NOT running on port 5000!");
      }
      dailyActivities = createFallbackActivities(destination, weatherData, days, startDate);
    }
    
    // Add weather info to each day
    const weatherDays = weatherData?.days || [];
    for (let i = 0; i < dailyActivities.length && i < weatherDays.length; i++) {
      dailyActivities[i].weather = {
        condition: weatherDays[i]?.conditions || 'Unknown',
        tempMax: weatherDays[i]?.tempmax || 25,
        tempMin: weatherDays[i]?.tempmin || 15
      };
    }
    
    // 3. Get packing list
    const packingResult = await getPackingList(weatherData, destination, dailyActivities, preferences);
    
    // Calculate total cost
    const totalCost = dailyActivities.reduce((sum, day) => {
      const dayCost = day.activities?.reduce((s, act) => s + (act.cost || 0), 0) || 0;
      return sum + dayCost;
    }, 0);
    
    res.status(200).json({
      success: true,
      destination,
      startDate,
      endDate,
      days,
      travelers,
      budget,
      totalCost,
      dailyActivities,
      packingList: packingResult.packingList,
      weatherSummary: packingResult.weatherSummary,
      generatedAt: new Date(),
      mlUsed: mlSuccess
    });
    
  } catch (error) {
    console.error('Generate itinerary error:', error);
    res.status(500).json({ message: error.message });
  }
};

// Fallback function (only used if ML server fails)
const createFallbackActivities = (destination, weatherData, days, startDate) => {
  console.log("📝 Creating fallback activities for", destination);
  const baseDate = new Date(startDate);
  const activities = [];
  for (let i = 0; i < days; i++) {
    const currentDate = new Date(baseDate);
    currentDate.setDate(baseDate.getDate() + i);
    activities.push({
      day: i + 1,
      date: currentDate,
      activities: [
        {
          time: "09:00 AM",
          title: `Explore ${destination}`,
          description: `Discover the beauty of ${destination}`,
          location: destination,
          cost: 0,
          duration: 2
        },
        {
          time: "12:00 PM",
          title: "Local Lunch",
          description: "Enjoy local cuisine",
          location: destination,
          cost: 15,
          duration: 1.5
        },
        {
          time: "03:00 PM",
          title: "Sightseeing",
          description: `Continue exploring ${destination}`,
          location: destination,
          cost: 20,
          duration: 3
        }
      ]
    });
  }
  return activities;
};

// 2. SAVE ITINERARY to database
const saveItinerary = async (req, res) => {
  try {
    const {
      destination,
      startDate,
      endDate,
      travelers,
      budget,
      preferences,
      dailyActivities,
      totalCost
    } = req.body;
    
    const itinerary = await Itinerary.create({
      user: req.user.id,
      destination,
      startDate,
      endDate,
      travelers: travelers || 1,
      budget: budget || 500,
      preferences: preferences || {},
      dailyActivities,
      totalCost: totalCost || 0,
      status: 'planned'
    });
    
    res.status(201).json(itinerary);
  } catch (error) {
    console.error('Save itinerary error:', error);
    res.status(500).json({ message: error.message });
  }
};

// 3. GET ALL USER ITINERARIES
const getItineraries = async (req, res) => {
  try {
    const itineraries = await Itinerary.find({ user: req.user.id })
      .sort({ createdAt: -1 });
    res.status(200).json(itineraries);
  } catch (error) {
    console.error('Get itineraries error:', error);
    res.status(500).json({ message: error.message });
  }
};

// 4. GET SINGLE ITINERARY BY ID
const getItineraryById = async (req, res) => {
  try {
    const itinerary = await Itinerary.findById(req.params.id);
    
    if (!itinerary) {
      return res.status(404).json({ message: "Itinerary not found" });
    }
    
    if (itinerary.user.toString() !== req.user.id) {
      return res.status(401).json({ message: "Not authorized" });
    }
    
    res.status(200).json(itinerary);
  } catch (error) {
    console.error('Get itinerary by ID error:', error);
    res.status(500).json({ message: error.message });
  }
};

// 5. UPDATE ITINERARY STATUS
const updateItineraryStatus = async (req, res) => {
  try {
    const { status } = req.body;
    const validStatuses = ['planned', 'ongoing', 'completed', 'cancelled'];
    
    if (!validStatuses.includes(status)) {
      return res.status(400).json({ message: "Invalid status" });
    }
    
    const itinerary = await Itinerary.findById(req.params.id);
    
    if (!itinerary) {
      return res.status(404).json({ message: "Itinerary not found" });
    }
    
    if (itinerary.user.toString() !== req.user.id) {
      return res.status(401).json({ message: "Not authorized" });
    }
    
    itinerary.status = status;
    await itinerary.save();
    
    res.status(200).json(itinerary);
  } catch (error) {
    console.error('Update status error:', error);
    res.status(500).json({ message: error.message });
  }
};

// 6. DELETE ITINERARY
const deleteItinerary = async (req, res) => {
  try {
    const itinerary = await Itinerary.findById(req.params.id);
    
    if (!itinerary) {
      return res.status(404).json({ message: "Itinerary not found" });
    }
    
    if (itinerary.user.toString() !== req.user.id) {
      return res.status(401).json({ message: "Not authorized" });
    }
    
    await itinerary.deleteOne();
    res.status(200).json({ message: "Itinerary deleted successfully", id: req.params.id });
  } catch (error) {
    console.error('Delete itinerary error:', error);
    res.status(500).json({ message: error.message });
  }
};

module.exports = {
  generateItinerary,
  saveItinerary,
  getItineraries,
  getItineraryById,
  updateItineraryStatus,
  deleteItinerary
};