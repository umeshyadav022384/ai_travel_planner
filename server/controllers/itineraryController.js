// server/controllers/itineraryController.js

const Itinerary = require('../model/itinerarySchema');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const ML_SERVER_URL = 'http://localhost:5000';
const WEATHER_API_KEY = process.env.WEATHER_API_KEY;

// ==================== LOAD NEPAL DATASET ====================
const loadNepalDataset = () => {
  try {
    const filePath = path.join(__dirname, '../../python_server/datasets/nepal_attractions.json');

    const data = fs.readFileSync(filePath, 'utf8');
    const jsonData = JSON.parse(data);
    return jsonData.cities || [];
  } catch (error) {
    console.error('❌ Error loading Nepal dataset:', error.message);
    return [];
  }
};

// ==================== VALIDATE DESTINATION ====================
const validateDestination = (destination) => {
  const cities = loadNepalDataset();
  const normalizedInput = destination.toLowerCase().trim();
  
  // Check if destination exists in dataset
  const found = cities.find(city => 
    city.city.toLowerCase().includes(normalizedInput) || 
    normalizedInput.includes(city.city.toLowerCase())
  );
  
  if (found) {
    return { valid: true, city: found.city };
  }
  
  return { 
    valid: false, 
    availableCities: cities.map(c => c.city).slice(0, 15) // Limit for response
  };
};

// ==================== GET WEATHER ====================
const getWeather = async (destination, startDate, endDate) => {
  try {
    const url = `https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/${destination}/${startDate}/${endDate}?unitGroup=metric&include=days&key=${WEATHER_API_KEY}&contentType=json`;
    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    console.error('❌ Weather API error:', error.message);
    return null;
  }
};

// ==================== GET PACKING LIST ====================
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

// ==================== FALLBACK ACTIVITIES ====================
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

// ==================== GENERATE ITINERARY ====================
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
    
    // ==================== 1. VALIDATE DESTINATION ====================
    const validation = validateDestination(destination);
    
    if (!validation.valid) {
      console.log(`❌ Destination "${destination}" not found in Nepal dataset`);
      
      // Format available cities list
      const cityList = validation.availableCities.join(', ');
      
      return res.status(400).json({
        success: false,
        message: `Sorry, "${destination}" is not available in our Nepal travel database.`,
        suggestion: `We currently support these destinations in Nepal: ${cityList}`,
        availableCities: validation.availableCities,
        supportedDestinations: validation.availableCities,
        errorType: 'DESTINATION_NOT_SUPPORTED'
      });
    }
    
    console.log(`✅ Destination "${destination}" validated successfully!`);
    console.log(`📍 Matched city: ${validation.city}`);
    
    // ==================== 2. VALIDATE DATES ====================
    if (!startDate || !endDate) {
      return res.status(400).json({
        success: false,
        message: "Please provide both start and end dates."
      });
    }
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
    
    if (days <= 0) {
      return res.status(400).json({
        success: false,
        message: "End date must be after start date."
      });
    }
    
    if (days > 30) {
      return res.status(400).json({
        success: false,
        message: "Maximum trip duration is 30 days."
      });
    }
    
    // ==================== 3. FETCH WEATHER ====================
    const weatherData = await getWeather(destination, startDate, endDate);
    
    // ==================== 4. CALL ML SERVER ====================
    let dailyActivities = [];
    let mlSuccess = false;
    
    try {
      console.log("📡 Calling Python ML for attractions at:", `${ML_SERVER_URL}/api/ml/generate`);
      
      const mlResponse = await axios.post(`${ML_SERVER_URL}/api/ml/generate`, {
        destination: validation.city, // Use validated city name
        preferences,
        days,
        budget: budget || 500
      });
      
      console.log("✅ ML Response received");
      
      if (mlResponse.data && mlResponse.data.dailyActivities && mlResponse.data.dailyActivities.length > 0) {
        dailyActivities = mlResponse.data.dailyActivities;
        mlSuccess = true;
        console.log(`✅ Using ML attractions: ${dailyActivities.length} days`);
      } else {
        console.log("⚠️ ML returned empty, using fallback");
        dailyActivities = createFallbackActivities(validation.city, weatherData, days, startDate);
      }
    } catch (mlError) {
      console.error("❌ ML server error:", mlError.message);
      if (mlError.code === 'ECONNREFUSED') {
        console.error("⚠️ Python server is NOT running on port 5000!");
      }
      dailyActivities = createFallbackActivities(validation.city, weatherData, days, startDate);
    }
    
    // ==================== 5. ADD WEATHER TO ACTIVITIES ====================
    const weatherDays = weatherData?.days || [];
    for (let i = 0; i < dailyActivities.length && i < weatherDays.length; i++) {
      dailyActivities[i].weather = {
        condition: weatherDays[i]?.conditions || 'Unknown',
        tempMax: weatherDays[i]?.tempmax || 25,
        tempMin: weatherDays[i]?.tempmin || 15
      };
    }
    
    // ==================== 6. GET PACKING LIST ====================
    const packingResult = await getPackingList(weatherData, validation.city, dailyActivities, preferences);
    
    // ==================== 7. CALCULATE TOTAL COST ====================
    const totalCost = dailyActivities.reduce((sum, day) => {
      const dayCost = day.activities?.reduce((s, act) => s + (act.cost || 0), 0) || 0;
      return sum + dayCost;
    }, 0);
    
    // ==================== 8. RETURN SUCCESS RESPONSE ====================
    res.status(200).json({
      success: true,
      destination: validation.city,
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
      mlUsed: mlSuccess,
      message: `✅ Itinerary generated for ${validation.city}`
    });
    
  } catch (error) {
    console.error('❌ Generate itinerary error:', error);
    res.status(500).json({
      success: false,
      message: "Internal server error. Please try again later.",
      error: error.message
    });
  }
};

