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
  const [timeMode, setTimeMode] = useState("per_day");
  const [availableHours, setAvailableHours] = useState(6);
  
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
    setTimeMode("per_day");
    setAvailableHours(6);
    setShowResult(false);
    toast.info("Form cleared");
  };

  // ⭐ GET ACTIVITY DURATION
  const getActivityDuration = (activity) => {
    if (!activity) return 0;
    
    if (activity.is_meal || activity.is_meal === true) {
      return 0.5;
    }
    
    if (activity.is_hotel || (activity.title && activity.title.includes('Stay at'))) {
      return 0;
    }
    
    if (activity.time_hours !== undefined && activity.time_hours !== null) {
      const val = parseFloat(activity.time_hours);
      if (!isNaN(val) && val > 0) {
        return val;
      }
    }
    
    if (activity.duration !== undefined && activity.duration !== null) {
      const val = parseFloat(activity.duration);
      if (!isNaN(val) && val > 0) {
        return val;
      }
    }
    
    return 1;
  };

  // ⭐ CALCULATE DAY TOTAL TIME
  const calculateDayTotalTime = (activities) => {
    if (!activities || !Array.isArray(activities)) return 0;
    
    let total = 0;
    activities.forEach(activity => {
      if (!activity) return;
      if (activity.is_hotel || (activity.title && activity.title.includes('Stay at'))) {
        return;
      }
      total += getActivityDuration(activity);
    });
    
    return total;
  };

  // ⭐ FORMAT TIME DISPLAY
  const formatTimeDisplay = (hours) => {
    if (!hours || hours === 0) return "0h";
    
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    
    if (h === 0) return `${m}m`;
    if (m === 0) return `${h}h`;
    return `${h}h ${m}m`;
  };

  // ⭐ Get time summary display
  const getTimeDisplay = () => {
    if (timeMode === "per_day" && totalDays > 0) {
      return {
        perDay: availableHours,
        total: availableHours * totalDays,
        description: `${availableHours} hours per day`,
        summary: `${availableHours} hours per day × ${totalDays} days = ${availableHours * totalDays} hours total`
      };
    } else if (timeMode === "total" && totalDays > 0) {
      const perDay = (availableHours / totalDays).toFixed(1);
      return {
        perDay: perDay,
        total: availableHours,
        description: `${availableHours} hours total`,
        summary: `${availableHours} hours total ÷ ${totalDays} days = ${perDay} hours per day`
      };
    } else if (timeMode === "no_limit") {
      return {
        perDay: "Full day",
        total: "No limit",
        description: "No time limit",
        summary: "No time limit — Full day itinerary"
      };
    }
    return {
      perDay: 0,
      total: 0,
      description: "",
      summary: ""
    };
  };

  const getHoursPerDay = () => {
    if (timeMode === "per_day") {
      return availableHours;
    } else if (timeMode === "total" && totalDays > 0) {
      return (availableHours / totalDays).toFixed(1);
    } else if (timeMode === "no_limit") {
      return "Full day";
    }
    return 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

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

    if (timeMode !== "no_limit") {
      if (timeMode === "per_day" && availableHours < 1) {
        toast.error("⏰ Please enter at least 1 hour per day");
        return;
      }
      if (timeMode === "total" && availableHours < 1) {
        toast.error("⏰ Please enter at least 1 hour total");
        return;
      }
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
          time_mode: timeMode,
          available_hours: availableHours,
        })
      );

      if (generateItinerary.fulfilled.match(result)) {
        setShowResult(true);
        const payload = result.payload;

        // ⭐ DEBUG: Log skipped attractions
        console.log("📦 PAYLOAD:", payload);
        if (payload.dailyActivities) {
          payload.dailyActivities.forEach((day, idx) => {
            console.log(`Day ${idx + 1} skipped:`, day.skipped_attractions || []);
          });
        }

        if (payload.enhanced) {
          toast.success("✨ Itinerary enhanced with Gemini ");
        } else if (useGemini) {
          toast.info("⚡ Gemini enhancement not available. Showing technical itinerary.");
        } else {
          toast.success("✅ Itinerary generated successfully!");
        }
        
        if (timeMode !== "no_limit") {
          const timeInfo = getTimeDisplay();
          toast.info(`⏰ Time limit: ${timeInfo.description}`);
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
    const timeDisplay = getTimeDisplay();
    
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
      timeMode: timeMode,
      availableHours: availableHours,
      timeDisplay: timeDisplay,
    };

    const result = await dispatch(saveItinerary(itineraryData));

    if (saveItinerary.fulfilled.match(result)) {
      toast.success("💾 Itinerary saved successfully!");
    } else {
      toast.error(result.payload || "❌ Failed to save itinerary");
    }
  };

  // -------- Preference Categories --------
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

  // ⭐ RENDER ACTIVITY ITEMS
  const renderActivityItem = (activity) => {
    if (!activity) return null;
    
    let duration = 0;
    if (activity.is_meal || activity.is_meal === true) {
      duration = 0.5;
    } else if (activity.time_hours !== undefined && activity.time_hours !== null) {
      duration = parseFloat(activity.time_hours);
    } else if (activity.duration !== undefined && activity.duration !== null) {
      duration = parseFloat(activity.duration);
    } else {
      duration = 1;
    }
    
    const isHotel = activity.is_hotel || (activity.title && activity.title.includes('Stay at'));
    const showDuration = !isHotel && duration > 0;
    
    return (
      <div className="activity-item">
        <div className="activity-time">
          <span>{activity.time || "Flexible"}</span>
        </div>
        <div className="activity-details">
          <h4>
            {activity.title}
            {showDuration && (
              <span className="duration-badge">⏱️ {formatTimeDisplay(duration)}</span>
            )}
          </h4>
          <p>{activity.description}</p>
          <div className="activity-meta">
            {activity.cost && activity.cost > 0 && (
              <span className="activity-cost">💰 ${activity.cost}</span>
            )}
            {activity.food_tip && (
              <span className="activity-food-tip">🍽️ {activity.food_tip}</span>
            )}
          </div>
        </div>
      </div>
    );
  };

  // ⭐ RENDER SKIPPED ATTRACTIONS
  const renderSkippedAttractions = (skippedAttractions) => {
    if (!skippedAttractions || skippedAttractions.length === 0) {
      return null;
    }
    
    return (
      <div className="skipped-notice">
        ⚠️ {skippedAttractions.length} attraction(s) skipped due to time limit.
        <div className="skipped-items">
          {skippedAttractions.map((item, i) => (
            <span key={i} className="skipped-item">
              {item.name || 'Unknown'} ({formatTimeDisplay(item.time_hours || 0)})
            </span>
          ))}
        </div>
      </div>
    );
  };

  // ⭐ RENDER DAY CARD
  const renderDayCard = (day, idx, isEnhanced = false) => {
    if (!day) return null;
    
    // ⭐ DEBUG: Log the day object to see what's in it
    console.log(`📊 Day ${idx + 1} data:`, day);
    console.log(`📊 Day ${idx + 1} skippedAttractions:`, day.skipped_attractions);
    
    // Get activities
    let activities = day.activities || day.enhanced_activities || [];
    
    // If still empty, try to find any array in the day object
    if (activities.length === 0) {
      for (const key in day) {
        if (Array.isArray(day[key]) && day[key].length > 0) {
          if (day[key][0]?.title || day[key][0]?.name) {
            activities = day[key];
            break;
          }
        }
      }
    }
    
    // Calculate total time
    const dayTotalTime = calculateDayTotalTime(activities);
    const dayCost = day.day_cost || day.day_total_cost || 0;
    
    // ⭐ Get skipped attractions - try multiple possible field names
    const skippedAttractions = day.skipped_attractions || day.skipped || [];
    
    // ⭐ DEBUG: Log what we found
    console.log(`✅ Day ${idx + 1} - Skipped found:`, skippedAttractions.length);
    
    return (
      <div key={idx} className="day-card">
        <div className="day-header">
          <div className="day-title">
            <span className="day-number">Day {day.day || idx + 1}</span>
            {day.title && (
              <span className="day-title-text">{day.title}</span>
            )}
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
          <div className="day-badges">
            {dayCost > 0 && (
              <span className="day-cost-badge">💰 ${dayCost}</span>
            )}
            {timeMode !== "no_limit" && (
              <span className="day-time-badge">⏱️ {formatTimeDisplay(dayTotalTime)}</span>
            )}
          </div>
        </div>

        {timeMode !== "no_limit" && (
          <div className="day-time-info">
            ⏰ {timeMode === "per_day" 
              ? `${availableHours} hours available today` 
              : `${getHoursPerDay()} hours available today`}
            <span className="time-used">
              (Used: {formatTimeDisplay(dayTotalTime)})
            </span>
          </div>
        )}

        {weatherForecast && weatherForecast[idx] && (
          <div className="day-weather">
            <span>🌡️ {Math.round(weatherForecast[idx].temp)}°C</span>
            <span>☀️ {weatherForecast[idx].condition}</span>
            <span>🌧️ {weatherForecast[idx].rain}% rain</span>
            {weatherForecast[idx].wind && (
              <span>💨 {weatherForecast[idx].wind} km/h</span>
            )}
          </div>
        )}

        <div className="activities-list">
          {activities.map((activity, actIdx) => (
            <div key={actIdx}>
              {renderActivityItem(activity)}
            </div>
          ))}
        </div>

        <div className="day-footer">
          <span className="day-total">
            Total: ${activities.reduce((sum, a) => sum + (a.cost || 0), 0)}
          </span>
          <span className="day-time-total">
            ⏱️ Total: {formatTimeDisplay(dayTotalTime)}
          </span>
        </div>
        
        {/* ⭐ SKIPPED ATTRACTIONS - Render them here! */}
        {renderSkippedAttractions(skippedAttractions)}
        
        {day.day_summary && (
          <div className="day-summary">
            <strong>📝 Day Summary:</strong> {day.day_summary}
          </div>
        )}
      </div>
    );
  };

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
          renderDayCard(day, idx, true)
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
          renderDayCard(day, idx, false)
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
      <div className="form-section">
        <div className="form-header">
          <div className="hero-pill">Travel planning, reimagined</div>
          <h1>Plan your trip</h1>
        </div>

        <form onSubmit={handleSubmit} className="trip-form" noValidate>
          {/* ... rest of the form (same as before) ... */}
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
                    aria-required="true"
                  />
                </div>
              </div>

              <div className="input-group">
                <label htmlFor="startDate">Start Date <span aria-hidden="true">*</span></label>
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
                <label htmlFor="endDate">End Date <span aria-hidden="true">*</span></label>
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

          {/* Time Panel */}
          <fieldset className="form-panel time-panel">
            <legend>⏰ Time Availability</legend>
            <div className="time-section">
              <div className="time-options">
                <label className={`time-option ${timeMode === 'per_day' ? 'active' : ''}`}>
                  <input
                    type="radio"
                    name="time_mode"
                    value="per_day"
                    checked={timeMode === 'per_day'}
                    onChange={() => setTimeMode('per_day')}
                  />
                  <span className="option-text">
                    I have 
                    <input
                      type="number"
                      className="hour-input"
                      value={availableHours}
                      min="1"
                      max="24"
                      onChange={(e) => setAvailableHours(Number(e.target.value))}
                      disabled={timeMode !== 'per_day'}
                    />
                    hours <strong>PER DAY</strong>
                  </span>
                  <span className="hint">
                    {totalDays > 0 
                      ? `(Total: ${availableHours * totalDays} hours for ${totalDays} days)`
                      : '(Select dates to see total)'}
                  </span>
                </label>

                <label className={`time-option ${timeMode === 'total' ? 'active' : ''}`}>
                  <input
                    type="radio"
                    name="time_mode"
                    value="total"
                    checked={timeMode === 'total'}
                    onChange={() => setTimeMode('total')}
                  />
                  <span className="option-text">
                    I have 
                    <input
                      type="number"
                      className="hour-input"
                      value={availableHours}
                      min="1"
                      max="72"
                      onChange={(e) => setAvailableHours(Number(e.target.value))}
                      disabled={timeMode !== 'total'}
                    />
                    hours <strong>TOTAL</strong>
                  </span>
                  <span className="hint">
                    {totalDays > 0 
                      ? `(${(availableHours / totalDays).toFixed(1)} hours per day)`
                      : '(Select dates to see per-day split)'}
                  </span>
                </label>

                <label className={`time-option ${timeMode === 'no_limit' ? 'active' : ''}`}>
                  <input
                    type="radio"
                    name="time_mode"
                    value="no_limit"
                    checked={timeMode === 'no_limit'}
                    onChange={() => setTimeMode('no_limit')}
                  />
                  <span className="option-text">
                    <strong>No time limit</strong> — Full day
                  </span>
                </label>
              </div>

              {timeMode !== 'no_limit' && totalDays > 0 && (
                <div className="time-summary">
                  📊 {getTimeDisplay().summary}
                </div>
              )}
            </div>
          </fieldset>

          {/* Gemini and Preferences */}
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
                  <span><span aria-hidden="true">🤖</span> Powered by Google Gemini</span>
                </div>
              )}
            </div>

            <div className="section-title">
              <span className="icon" aria-hidden="true">⭐</span>
              <div>
                <h3>Your interests</h3>
                <p className="section-subtitle">Fine-tune the sliders to match your travel mood.</p>
              </div>
            </div>

            <div className="preferences-grid">
              {preferenceCategories.map((cat) => (
                <div key={cat.key} className="preference-card" style={{ color: cat.color }}>
                  <div className="preference-header">
                    <span className="preference-icon" style={{ backgroundColor: cat.color }} aria-hidden="true">
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
                      aria-label={cat.label}
                    />
                    <span className="slider-value">{formData.preferences[cat.key]}</span>
                  </div>
                  <p className="preference-desc">{cat.description}</p>
                </div>
              ))}
            </div>
          </fieldset>

          <div className="button-group">
            <button type="submit" className="generate-btn" disabled={isLoading} aria-busy={isLoading}>
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

      {isLoading && (
        <div className="loading-section" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true"></div>
          <h3>Crafting your personalized itinerary...</h3>
          <p>Analyzing weather, attractions, and your preferences to shape the best plan.</p>
          {timeMode !== "no_limit" && (
            <p className="time-loading">
              ⏰ With {timeMode === "per_day" 
                ? `${availableHours} hours per day` 
                : `${availableHours} hours total`} time limit
            </p>
          )}
          {useGemini && <p className="gemini-loading">✨ Enhancing with Gemini AI...</p>}
          <div className="loading-skeleton" aria-hidden="true">
            <div className="skeleton-line wide"></div>
            <div className="skeleton-line"></div>
            <div className="skeleton-line short"></div>
          </div>
          <div className="loading-steps">
            <span>🌤️ Checking weather...</span>
            <span>🗺️ Finding attractions...</span>
            <span>📅 Planning your days...</span>
            {timeMode !== "no_limit" && <span>⏰ Applying time constraints...</span>}
            {useGemini && <span>🤖 Adding natural language...</span>}
          </div>
        </div>
      )}

      {generatedItinerary && !isLoading && showResult && (
        <div className="results-section">
          <div className="itinerary-header">
            <div className="header-left">
              <div className="hero-pill">Live itinerary preview</div>
              <h2><span aria-hidden="true">🗺️</span> {formData.destination} itinerary</h2>
              <p>
                {new Date(formData.startDate).toLocaleDateString("en-US", {
                  month: "long",
                  day: "numeric",
                  year: "numeric",
                })} —{" "}
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
                💰 {budgetType === "per_day" ? `$${formData.budget}/day` : `Total $${formData.budget}`}
              </span>
              {dailyBudget > 0 && <span className="stat-badge">💵 Daily: ${dailyBudget}</span>}
              {totalCost > 0 && <span className="stat-badge">💵 Total: ${totalCost}</span>}
              {geminiUsed && enhancedItinerary && <span className="stat-badge gemini-badge">✨ AI Enhanced</span>}
              {timeMode !== "no_limit" && (
                <span className="stat-badge time-badge">
                  ⏰ {timeMode === "per_day" ? `${availableHours}h/day` : `${availableHours}h total`}
                </span>
              )}
            </div>
          </div>

          {renderCostSummary()}

          {useGemini && enhancedItinerary ? renderGeminiContent() : renderTechnicalItinerary()}

          {packingList && (
            <div className="packing-section-wrapper">
              <PackingList packingData={packingList} />
            </div>
          )}

          {weatherSummary && (
            <div className="weather-summary">
              <h4>🌡️ Weather Overview</h4>
              <div className="weather-stats">
                <span>🌧️ Rain expected: {weatherSummary.hasRain ? "Yes" : "No"}</span>
                <span>🔥 Max: {weatherSummary.maxTemp}°C</span>
                <span>❄️ Min: {weatherSummary.minTemp}°C</span>
              </div>
            </div>
          )}

          {useGemini && enhancedItinerary && (
            <div className="gemini-notice">✨ This itinerary was enhanced with Google Gemini AI</div>
          )}

          {useGemini && !enhancedItinerary && generatedItinerary && (
            <div className="gemini-notice warning">⚠️ Gemini enhancement is not available. Showing technical itinerary.</div>
          )}

          <div className="result-actions">
            <button className="save-btn" onClick={handleSave}><span aria-hidden="true">💾</span> Save Itinerary</button>
            <button className="print-btn" onClick={() => window.print()}><span aria-hidden="true">🖨️</span> Print</button>
            <button className="share-btn" onClick={handleClear}><span aria-hidden="true">📝</span> New Trip</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Generate;