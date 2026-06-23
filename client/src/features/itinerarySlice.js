// client/src/features/itinerarySlice.js

import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";

const initialState = {
  // Data states
  itineraries: [],           // All saved itineraries for the user
  currentItinerary: null,    // Currently viewed/saved itinerary
  generatedItinerary: null,   // Newly generated itinerary (not saved yet)
  packingList: null,          // Packing list for generated itinerary
  weatherSummary: null,       // Weather summary for generated itinerary
  
  // Error states
  errorType: null,            // e.g., 'DESTINATION_NOT_SUPPORTED'
  availableCities: [],        // List of supported cities
  suggestion: "",             // Suggestion message for user
  
  // UI states
  isLoading: false,
  isError: false,
  isSuccess: false,
  message: "",
};

// ============================================================
// ASYNC THUNKS (API CALLS)
// ============================================================

// 1. GENERATE ITINERARY (Call ML server)
export const generateItinerary = createAsyncThunk(
  "itinerary/generate",
  async (formData, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem("user") 
        ? JSON.parse(localStorage.getItem("user")).token 
        : null;
      
      const response = await axios.post(
        "http://localhost:5001/api/itineraries/generate",
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    } catch (error) {
      // ✅ Pass the FULL error object from backend
      return rejectWithValue(error.response?.data || { 
        message: error.message,
        errorType: 'SERVER_ERROR'
      });
    }
  }
);

// 2. SAVE ITINERARY (Save to MongoDB)
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

// 3. GET ALL SAVED ITINERARIES
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

// 4. GET SINGLE ITINERARY BY ID
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

// 5. DELETE ITINERARY
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

