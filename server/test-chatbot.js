const axios = require("axios");

const url = "http://localhost:5000/api/chatbot";
const payload = {
  message: "What should I pack for a 5-day trip to Kathmandu in April?"
};

(async () => {
  try {
    console.log("Sending test message to", url);
    const response = await axios.post(url, payload, {
      headers: { "Content-Type": "application/json" }
    });

    console.log("Response status:", response.status);
    console.log("Reply:", response.data.reply);
  } catch (error) {
    if (error.response) {
      console.error("Server responded with status", error.response.status);
      console.error(error.response.data);
    } else {
      console.error("Request failed:", error.message);
    }
    process.exit(1);
  }
})();