// ==================== GET SUPPORTED DESTINATIONS ====================
const getSupportedDestinations = (req, res) => {
  const cities = loadNepalDataset();
  const cityNames = cities.map(c => c.city);
  
  res.status(200).json({
    success: true,
    totalDestinations: cityNames.length,
    destinations: cityNames,
    message: "These are the Nepal destinations currently supported"
  });
};

// ==================== SAVE ITINERARY ====================
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
    
    // Validate destination before saving
    const validation = validateDestination(destination);
    if (!validation.valid) {
      return res.status(400).json({
        success: false,
        message: `Cannot save: "${destination}" is not a supported Nepal destination.`
      });
    }
    
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
    
    res.status(201).json({
      success: true,
      message: "Itinerary saved successfully!",
      itinerary
    });
  } catch (error) {
    console.error('❌ Save itinerary error:', error);
    res.status(500).json({
      success: false,
      message: "Failed to save itinerary.",
      error: error.message
    });
  }
};

// ==================== GET ALL ITINERARIES ====================
const getItineraries = async (req, res) => {
  try {
    const itineraries = await Itinerary.find({ user: req.user.id })
      .sort({ createdAt: -1 });
    res.status(200).json({
      success: true,
      count: itineraries.length,
      itineraries
    });
  } catch (error) {
    console.error('❌ Get itineraries error:', error);
    res.status(500).json({
      success: false,
      message: "Failed to retrieve itineraries.",
      error: error.message
    });
  }
};

// ==================== GET SINGLE ITINERARY ====================
const getItineraryById = async (req, res) => {
  try {
    const itinerary = await Itinerary.findById(req.params.id);
    
    if (!itinerary) {
      return res.status(404).json({
        success: false,
        message: "Itinerary not found"
      });
    }
    
    if (itinerary.user.toString() !== req.user.id) {
      return res.status(401).json({
        success: false,
        message: "Not authorized to view this itinerary"
      });
    }
    
    res.status(200).json({
      success: true,
      itinerary
    });
  } catch (error) {
    console.error('❌ Get itinerary error:', error);
    res.status(500).json({
      success: false,
      message: "Failed to retrieve itinerary.",
      error: error.message
    });
  }
};

// ==================== UPDATE ITINERARY STATUS ====================
const updateItineraryStatus = async (req, res) => {
  try {
    const { status } = req.body;
    const validStatuses = ['planned', 'ongoing', 'completed', 'cancelled'];
    
    if (!validStatuses.includes(status)) {
      return res.status(400).json({
        success: false,
        message: `Invalid status. Must be one of: ${validStatuses.join(', ')}`
      });
    }
    
    const itinerary = await Itinerary.findById(req.params.id);
    
    if (!itinerary) {
      return res.status(404).json({
        success: false,
        message: "Itinerary not found"
      });
    }
    
    if (itinerary.user.toString() !== req.user.id) {
      return res.status(401).json({
        success: false,
        message: "Not authorized to update this itinerary"
      });
    }
    
    itinerary.status = status;
    await itinerary.save();
    
    res.status(200).json({
      success: true,
      message: `Itinerary status updated to "${status}"`,
      itinerary
    });
  } catch (error) {
    console.error('❌ Update status error:', error);
    res.status(500).json({
      success: false,
      message: "Failed to update itinerary status.",
      error: error.message
    });
  }
};

// ==================== DELETE ITINERARY ====================
const deleteItinerary = async (req, res) => {
  try {
    const itinerary = await Itinerary.findById(req.params.id);
    
    if (!itinerary) {
      return res.status(404).json({
        success: false,
        message: "Itinerary not found"
      });
    }
    
    if (itinerary.user.toString() !== req.user.id) {
      return res.status(401).json({
        success: false,
        message: "Not authorized to delete this itinerary"
      });
    }
    
    await itinerary.deleteOne();
    res.status(200).json({
      success: true,
      message: "Itinerary deleted successfully",
      id: req.params.id
    });
  } catch (error) {
    console.error('❌ Delete itinerary error:', error);
    res.status(500).json({
      success: false,
      message: "Failed to delete itinerary.",
      error: error.message
    });
  }
};

module.exports = {
  generateItinerary,
  saveItinerary,
  getItineraries,
  getItineraryById,
  updateItineraryStatus,
  deleteItinerary,
  getSupportedDestinations,
  validateDestination
};