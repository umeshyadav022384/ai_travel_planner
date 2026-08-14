// client/src/features/itinerarySlice.js

import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";

const initialState = {
  // Data states
  itineraries: [],
  currentItinerary: null,
  generatedItinerary: null,
  enhancedItinerary: null,
  packingList: null,
  weatherSummary: null,
  
  // Cost & Weather
  dailyCosts: [],
  totalCost: 0,
  budget: 0,
  dailyBudget: 0,
  weatherForecast: [],
  
  // Time Constraint States
  timeMode: "no_limit",
  availableHours: 0,
  timeDisplay: null,
  dailyTimeInfo: [],
  
  // Error states
  errorType: null,
  availableCities: [],
  suggestion: "",
  
  // UI states
  isLoading: false,
  isError: false,
  isSuccess: false,
  message: "",
  geminiUsed: false,
};

// ==========================================
// ASYNC THUNKS
// ==========================================

export const generateItinerary = createAsyncThunk(
  "itinerary/generate",
  async (formData, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem("user") 
        ? JSON.parse(localStorage.getItem("user")).token 
        : null;
      
      const response = await axios.post(
        "http://localhost:5000/api/ml/generate",
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      console.log("🔍 API Response:", response.data);
      
      return response.data;
    } catch (error) {
      console.error("❌ API Error:", error);
      return rejectWithValue(error.response?.data || { 
        message: error.message,
        errorType: 'SERVER_ERROR'
      });
    }
  }
);

