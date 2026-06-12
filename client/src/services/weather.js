// src/services/weather.js
import axios from 'axios';

const API_KEY = "MYZ8S3QHVUUXBXSWP2DKSL74V"; 

export const getWeather = async (location, startDate, endDate) => {
  try {
    // Visual Crossing API URL
    const url = `https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/${location}/${startDate}/${endDate}?unitGroup=metric&include=days&key=${API_KEY}&contentType=json`;
    
    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    console.error("Weather API Error:", error);
    return null; // Return null if weather fails so the app doesn't crash
  }
};