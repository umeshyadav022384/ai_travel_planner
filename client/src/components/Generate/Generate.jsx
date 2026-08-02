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

  const {
    isLoading,
    generatedItinerary,
    enhancedItinerary,
    packingList,
    weatherSummary,
    geminiUsed,
    dailyCosts,
    totalCost,
    budget,
    dailyBudget,
    weatherForecast,
  } = useSelector((state) => state.itinerary);

  // -------- State --------
  const [useGemini, setUseGemini] = useState(true);
  const [budgetType, setBudgetType] = useState("per_day");
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

  // -------- Effects --------
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

  // -------- Handlers --------
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

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation
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
      toast.error("💰 Minimum budget is $50");
      return;
    }

    dispatch(clearGeneratedItinerary());
    setShowResult(false);

    try {
      const result = await dispatch(
        generateItinerary({
          ...formData,
          useGemini: useGemini,
          budget_type: budgetType,
          days: totalDays,
        })
      );

      if (generateItinerary.fulfilled.match(result)) {
        setShowResult(true);
        const payload = result.payload;

        if (payload.enhanced) {
          toast.success("✨ Itinerary enhanced with gemini ");
        } else if (useGemini) {
          toast.info("⚡ Gemini enhancement not available. Showing technical itinerary.");
        } else {
          toast.success("✅ Itinerary generated successfully!");
        }
      } else if (result.payload?.errorType === "DESTINATION_NOT_SUPPORTED") {
        const { message, suggestion, availableCities } = result.payload;
        toast.error(
          <div>
            <strong>{message}</strong>
            <p style={{ fontSize: "13px", marginTop: "8px" }}>{suggestion}</p>
            <details style={{ fontSize: "12px", marginTop: "4px" }}>
              <summary>📍 Show all supported destinations</summary>
              <p style={{ marginTop: "4px", color: "#555" }}>
                {availableCities?.join(", ") || "Nepal destinations only"}
              </p>
            </details>
          </div>,
          { autoClose: false }
        );
      } else {
        toast.error(result.payload?.message || "❌ Failed to generate itinerary");
      }
    } catch (error) {
      toast.error("Something went wrong. Please try again.");
      console.error("Generate error:", error);
    }
  };

  const handleSave = async () => {
    const itineraryData = {
      destination: formData.destination,
      startDate: formData.startDate,
      endDate: formData.endDate,
      travelers: formData.travelers,
      budget: formData.budget,
      budgetType: budgetType,
      preferences: formData.preferences,
      dailyActivities: generatedItinerary,
      enhanced: enhancedItinerary,
      totalCost: totalCost,
      dailyCosts: dailyCosts,
    };

    const result = await dispatch(saveItinerary(itineraryData));

    if (saveItinerary.fulfilled.match(result)) {
      toast.success("💾 Itinerary saved successfully!");
    } else {
      toast.error(result.payload || "❌ Failed to save itinerary");
    }
  };

  // -------- Preference Categories --------
  // Colors tuned to match the app's Himalayan-dusk palette
  // (rhododendron red, aged wood, forest green, marigold, lake teal).
  const preferenceCategories = [
    {
      key: "art",
      label: "Art & Museums",
      icon: "🎨",
      color: "#bd4438",
      description: "Galleries, exhibitions, street art",
    },
    {
      key: "history",
      label: "History & Heritage",
      icon: "🏛️",
      color: "#8a6642",
      description: "Monuments, temples, ancient sites",
    },
    {
      key: "nature",
      label: "Nature & Outdoors",
      icon: "🌿",
      color: "#3c8a5b",
      description: "Parks, hiking, wildlife",
    },
    {
      key: "food",
      label: "Food & Cuisine",
      icon: "🍜",
      color: "#e0952f",
      description: "Local dishes, restaurants, food tours",
    },
    {
      key: "adventure",
      label: "Adventure & Sports",
      icon: "⚡",
      color: "#2d6b6e",
      description: "Trekking, rafting, activities",
    },
  ];

  // -------- Render Functions --------
  const renderGeminiContent = () => {
    if (!enhancedItinerary) return null;

    return (
      <div className="gemini-enhanced-content">
        {enhancedItinerary.introduction && (
          <div className="gemini-introduction">
            <p>{enhancedItinerary.introduction}</p>
          </div>
        )}

        {enhancedItinerary.daily_itineraries?.map((day, idx) => (
          <div key={idx} className="day-card enhanced-day">
            <div className="day-header">
              <div className="day-title">
                <span className="day-number">Day {day.day}</span>
                <span className="day-title-text">{day.title}</span>
              </div>
              {day.day_total_cost !== undefined && day.day_total_cost > 0 && (
                <div className="day-cost-badge">💰 ${day.day_total_cost}</div>
              )}
            </div>

            {weatherForecast && weatherForecast[idx] && (
              <div className="day-weather">
                <span>🌡️ {Math.round(weatherForecast[idx].temp)}°C</span>
                <span>☀️ {weatherForecast[idx].condition}</span>
                <span>🌧️ {weatherForecast[idx].rain}% rain</span>
                <span>💨 {weatherForecast[idx].wind} km/h</span>
              </div>
            )}

            <div className="activities-list">
              {day.enhanced_activities?.map((activity, actIdx) => (
                <div key={actIdx} className="activity-item">
                  <div className="activity-time">
                    <span>{activity.time || "Flexible"}</span>
                  </div>
                  <div className="activity-details">
                    <h4>{activity.title}</h4>
                    <p className="activity-description">{activity.description}</p>
                    <div className="activity-meta">
                      {activity.food_tip && (
                        <span className="activity-food-tip">🍽️ {activity.food_tip}</span>
                      )}
                      {activity.cost !== undefined && activity.cost > 0 && (
                        <span className="activity-cost">💰 ${activity.cost}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {day.day_summary && (
              <div className="day-summary">
                <strong>📝 Day Summary:</strong> {day.day_summary}
              </div>
            )}
          </div>
        ))}

        {enhancedItinerary.final_tips && (
          <div className="gemini-final-tips">
            <h4>💡 Final Tips</h4>
            <p>{enhancedItinerary.final_tips}</p>
          </div>
        )}
      </div>
    );
  };

  const renderTechnicalItinerary = () => {
    if (!generatedItinerary) return null;

    return (
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
              {day.day_cost !== undefined && day.day_cost > 0 && (
                <div className="day-cost-badge">💰 ${day.day_cost}</div>
              )}
            </div>

            {weatherForecast && weatherForecast[idx] && (
              <div className="day-weather">
                <span>🌡️ {Math.round(weatherForecast[idx].temp)}°C</span>
                <span>☀️ {weatherForecast[idx].condition}</span>
                <span>🌧️ {weatherForecast[idx].rain}% rain</span>
              </div>
            )}

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
                Total: ${day.activities?.reduce((sum, a) => sum + (a.cost || 0), 0)}
              </span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderCostSummary = () => {
    if (!generatedItinerary || dailyCosts.length === 0) return null;

    const totalBudget = budgetType === "per_day" ? budget * totalDays : budget;

    return (
      <div className="cost-summary">
        <h4>💰 Budget Summary</h4>
        <div className="cost-stats">
          <span>Budget Type: {budgetType === "per_day" ? "Per Day" : "Total"}</span>
          <span>Daily Budget: ${dailyBudget}</span>
          <span>Total Budget: ${totalBudget}</span>
          <span>Total Cost: ${totalCost}</span>
          <span>Remaining: ${totalBudget - totalCost}</span>
        </div>
        <div className="daily-cost-breakdown">
          {dailyCosts.map((cost, idx) => (
            <span key={idx}>Day {idx + 1}: ${cost}</span>
          ))}
        </div>
      </div>
    );
  };

  // -------- Main Render --------
  return (
    <div className="generate-container">
      {/* Form Section */}
      <div className="form-section">
        <div className="form-header">
          <div className="hero-pill">Travel planning, reimagined</div>
          <h1>Plan your trip</h1>
          
        </div>

        <form onSubmit={handleSubmit} className="trip-form" noValidate>
          {/* Trip Essentials */}
          <fieldset className="form-panel">
            <legend>Trip essentials</legend>
            <div className="form-grid">
              <div className="input-group">
                <label htmlFor="destination">
                  Destination <span aria-hidden="true">*</span>
                </label>
                <div className="field-shell">
                  <input
                    id="destination"
                    type="text"
                    name="destination"
                    value={formData.destination}
                    onChange={handleChange}
                    placeholder="e.g., Pokhara, Janakpur, Kathmandu"
                    className="destination-input"
                    aria-required="true"
                  />
                </div>
              </div>

              <div className="input-group">
                <label htmlFor="startDate">
                  Start Date <span aria-hidden="true">*</span>
                </label>
                <div className="field-shell">
                  <input
                    id="startDate"
                    type="date"
                    name="startDate"
                    value={formData.startDate}
                    onChange={handleChange}
                    min={new Date().toISOString().split("T")[0]}
                    aria-required="true"
                  />
                </div>
              </div>

              <div className="input-group">
                <label htmlFor="endDate">
                  End Date <span aria-hidden="true">*</span>
                </label>
                <div className="field-shell">
                  <input
                    id="endDate"
                    type="date"
                    name="endDate"
                    value={formData.endDate}
                    onChange={handleChange}
                    min={minEndDate || new Date().toISOString().split("T")[0]}
                    disabled={!formData.startDate}
                    aria-required="true"
                  />
                </div>
                {totalDays > 0 && (
                  <span className="date-helper">
                    {totalDays} {totalDays === 1 ? "day" : "days"}
                  </span>
                )}
              </div>

              <div className="input-group">
                <label htmlFor="travelers">Travelers</label>
                <div className="field-shell">
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
              </div>

              <div className="input-group">
                <label htmlFor="budgetType">Budget Type</label>
                <div className="field-shell">
                  <select
                    id="budgetType"
                    value={budgetType}
                    onChange={(e) => setBudgetType(e.target.value)}
                    className="budget-type-select"
                  >
                    <option value="per_day">Per Day</option>
                    <option value="total">Total</option>
                  </select>
                </div>
              </div>

              <div className="input-group">
                <label htmlFor="budget">
                  {budgetType === "per_day" ? "Daily Budget (USD)" : "Total Budget (USD)"}
                </label>
                <div className="field-shell">
                  <input
                    id="budget"
                    type="number"
                    name="budget"
                    value={formData.budget}
                    onChange={handleChange}
                    min={budgetType === "per_day" ? 50 : 150}
                    step={budgetType === "per_day" ? 10 : 50}
                  />
                </div>
                {budgetType === "per_day" && totalDays > 0 && (
                  <span className="budget-helper">
                    Estimated trip budget: ${formData.budget * totalDays}
                  </span>
                )}
              </div>
            </div>
          </fieldset>

          {/* AI and Preferences */}
          <fieldset className="form-panel">
            <div className="gemini-toggle-section">
              <div className="gemini-toggle">
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={useGemini}
                    onChange={(e) => setUseGemini(e.target.checked)}
                  />
                  <span className="toggle-slider"></span>
                </label>
                <div className="toggle-label">
                  <span className="toggle-title">Enhance with Gemini AI</span>
                </div>
              </div>
              {useGemini && (
                <div className="gemini-badge">
                  <span>
                    <span aria-hidden="true">🤖</span> Powered by Google Gemini
                  </span>
                </div>
              )}
            </div>

            <div className="section-title">
              <span className="icon" aria-hidden="true">⭐</span>
              <div>
                <h3>Your interests</h3>
                <p className="section-subtitle">
                  Fine-tune the sliders to match your travel mood.
                </p>
              </div>
            </div>

            <div className="preferences-grid">
              {preferenceCategories.map((cat) => (
                <div key={cat.key} className="preference-card" style={{ color: cat.color }}>
                  <div className="preference-header">
                    <span
                      className="preference-icon"
                      style={{ backgroundColor: cat.color }}
                      aria-hidden="true"
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
          </fieldset>

          <div className="button-group">
            <button
              type="submit"
              className="generate-btn"
              disabled={isLoading}
              aria-busy={isLoading}
            >
              {isLoading ? (
                <>
                  <span className="spinner-small" aria-hidden="true"></span>
                  Generating...
                </>
              ) : (
                <>
                  <span aria-hidden="true">✨</span> Generate Itinerary
                </>
              )}
            </button>
            <button type="button" className="clear-btn" onClick={handleClear}>
              <span aria-hidden="true">🗑️</span> Clear
            </button>
          </div>
        </form>
      </div>

      {/* Loading Section */}
      {isLoading && (
        <div className="loading-section" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true"></div>
          <h3>Crafting your personalized itinerary...</h3>
          <p>
            Analyzing weather, attractions, and your preferences to shape the
            best plan.
          </p>
          {useGemini && (
            <p className="gemini-loading">✨ Enhancing with Gemini AI...</p>
          )}
          <div className="loading-skeleton" aria-hidden="true">
            <div className="skeleton-line wide"></div>
            <div className="skeleton-line"></div>
            <div className="skeleton-line short"></div>
          </div>
          <div className="loading-steps">
            <span>🌤️ Checking weather...</span>
            <span>🗺️ Finding attractions...</span>
            <span>📅 Planning your days...</span>
            {useGemini && <span>🤖 Adding natural language...</span>}
          </div>
        </div>
      )}

      {/* Results Section */}
      {generatedItinerary && !isLoading && showResult && (
        <div className="results-section">
          <div className="itinerary-header">
            <div className="header-left">
              <div className="hero-pill">Live itinerary preview</div>
              <h2>
                <span aria-hidden="true">🗺️</span> {formData.destination} itinerary
              </h2>
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
              <span className="stat-badge">
                💰{" "}
                {budgetType === "per_day"
                  ? `$${formData.budget}/day`
                  : `Total $${formData.budget}`}
              </span>
              {dailyBudget > 0 && (
                <span className="stat-badge">💵 Daily: ${dailyBudget}</span>
              )}
              {totalCost > 0 && (
                <span className="stat-badge">💵 Total: ${totalCost}</span>
              )}
              {geminiUsed && enhancedItinerary && (
                <span className="stat-badge gemini-badge">✨ AI Enhanced</span>
              )}
            </div>
          </div>

          {renderCostSummary()}

          {useGemini && enhancedItinerary
            ? renderGeminiContent()
            : renderTechnicalItinerary()}

          {packingList && (
            <div className="packing-section-wrapper">
              <PackingList packingData={packingList} />
            </div>
          )}

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

          {useGemini && enhancedItinerary && (
            <div className="gemini-notice">
              ✨ This itinerary was enhanced with Google Gemini AI
            </div>
          )}

          {useGemini && !enhancedItinerary && generatedItinerary && (
            <div className="gemini-notice warning">
              ⚠️ Gemini enhancement is not available. Showing technical
              itinerary.
            </div>
          )}

          <div className="result-actions">
            <button className="save-btn" onClick={handleSave}>
              <span aria-hidden="true">💾</span> Save Itinerary
            </button>
            <button className="print-btn" onClick={() => window.print()}>
              <span aria-hidden="true">🖨️</span> Print
            </button>
            <button className="share-btn" onClick={handleClear}>
              <span aria-hidden="true">📝</span> New Trip
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Generate;
