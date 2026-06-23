const axios = require("axios");

async function chatReply(req, res) {
  const { message } = req.body;

  if (!message || typeof message !== "string") {
    return res.status(400).json({ error: "Message is required." });
  }

  try {
    if (process.env.OPENAI_API_KEY) {
      const apiResponse = await axios.post(
        "https://api.openai.com/v1/chat/completions",
        {
          model: "gpt-3.5-turbo",
          messages: [
            {
              role: "system",
              content: "You are a helpful travel planning assistant."
            },
            {
              role: "user",
              content: message
            }
          ],
          max_tokens: 250,
          temperature: 0.8
        },
        {
          headers: {
            Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
            "Content-Type": "application/json"
          }
        }
      );

      const reply = apiResponse?.data?.choices?.[0]?.message?.content?.trim();
      return res.json({ reply: reply || getFallbackReply(message) });
    }

    return res.json({ reply: getFallbackReply(message) });
  } catch (error) {
    console.error("Chatbot error:", error?.response?.data || error.message || error);
    return res.json({ reply: getFallbackReply(message) });
  }
}

function getFallbackReply(message) {
  const normalized = message.trim().toLowerCase();

  if (!normalized) {
    return "What travel question can I help with today?";
  }

  if (/(recommend|destination|where|go|place|think)/i.test(normalized)) {
    return "Tell me the destination or type of trip you want, and I’ll suggest something great.";
  }

  if (/(hotel|stay|accommodation|sleep)/i.test(normalized)) {
    return "I can help with hotel suggestions if you share your location, budget, and travel style.";
  }

  if (/(weather|forecast|temperature|rain)/i.test(normalized)) {
    return "Let me know the city and travel dates so I can help with weather guidance.";
  }

  if (/(itinerary|plan|schedule|days)/i.test(normalized)) {
    return "How many days will you travel, and what kinds of activities do you enjoy?";
  }

  return "I’m ready to help with travel planning — ask me about destinations, itineraries, weather, packing, or hotels.";
}

module.exports = { chatReply };
