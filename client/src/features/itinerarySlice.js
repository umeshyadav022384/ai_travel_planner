import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";

// ============================================
// INITIAL STATE
// ============================================
const initialState = {
  // Data states
  itineraries: [],           // All saved itineraries for the user
  currentItinerary: null,    // Currently viewed/saved itinerary
  generatedItinerary: null,   // Newly generated itinerary (not saved yet)
  packingList: null,          // Packing list for generated itinerary
  weatherSummary: null,       // Weather summary for generated itinerary
  
  // UI states
  isLoading: false,
  isError: false,
  isSuccess: false,
  message: "",
};

// ============================================
// ASYNC THUNKS (API CALLS)
// ============================================

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
      return rejectWithValue(error.response?.data?.message || error.message);
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

// ============================================
// SLICE
// ============================================
const itinerarySlice = createSlice({
  name: "itinerary",
  initialState,
  reducers: {
    // Clear generated itinerary (when user saves or discards)
    clearGeneratedItinerary: (state) => {
      state.generatedItinerary = null;
      state.packingList = null;
      state.weatherSummary = null;
    },
    
    // Clear all itineraries (on logout)
    clearItineraries: (state) => {
      state.itineraries = [];
      state.currentItinerary = null;
    },
    
    // Reset states
    reset: (state) => {
      state.isLoading = false;
      state.isError = false;
      state.isSuccess = false;
      state.message = "";
    },
  },
  extraReducers: (builder) => {
    builder
      // ========== GENERATE ITINERARY ==========
      .addCase(generateItinerary.pending, (state) => {
        state.isLoading = true;
        state.isError = false;
        state.message = "";
      })
      .addCase(generateItinerary.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isSuccess = true;
        state.generatedItinerary = action.payload.dailyActivities;
        state.packingList = action.payload.packingList;
        state.weatherSummary = action.payload.weatherSummary;
      })
      .addCase(generateItinerary.rejected, (state, action) => {
        state.isLoading = false;
        state.isError = true;
        state.message = action.payload;
      })
      
      // ========== SAVE ITINERARY ==========
      .addCase(saveItinerary.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(saveItinerary.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isSuccess = true;
        state.itineraries.unshift(action.payload);  // Add to beginning
        state.generatedItinerary = null;  // Clear generated after save
        state.packingList = null;
      })
      .addCase(saveItinerary.rejected, (state, action) => {
        state.isLoading = false;
        state.isError = true;
        state.message = action.payload;
      })
      
      // ========== GET ALL ITINERARIES ==========
      .addCase(getItineraries.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(getItineraries.fulfilled, (state, action) => {
        state.isLoading = false;
        state.itineraries = action.payload;
      })
      .addCase(getItineraries.rejected, (state, action) => {
        state.isLoading = false;
        state.isError = true;
        state.message = action.payload;
      })
      
      // ========== GET SINGLE ITINERARY ==========
      .addCase(getItineraryById.fulfilled, (state, action) => {
        state.currentItinerary = action.payload;
      })
      
      // ========== DELETE ITINERARY ==========
      .addCase(deleteItinerary.fulfilled, (state, action) => {
        state.itineraries = state.itineraries.filter(
          (item) => item._id !== action.payload
        );
      })
      
      // ========== UPDATE STATUS ==========
      .addCase(updateItineraryStatus.fulfilled, (state, action) => {
        const index = state.itineraries.findIndex(
          (item) => item._id === action.payload._id
        );
        if (index !== -1) {
          state.itineraries[index] = action.payload;
        }
        if (state.currentItinerary?._id === action.payload._id) {
          state.currentItinerary = action.payload;
        }
      });
  },
});

// ============================================
// EXPORT ACTIONS & SELECTORS
// ============================================
export const { clearGeneratedItinerary, clearItineraries, reset } = itinerarySlice.actions;

// Selectors
export const getItineraryState = (state) => state.itinerary;
export const getGeneratedItinerary = (state) => state.itinerary.generatedItinerary;
export const getPackingList = (state) => state.itinerary.packingList;
export const getWeatherSummary = (state) => state.itinerary.weatherSummary;
export const getSavedItineraries = (state) => state.itinerary.itineraries;

export default itinerarySlice.reducer;