export const saveItinerary = createAsyncThunk(
  "itinerary/save",
  async (itineraryData, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem("user") 
        ? JSON.parse(localStorage.getItem("user")).token 
        : null;
      
      const response = await axios.post(
        "http://localhost:5001/api/itineraries",
        itineraryData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

export const getItineraries = createAsyncThunk(
  "itinerary/getAll",
  async (_, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem("user") 
        ? JSON.parse(localStorage.getItem("user")).token 
        : null;
      
      const response = await axios.get(
        "http://localhost:5001/api/itineraries",
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

export const getItineraryById = createAsyncThunk(
  "itinerary/getById",
  async (id, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem("user") 
        ? JSON.parse(localStorage.getItem("user")).token 
        : null;
      
      const response = await axios.get(
        `http://localhost:5001/api/itineraries/${id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

export const deleteItinerary = createAsyncThunk(
  "itinerary/delete",
  async (id, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem("user") 
        ? JSON.parse(localStorage.getItem("user")).token 
        : null;
      
      await axios.delete(
        `http://localhost:5001/api/itineraries/${id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return id;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// ==========================================
// SLICE
// ==========================================

const itinerarySlice = createSlice({
  name: "itinerary",
  initialState,
  reducers: {
    clearGeneratedItinerary: (state) => {
      state.generatedItinerary = null;
      state.enhancedItinerary = null;
      state.packingList = null;
      state.weatherSummary = null;
      state.dailyCosts = [];
      state.totalCost = 0;
      state.budget = 0;
      state.dailyBudget = 0;
      state.weatherForecast = [];
      state.errorType = null;
      state.availableCities = [];
      state.suggestion = "";
      state.isError = false;
      state.message = "";
      state.geminiUsed = false;
      state.timeMode = "no_limit";
      state.availableHours = 0;
      state.timeDisplay = null;
      state.dailyTimeInfo = [];
    },
    clearItineraries: (state) => {
      state.itineraries = [];
      state.currentItinerary = null;
    },
    resetError: (state) => {
      state.isError = false;
      state.message = "";
      state.errorType = null;
      state.availableCities = [];
      state.suggestion = "";
    },
    reset: (state) => {
      state.isLoading = false;
      state.isError = false;
      state.isSuccess = false;
      state.message = "";
      state.errorType = null;
      state.availableCities = [];
      state.suggestion = "";
    },
  },
  
  extraReducers: (builder) => {
    builder
      .addCase(generateItinerary.pending, (state) => {
        state.isLoading = true;
        state.isError = false;
        state.isSuccess = false;
        state.message = "";
        state.errorType = null;
        state.availableCities = [];
        state.suggestion = "";
        state.enhancedItinerary = null;
        state.geminiUsed = false;
        state.dailyCosts = [];
        state.totalCost = 0;
        state.dailyBudget = 0;
        state.weatherForecast = [];
        state.timeMode = "no_limit";
        state.availableHours = 0;
        state.timeDisplay = null;
        state.dailyTimeInfo = [];
      })
      .addCase(generateItinerary.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isSuccess = true;
        state.isError = false;
        
        const payload = action.payload || {};
        
        // ⭐ CRITICAL FIX: Store the original itinerary with skipped_attractions
        state.generatedItinerary = payload.dailyActivities || null;
        
        // ⭐ Debug: Log skipped attractions from payload
        if (payload.dailyActivities) {
          payload.dailyActivities.forEach((day, idx) => {
            if (day.skipped_attractions && day.skipped_attractions.length > 0) {
              console.log(`📊 Day ${idx + 1} has ${day.skipped_attractions.length} skipped attractions`);
            }
          });
        }
        
        state.enhancedItinerary = payload.enhanced || null;
        state.packingList = payload.packingList || null;
        state.weatherSummary = payload.weatherSummary || null;
        state.geminiUsed = payload.gemini_used || false;
        state.dailyCosts = payload.dailyCosts || [];
        state.totalCost = payload.totalCost || 0;
        state.budget = payload.budget || 0;
        state.dailyBudget = payload.dailyBudget || 0;
        state.weatherForecast = payload.weatherForecast || [];
        state.errorType = null;
        state.availableCities = [];
        state.message = payload.message || "Itinerary generated successfully!";
        
        state.timeMode = payload.time_mode || "no_limit";
        state.availableHours = payload.available_hours || 0;
        state.timeDisplay = payload.time_display || null;
        state.dailyTimeInfo = payload.daily_time_info || [];
        
        console.log("✅ Redux State Updated:");
        console.log("  generatedItinerary:", state.generatedItinerary);
        console.log("  enhancedItinerary:", state.enhancedItinerary);
        console.log("  geminiUsed:", state.geminiUsed);
        console.log("  dailyCosts:", state.dailyCosts);
        console.log("  totalCost:", state.totalCost);
        console.log("  dailyBudget:", state.dailyBudget);
        console.log("  timeMode:", state.timeMode);
        console.log("  availableHours:", state.availableHours);
      })
      .addCase(generateItinerary.rejected, (state, action) => {
        state.isLoading = false;
        state.isError = true;
        state.isSuccess = false;
        state.enhancedItinerary = null;
        state.geminiUsed = false;
        state.dailyCosts = [];
        state.totalCost = 0;
        state.dailyBudget = 0;
        state.weatherForecast = [];
        state.timeMode = "no_limit";
        state.availableHours = 0;
        state.timeDisplay = null;
        state.dailyTimeInfo = [];
        
        const errorData = action.payload || {};
        state.message = errorData.message || "Failed to generate itinerary";
        state.errorType = errorData.errorType || null;
        state.availableCities = errorData.availableCities || [];
        state.suggestion = errorData.suggestion || "";
        state.generatedItinerary = null;
        state.packingList = null;
        state.weatherSummary = null;
      })
      .addCase(saveItinerary.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isSuccess = true;
        state.itineraries.unshift(action.payload);
        state.generatedItinerary = null;
        state.enhancedItinerary = null;
        state.packingList = null;
        state.weatherSummary = null;
        state.dailyCosts = [];
        state.totalCost = 0;
        state.message = "Itinerary saved successfully!";
        state.timeMode = "no_limit";
        state.availableHours = 0;
        state.timeDisplay = null;
        state.dailyTimeInfo = [];
      })
      .addCase(getItineraries.fulfilled, (state, action) => {
        state.isLoading = false;
        state.itineraries = action.payload.itineraries || action.payload || [];
        state.isError = false;
      })
      .addCase(getItineraryById.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentItinerary = action.payload.itinerary || action.payload;
        state.isError = false;
        if (state.currentItinerary) {
          state.timeMode = state.currentItinerary.timeMode || "no_limit";
          state.availableHours = state.currentItinerary.availableHours || 0;
          state.timeDisplay = state.currentItinerary.timeDisplay || null;
        }
      })
      .addCase(deleteItinerary.fulfilled, (state, action) => {
        state.itineraries = state.itineraries.filter(
          (item) => item._id !== action.payload && item.id !== action.payload
        );
        state.message = "Itinerary deleted successfully!";
      });
  },
});

// ==========================================
// EXPORT ACTIONS
// ==========================================

export const { 
  clearGeneratedItinerary, 
  clearItineraries, 
  reset,
  resetError 
} = itinerarySlice.actions;

// ==========================================
// SELECTORS
// ==========================================

export const getItineraryState = (state) => state.itinerary;
export const getGeneratedItinerary = (state) => state.itinerary.generatedItinerary;
export const getEnhancedItinerary = (state) => state.itinerary.enhancedItinerary;
export const getPackingList = (state) => state.itinerary.packingList;
export const getWeatherSummary = (state) => state.itinerary.weatherSummary;
export const getDailyCosts = (state) => state.itinerary.dailyCosts;
export const getTotalCost = (state) => state.itinerary.totalCost;
export const getBudget = (state) => state.itinerary.budget;
export const getDailyBudget = (state) => state.itinerary.dailyBudget;
export const getWeatherForecast = (state) => state.itinerary.weatherForecast;
export const getSavedItineraries = (state) => state.itinerary.itineraries;

// Time constraint selectors
export const getTimeMode = (state) => state.itinerary.timeMode;
export const getAvailableHours = (state) => state.itinerary.availableHours;
export const getTimeDisplay = (state) => state.itinerary.timeDisplay;
export const getDailyTimeInfo = (state) => state.itinerary.dailyTimeInfo;
export const hasTimeConstraint = (state) => state.itinerary.timeMode !== "no_limit";

export default itinerarySlice.reducer;