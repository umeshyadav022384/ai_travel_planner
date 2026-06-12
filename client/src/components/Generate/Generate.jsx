import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { toast } from "react-toastify";
import { generateItinerary, clearGeneratedItinerary } from "../../features/itinerarySlice";
import PackingList from '../PackingList/PackingList';  // ← IMPORT PackingList
import "./Generate.scss";

const Generate = () => {
  const dispatch = useDispatch();
  const { isLoading, generatedItinerary, packingList, weatherSummary } = useSelector(
    (state) => state.itinerary
  );

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

  // ... (rest of your handlers remain the same)

  const handlePreferenceChange = (category, value) => {
    setFormData({
      ...formData,
      preferences: {
        ...formData.preferences,
        [category]: parseInt(value)
      }
    });
  };

  const preferenceCategories = [
    { key: 'art', label: '🎨 Art', icon: '🖼️', color: '#e91e63', description: 'Museums, galleries, street art' },
    { key: 'history', label: '🏛️ History', icon: '📜', color: '#795548', description: 'Heritage sites, monuments, ancient ruins' },
    { key: 'nature', label: '🌿 Nature', icon: '🌲', color: '#4caf50', description: 'Parks, landscapes, wildlife' },
    { key: 'food', label: '🍜 Food', icon: '🍽️', color: '#ff9800', description: 'Local cuisine, restaurants, food tours' },
    { key: 'adventure', label: '⚡ Adventure', icon: '🏔️', color: '#2196f3', description: 'Trekking, rafting, extreme sports' },
  ];

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.destination) {
      toast.error("Please enter a destination");
      return;
    }
    if (!formData.startDate || !formData.endDate) {
      toast.error("Please select dates");
      return;
    }

    const start = new Date(formData.startDate);
    const end = new Date(formData.endDate);
    const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));

    if (days <= 0) {
      toast.error("End date must be after start date");
      return;
    }

    dispatch(clearGeneratedItinerary());
    const result = await dispatch(generateItinerary(formData));
    
    if (generateItinerary.fulfilled.match(result)) {
      toast.success("✨ Itinerary generated successfully!");
    } else {
      toast.error(result.payload || "Failed to generate itinerary");
    }
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
  };

  return (
    <div className="generate-container">
      <div className="form-section">
        <h1>✈️ Plan Your Perfect Trip</h1>
        <p>Tell us about your travel plans and preferences</p>
        
        <form onSubmit={handleSubmit}>
          {/* Trip Details Section */}
          <div className="section-title">
            <span className="icon">📍</span>
            <h3>Trip Details</h3>
          </div>
          
          <div className="input-group">
            <label>Destination *</label>
            <input
              type="text"
              name="destination"
              value={formData.destination}
              onChange={handleChange}
              placeholder="e.g., Pokhara, Janakpur, Kathmandu"
            />
          </div>

          <div className="row">
            <div className="input-group">
              <label>Start Date *</label>
              <input
                type="date"
                name="startDate"
                value={formData.startDate}
                onChange={handleChange}
              />
            </div>
            <div className="input-group">
              <label>End Date *</label>
              <input
                type="date"
                name="endDate"
                value={formData.endDate}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="row">
            <div className="input-group">
              <label>👥 Number of Travelers</label>
              <input
                type="number"
                name="travelers"
                value={formData.travelers}
                onChange={handleChange}
                min="1"
                max="20"
              />
            </div>
            <div className="input-group">
              <label>💰 Budget (per day in USD)</label>
              <input
                type="number"
                name="budget"
                value={formData.budget}
                onChange={handleChange}
                min="50"
                step="50"
              />
            </div>
          </div>

          {/* Preferences Section */}
          <div className="section-title">
            <span className="icon">⭐</span>
            <h3>Your Interests (1-10 scale)</h3>
          </div>

          <div className="preferences-grid">
            {preferenceCategories.map((cat) => (
              <div key={cat.key} className="preference-card">
                <div className="preference-header">
                  <span className="preference-icon" style={{ backgroundColor: cat.color }}>
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
                    onChange={(e) => handlePreferenceChange(cat.key, e.target.value)}
                    style={{ accentColor: cat.color }}
                  />
                  <span className="slider-value">{formData.preferences[cat.key]}/10</span>
                </div>
                <p className="preference-desc">{cat.description}</p>
              </div>
            ))}
          </div>

          <div className="button-group">
            <button type="submit" className="generate-btn" disabled={isLoading}>
              {isLoading ? "🔄 Generating..." : "✨ Generate Itinerary"}
            </button>
            <button type="button" className="clear-btn" onClick={handleClear}>
              🗑️ Clear Form
            </button>
          </div>
        </form>
      </div>

      {/* Loading Section */}
      {isLoading && (
        <div className="loading-section">
          <div className="spinner"></div>
          <h3>Creating your personalized itinerary...</h3>
          <p>Analyzing weather, attractions, and your preferences</p>
        </div>
      )}

      {/* Results Section - WITH PACKING LIST INTEGRATED */}
      {generatedItinerary && !isLoading && (
        <div className="results-section">
          <div className="itinerary-header">
            <h2>🗺️ Your {formData.destination} Itinerary</h2>
            <p>{formData.startDate} to {formData.endDate}</p>
            <div className="itinerary-stats">
              <span>📅 {Math.ceil((new Date(formData.endDate) - new Date(formData.startDate)) / (1000*60*60*24))} days</span>
              <span>👥 {formData.travelers} travelers</span>
              <span>💰 ${formData.budget}/day</span>
            </div>
          </div>

          {/* Day by Day Itinerary */}
          <div className="itinerary-days">
            {generatedItinerary.map((day, idx) => (
              <div key={idx} className="day-card">
                <div className="day-header">
                  <h3>Day {day.day}</h3>
                  <div className="weather-badge">
                    {day.weather?.condition === 'Rainy' ? '🌧️' : '☀️'} {day.weather?.tempMax}°C
                  </div>
                </div>
                <div className="activities-list">
                  {day.activities?.map((activity, actIdx) => (
                    <div key={actIdx} className="activity-item">
                      <span className="activity-time">{activity.time}</span>
                      <div className="activity-details">
                        <h4>{activity.title}</h4>
                        <p>{activity.description}</p>
                        {activity.cost > 0 && (
                          <span className="activity-cost">💰 ${activity.cost}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="day-total">
                  Total: ${day.activities?.reduce((sum, a) => sum + (a.cost || 0), 0)}
                </div>
              </div>
            ))}
          </div>

          {/* ============================================================ */}
          {/* ✅ PACKING LIST COMPONENT - INTEGRATED HERE ✅ */}
          {/* ============================================================ */}
          {packingList && (
            <PackingList packingData={packingList} />
          )}

          {/* Optional: Weather Summary (if not already in packing list) */}
          {weatherSummary && (
            <div className="weather-summary">
              <h4>🌡️ Weather Summary</h4>
              <div className="weather-stats">
                <span>🌧️ Rain expected: {weatherSummary.hasRain ? 'Yes' : 'No'}</span>
                <span>🔥 Max temperature: {weatherSummary.maxTemp}°C</span>
                <span>❄️ Min temperature: {weatherSummary.minTemp}°C</span>
              </div>
            </div>
          )}

          <button 
            className="save-btn"
            onClick={() => {
              // dispatch(saveItinerary({...}))
              toast.info("Save feature coming soon!");
            }}
          >
            💾 Save This Itinerary
          </button>
        </div>
      )}
    </div>
  );
};

export default Generate;