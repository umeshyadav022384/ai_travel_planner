// client/src/components/Generate/Generate.jsx

import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { toast } from "react-toastify";
import {
  generateItinerary,
  clearGeneratedItinerary,
  saveItinerary,
} from "../../features/itinerarySlice";
import PackingList from "../PackingList/PackingList";
import "./Generate.scss";

const Generate = () => {
  const dispatch = useDispatch();
  const { isLoading, generatedItinerary, packingList, weatherSummary } =
    useSelector((state) => state.itinerary);

  const [formData, setFormData] = useState({
    destination: "",
    startDate: "",
    endDate: "",
    travelers: 1,
    budget: 500,
    preferences: {
      art: 5,
      history: 5,
      nature: 5,
      food: 5,
      adventure: 5,
    },
  });

  const [minEndDate, setMinEndDate] = useState("");
  const [totalDays, setTotalDays] = useState(0);
  const [showResult, setShowResult] = useState(false);

  // ==================== DATE VALIDATION ====================
  useEffect(() => {
    if (formData.startDate) {
      const start = new Date(formData.startDate);
      const minEnd = new Date(start);
      minEnd.setDate(minEnd.getDate() + 1);
      setMinEndDate(minEnd.toISOString().split("T")[0]);

      if (formData.endDate) {
        const end = new Date(formData.endDate);
        const diffTime = Math.abs(end - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        setTotalDays(diffDays + 1);
      }
    }
  }, [formData.startDate, formData.endDate]);

  // ==================== HANDLERS ====================
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handlePreferenceChange = (category, value) => {
    setFormData((prev) => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [category]: parseInt(value),
      },
    }));
  };

  const handleClear = () => {
    dispatch(clearGeneratedItinerary());
    setFormData({
      destination: "",
      startDate: "",
      endDate: "",
      travelers: 1,
      budget: 500,
      preferences: {
        art: 5,
        history: 5,
        nature: 5,
        food: 5,
        adventure: 5,
      },
    });
    setShowResult(false);
    toast.info("Form cleared");
  };

  // ==================== HANDLE SUBMIT (UPDATED) ====================
  const handleSubmit = async (e) => {
    e.preventDefault();

    // ==================== VALIDATIONS ====================
    if (!formData.destination.trim()) {
      toast.error("📍 Please enter a destination");
      return;
    }

    if (!formData.startDate) {
      toast.error("📅 Please select a start date");
      return;
    }

    if (!formData.endDate) {
      toast.error("📅 Please select an end date");
      return;
    }

    const start = new Date(formData.startDate);
    const end = new Date(formData.endDate);

    if (end <= start) {
      toast.error("⚠️ End date must be after start date");
      return;
    }

    const diffDays = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
    if (diffDays > 30) {
      toast.warning("⚠️ Maximum trip duration is 30 days");
      return;
    }

    if (formData.travelers < 1) {
      toast.error("👥 At least 1 traveler is required");
      return;
    }

    if (formData.budget < 50) {
      toast.error("💰 Minimum budget is $50 per day");
      return;
    }

    // ==================== DISPATCH ====================
    dispatch(clearGeneratedItinerary());
    setShowResult(false);

    try {
      const result = await dispatch(generateItinerary(formData));

      // ==================== SUCCESS ====================
      if (generateItinerary.fulfilled.match(result)) {
        setShowResult(true);
        toast.success("✨ Itinerary generated successfully!");
      }
      // ==================== DESTINATION NOT SUPPORTED ====================
      else if (result.payload?.errorType === 'DESTINATION_NOT_SUPPORTED') {
        const { message, suggestion, availableCities } = result.payload;

        toast.error(
          <div>
            <strong>{message}</strong>
            <p style={{ fontSize: '13px', marginTop: '8px' }}>
              {suggestion}
            </p>
            <details style={{ fontSize: '12px', marginTop: '4px' }}>
              <summary>📍 Show all supported destinations</summary>
              <p style={{ marginTop: '4px', color: '#555' }}>
                {availableCities?.join(', ') || 'Nepal destinations only'}
              </p>
            </details>
          </div>,
          { autoClose: false }
        );
      }
      // ==================== OTHER ERRORS ====================
      else {
        toast.error(result.payload?.message || "❌ Failed to generate itinerary");
      }
    } catch (error) {
      toast.error("Something went wrong. Please try again.");
      console.error("Generate error:", error);
    }
  };

  // ==================== HANDLE SAVE ====================
  const handleSave = async () => {
    const itineraryData = {
      destination: formData.destination,
      startDate: formData.startDate,
      endDate: formData.endDate,
      travelers: formData.travelers,
      budget: formData.budget,
      preferences: formData.preferences,
      dailyActivities: generatedItinerary,
      totalCost: generatedItinerary?.reduce(
        (sum, day) =>
          sum +
          day.activities?.reduce(
            (daySum, activity) => daySum + (activity.cost || 0),
            0,
          ),
        0,
      ),
    };

    const result = await dispatch(saveItinerary(itineraryData));

    if (saveItinerary.fulfilled.match(result)) {
      toast.success("💾 Itinerary saved successfully!");
    } else {
      toast.error(result.payload || "❌ Failed to save itinerary");
    }
  };

  // ==================== PREFERENCE CONFIG ====================
  const preferenceCategories = [
    {
      key: "art",
      label: "Art & Museums",
      icon: "🎨",
      color: "#e91e63",
      description: "Galleries, exhibitions, street art",
    },
    {
      key: "history",
      label: "History & Heritage",
      icon: "🏛️",
      color: "#795548",
      description: "Monuments, temples, ancient sites",
    },
    {
      key: "nature",
      label: "Nature & Outdoors",
      icon: "🌿",
      color: "#4caf50",
      description: "Parks, hiking, wildlife",
    },
    {
      key: "food",
      label: "Food & Cuisine",
      icon: "🍜",
      color: "#ff9800",
      description: "Local dishes, restaurants, food tours",
    },
    {
      key: "adventure",
      label: "Adventure & Sports",
      icon: "⚡",
      color: "#2196f3",
      description: "Trekking, rafting, activities",
    },
  ];

  // ==================== RENDER ====================
  return (
    <div className="generate-container">
      {/* Form Section */}
      <div className="form-section">
        <div className="form-header">
          <h1>✈️ Plan Your Perfect Trip</h1>
          <p>Tell us about your travel plans and we'll create a personalized itinerary</p>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Trip Details */}
          <div className="section-title">
            <span className="icon">📍</span>
            <h3>Trip Details</h3>
          </div>

          <div className="input-group">
            <label htmlFor="destination">Destination *</label>
            <input
              id="destination"
              type="text"
              name="destination"
              value={formData.destination}
              onChange={handleChange}
              placeholder="e.g., Pokhara, Janakpur, Kathmandu"
              className="destination-input"
            />
          </div>

          <div className="row">
            <div className="input-group">
              <label htmlFor="startDate">Start Date *</label>
              <input
                id="startDate"
                type="date"
                name="startDate"
                value={formData.startDate}
                onChange={handleChange}
                min={new Date().toISOString().split("T")[0]}
              />
            </div>
            <div className="input-group">
              <label htmlFor="endDate">End Date *</label>
              <input
                id="endDate"
                type="date"
                name="endDate"
                value={formData.endDate}
                onChange={handleChange}
                min={minEndDate || new Date().toISOString().split("T")[0]}
                disabled={!formData.startDate}
              />
              {totalDays > 0 && (
                <span className="date-helper">{totalDays} days</span>
              )}
            </div>
          </div>

          <div className="row">
            <div className="input-group">
              <label htmlFor="travelers">👥 Travelers</label>
              <input
                id="travelers"
                type="number"
                name="travelers"
                value={formData.travelers}
                onChange={handleChange}
                min="1"
                max="20"
              />
            </div>
            <div className="input-group">
              <label htmlFor="budget">💰 Daily Budget (USD)</label>
              <input
                id="budget"
                type="number"
                name="budget"
                value={formData.budget}
                onChange={handleChange}
                min="50"
                step="50"
              />
            </div>
          </div>

          {/* Preferences */}
          <div className="section-title">
            <span className="icon">⭐</span>
            <h3>Your Interests (1-10)</h3>
            <p className="section-subtitle">
              Adjust the sliders to match your preferences
            </p>
          </div>

          <div className="preferences-grid">
            {preferenceCategories.map((cat) => (
              <div key={cat.key} className="preference-card">
                <div className="preference-header">
                  <span
                    className="preference-icon"
                    style={{ backgroundColor: cat.color }}
                  >
                    {cat.icon}
                  </span>
                  <span className="preference-label">{cat.label}</span>
                </div>
                <div className="slider-container">
                  <span className="slider-min">1</span>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={formData.preferences[cat.key]}
                    onChange={(e) =>
                      handlePreferenceChange(cat.key, e.target.value)
                    }
                    style={{ accentColor: cat.color }}
                    aria-label={cat.label}
                  />
                  <span className="slider-value">
                    {formData.preferences[cat.key]}
                  </span>
                </div>
                <p className="preference-desc">{cat.description}</p>
              </div>
            ))}
          </div>

          {/* Buttons */}
          <div className="button-group">
            <button
              type="submit"
              className="generate-btn"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <span className="spinner-small"></span>
                  Generating...
                </>
              ) : (
                "✨ Generate Itinerary"
              )}
            </button>
            <button type="button" className="clear-btn" onClick={handleClear}>
              🗑️ Clear
            </button>
          </div>
        </form>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="loading-section">
          <div className="spinner"></div>
          <h3>Creating your personalized itinerary...</h3>
          <p>Analyzing weather, attractions, and your preferences</p>
          <div className="loading-steps">
            <span>🌤️ Checking weather...</span>
            <span>🗺️ Finding attractions...</span>
            <span>📅 Planning your days...</span>
          </div>
        </div>
      )}

      {/* Results */}
      {generatedItinerary && !isLoading && showResult && (
        <div className="results-section">
          {/* Header */}
          <div className="itinerary-header">
            <div className="header-left">
              <h2>🗺️ {formData.destination} Itinerary</h2>
              <p>
                {new Date(formData.startDate).toLocaleDateString("en-US", {
                  month: "long",
                  day: "numeric",
                  year: "numeric",
                })}{" "}
                —{" "}
                {new Date(formData.endDate).toLocaleDateString("en-US", {
                  month: "long",
                  day: "numeric",
                  year: "numeric",
                })}
              </p>
            </div>
            <div className="header-stats">
              <span className="stat-badge">📅 {totalDays || "?"} days</span>
              <span className="stat-badge">👥 {formData.travelers}</span>
              <span className="stat-badge">💰 ${formData.budget}/day</span>
            </div>
          </div>

          {/* Day Cards */}
          <div className="itinerary-days">
            {generatedItinerary.map((day, idx) => (
              <div key={idx} className="day-card">
                <div className="day-header">
                  <div className="day-title">
                    <span className="day-number">Day {day.day}</span>
                    {day.date && (
                      <span className="day-date">
                        {new Date(day.date).toLocaleDateString("en-US", {
                          weekday: "short",
                          month: "short",
                          day: "numeric",
                        })}
                      </span>
                    )}
                  </div>
                  {day.weather && (
                    <div className="weather-badge">
                      {day.weather.condition === "Rainy" ? "🌧️" : "☀️"}{" "}
                      {day.weather.tempMax}°C
                    </div>
                  )}
                </div>

                <div className="activities-list">
                  {day.activities?.map((activity, actIdx) => (
                    <div key={actIdx} className="activity-item">
                      <div className="activity-time">
                        <span>{activity.time || "Flexible"}</span>
                      </div>
                      <div className="activity-details">
                        <h4>{activity.title}</h4>
                        <p>{activity.description}</p>
                        {activity.cost && activity.cost > 0 && (
                          <span className="activity-cost">💰 ${activity.cost}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="day-footer">
                  <span className="day-total">
                    Total: $
                    {day.activities?.reduce(
                      (sum, a) => sum + (a.cost || 0),
                      0,
                    )}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Packing List */}
          {packingList && (
            <div className="packing-section-wrapper">
              <PackingList packingData={packingList} />
            </div>
          )}

          {/* Weather Summary */}
          {weatherSummary && (
            <div className="weather-summary">
              <h4>🌡️ Weather Overview</h4>
              <div className="weather-stats">
                <span>
                  🌧️ Rain expected: {weatherSummary.hasRain ? "Yes" : "No"}
                </span>
                <span>🔥 Max: {weatherSummary.maxTemp}°C</span>
                <span>❄️ Min: {weatherSummary.minTemp}°C</span>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="result-actions">
            <button className="save-btn" onClick={handleSave}>
              💾 Save Itinerary
            </button>
            <button className="print-btn" onClick={() => window.print()}>
              🖨️ Print
            </button>
            <button className="share-btn" onClick={handleClear}>
              📝 New Trip
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Generate;