// 6. UPDATE ITINERARY STATUS
export const updateItineraryStatus = createAsyncThunk(
  "itinerary/updateStatus",
  async ({ id, status }, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem("user") 
        ? JSON.parse(localStorage.getItem("user")).token 
        : null;
      
      const response = await axios.put(
        `http://localhost:5001/api/itineraries/${id}/status`,
        { status },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// 7. GET SUPPORTED DESTINATIONS
export const getSupportedDestinations = createAsyncThunk(
  "itinerary/getSupportedDestinations",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get(
        "http://localhost:5001/api/itineraries/supported-destinations"
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// ============================================================
// SLICE
// ============================================================

const itinerarySlice = createSlice({
  name: "itinerary",
  initialState,
  reducers: {
    // Clear generated itinerary (when user saves or discards)
    clearGeneratedItinerary: (state) => {
      state.generatedItinerary = null;
      state.packingList = null;
      state.weatherSummary = null;
      state.errorType = null;
      state.availableCities = [];
      state.suggestion = "";
      state.isError = false;
      state.message = "";
    },
    
    // Clear all itineraries (on logout)
    clearItineraries: (state) => {
      state.itineraries = [];
      state.currentItinerary = null;
    },
    
    // Reset all error states
    resetError: (state) => {
      state.isError = false;
      state.message = "";
      state.errorType = null;
      state.availableCities = [];
      state.suggestion = "";
    },
    
    // Reset all states
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
      // ========== GENERATE ITINERARY ==========
      .addCase(generateItinerary.pending, (state) => {
        state.isLoading = true;
        state.isError = false;
        state.isSuccess = false;
        state.message = "";
        state.errorType = null;
        state.availableCities = [];
        state.suggestion = "";
      })
      .addCase(generateItinerary.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isSuccess = true;
        state.isError = false;
        state.generatedItinerary = action.payload.dailyActivities;
        state.packingList = action.payload.packingList;
        state.weatherSummary = action.payload.weatherSummary;
        state.errorType = null;
        state.availableCities = [];
        state.message = action.payload.message || "Itinerary generated successfully!";
      })
      .addCase(generateItinerary.rejected, (state, action) => {
        state.isLoading = false;
        state.isError = true;
        state.isSuccess = false;
        
        // ✅ Store ALL error details from backend
        const errorData = action.payload || {};
        state.message = errorData.message || "Failed to generate itinerary";
        state.errorType = errorData.errorType || null;
        state.availableCities = errorData.availableCities || [];
        state.suggestion = errorData.suggestion || "";
        state.generatedItinerary = null;
        state.packingList = null;
        state.weatherSummary = null;
      })
      
      // ========== SAVE ITINERARY ==========
      .addCase(saveItinerary.pending, (state) => {
        state.isLoading = true;
        state.isError = false;
      })
      .addCase(saveItinerary.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isSuccess = true;
        state.itineraries.unshift(action.payload);
        state.generatedItinerary = null;
        state.packingList = null;
        state.weatherSummary = null;
        state.message = "Itinerary saved successfully!";
      })
      .addCase(saveItinerary.rejected, (state, action) => {
        state.isLoading = false;
        state.isError = true;
        state.message = action.payload || "Failed to save itinerary";
      })
      
      // ========== GET ALL ITINERARIES ==========
      .addCase(getItineraries.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(getItineraries.fulfilled, (state, action) => {
        state.isLoading = false;
        state.itineraries = action.payload.itineraries || action.payload || [];
        state.isError = false;
      })
      .addCase(getItineraries.rejected, (state, action) => {
        state.isLoading = false;
        state.isError = true;
        state.message = action.payload || "Failed to load itineraries";
      })
      
      // ========== GET SINGLE ITINERARY ==========
      .addCase(getItineraryById.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(getItineraryById.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentItinerary = action.payload.itinerary || action.payload;
        state.isError = false;
      })
      .addCase(getItineraryById.rejected, (state, action) => {
        state.isLoading = false;
        state.isError = true;
        state.message = action.payload || "Failed to load itinerary";
      })
      
      // ========== DELETE ITINERARY ==========
      .addCase(deleteItinerary.fulfilled, (state, action) => {
        state.itineraries = state.itineraries.filter(
          (item) => item._id !== action.payload && item.id !== action.payload
        );
        state.message = "Itinerary deleted successfully!";
      })
      .addCase(deleteItinerary.rejected, (state, action) => {
        state.isError = true;
        state.message = action.payload || "Failed to delete itinerary";
      })
      
      // ========== UPDATE STATUS ==========
      .addCase(updateItineraryStatus.fulfilled, (state, action) => {
        const updated = action.payload.itinerary || action.payload;
        const index = state.itineraries.findIndex(
          (item) => item._id === updated._id || item.id === updated.id
        );
        if (index !== -1) {
          state.itineraries[index] = updated;
        }
        if (state.currentItinerary?._id === updated._id || state.currentItinerary?.id === updated.id) {
          state.currentItinerary = updated;
        }
        state.message = `Status updated to "${updated.status}"`;
      })
      .addCase(updateItineraryStatus.rejected, (state, action) => {
        state.isError = true;
        state.message = action.payload || "Failed to update status";
      })
      
      // ========== GET SUPPORTED DESTINATIONS ==========
      .addCase(getSupportedDestinations.fulfilled, (state, action) => {
        state.availableCities = action.payload.destinations || [];
      });
  },
});

// ============================================================
// EXPORT ACTIONS
// ============================================================

export const { 
  clearGeneratedItinerary, 
  clearItineraries, 
  reset,
  resetError 
} = itinerarySlice.actions;

// ============================================================
// SELECTORS
// ============================================================

export const getItineraryState = (state) => state.itinerary;
export const getGeneratedItinerary = (state) => state.itinerary.generatedItinerary;
export const getPackingList = (state) => state.itinerary.packingList;
export const getWeatherSummary = (state) => state.itinerary.weatherSummary;
export const getSavedItineraries = (state) => state.itinerary.itineraries;
export const getItineraryError = (state) => ({
  isError: state.itinerary.isError,
  message: state.itinerary.message,
  errorType: state.itinerary.errorType,
  availableCities: state.itinerary.availableCities,
  suggestion: state.itinerary.suggestion,
});

export default itinerarySlice.reducer;