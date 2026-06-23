import axios from "axios";

const CHAT_API_URL = "/api/chatbot";

export async function sendChatMessage(message) {
  try {
    const response = await axios.post(CHAT_API_URL, { message });
    return response?.data?.reply || fallbackResponse(message);
  } catch (error) {
    console.warn("Chatbot endpoint unavailable, using fallback response.", error);
    return fallbackResponse(message);
  }
}

function fallbackResponse(message) {
  const normalized = message.trim().toLowerCase();

  if (!normalized) {
    return "What would you like to know about travel planning today?";
  }

  if (/(recommend|destination|where|go|place|think)/i.test(normalized)) {
    return "I’d love to help — tell me the destination or type of trip you’re planning.";
  }

  if (/(hotel|stay|accommodation|sleep)/i.test(normalized)) {
    return "For hotels, let me know your budget and style, and I can suggest a good area to stay.";
  }

  if (/(weather|forecast|temperature|rain)/i.test(normalized)) {
    return "I can give travel weather guidance. Which city and dates are you interested in?";
  }

  if (/(itinerary|plan|schedule|days)/i.test(normalized)) {
    return "Tell me how many days you have and what activities you enjoy, and I’ll suggest a travel plan.";
  }

  return "I’m here to help with travel planning — ask me about destinations, itineraries, weather, packing, or hotels.";
}
