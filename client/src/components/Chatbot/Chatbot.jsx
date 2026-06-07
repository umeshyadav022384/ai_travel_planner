import React, { useState } from 'react';
import axios from 'axios';
import './Chatbot.scss';

const Chatbot = () => {
  // The initial message is now in the info panel, so we start with an empty array
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { from: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

 //   try {
   //   const response = await axios.post('https://trip-planner-major.onrender.com/chat', {
     //   message: input,
     // });

     // const botMessage = { from: 'bot', text: response.data.reply };
      //setMessages(prev => [...prev, botMessage]);
    //} catch (error) {
      //console.error("Error communicating with the chatbot API:", error);
      //const errorMessage = { from: 'bot', text: 'Sorry, I am having trouble connecting.' };
      //setMessages(prev => [...prev, errorMessage]);
    //}
  };

  return (
    // This new container holds both the chatbot and the info panel
    <div className="chatbot-page-container">
      
      {/* --- Left Column: The Chatbot --- */}
      <div className="chatbot-container">
        <div className="chatbot-header">
          <h2>AI Travel Assistant</h2>
        </div>
        <div className="chatbot-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`message-wrapper ${msg.from}`}>
              <div className="message-content">
                {msg.text}
              </div>
            </div>
          ))}
        </div>
        <form className="chatbot-input-form" onSubmit={sendMessage}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
          />
          <button type="submit">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
              <path fill="currentColor" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path>
            </svg>
          </button>
        </form>
      </div>

      {/* --- Right Column: The Info Panel --- */}
      <div className="info-panel">
        <h3>Welcome!</h3>
        <p>I'm your personal AI travel assistant. I can help you plan your next adventure.</p>
        <p>Try asking me things like:</p>
        <ul>
          <li>"Tell me about Paris"</li>
          <li>"Suggest a hotel in London"</li>
          <li>"What are the top attractions in Tokyo?"</li>
        </ul>
      </div>

    </div>
  );
};

export default Chatbot;