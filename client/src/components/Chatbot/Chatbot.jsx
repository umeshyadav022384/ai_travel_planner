import React, { useState, useEffect, useRef } from "react";
import "./Chatbot.scss";

const Chatbot = () => {
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hi! I'm Travel Nepal. How can I help you explore the beautiful Himalayas today?"
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const chatWindowRef = useRef(null);
  const inputRef = useRef(null);

  // Auto scroll to bottom
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages, loading, isTyping]);

  // Focus input on load
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setIsTyping(true);

    try {
      const response = await fetch("http://127.0.0.1:5000/api/ml/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input })
      });

      const data = await response.json();

      // Simulate typing delay for natural feel
      setTimeout(() => {
        const botMessage = { sender: "bot", text: data.reply };
        setMessages((prev) => [...prev, botMessage]);
        setIsTyping(false);
      }, 300 + Math.random() * 400);

    } catch (error) {
      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          {
            sender: "bot",
            text: "Oops! I couldn't reach the server. Please check your connection."
          }
        ]);
        setIsTyping(false);
      }, 500);
    }

    setLoading(false);
    setInput("");
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Format message with proper line breaks and markdown-like styling
  const formatMessage = (text) => {
    if (!text) return null;

    const lines = text.split('\n');

    return lines.map((line, index) => {
      if (line.trim() === '') {
        return <br key={index} />;
      }

      // Check for headers (lines with === or ---)
      if (line.includes('===') || line.includes('---')) {
        return <div key={index} className="divider">{line}</div>;
      }

      // Check for numbered items (1., 2., etc.)
      if (/^\d+\./.test(line.trim())) {
        return <div key={index} className="numbered-item">{line}</div>;
      }

      // Check for bullet items (- or •) - FIXED ESLINT WARNING
      if (/^[•-]\s/.test(line.trim())) {
        return <div key={index} className="bullet-item">{line}</div>;
      }

      // Check for lines with colon (key: value)
      if (/^[A-Za-z\s]+:/.test(line.trim())) {
        return <div key={index} className="key-value">{line}</div>;
      }

      // Regular line
      return <div key={index} className="message-line">{line}</div>;
    });
  };

  // Get current time greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning!";
    if (hour < 17) return "Good afternoon!";
    return "Good evening!";
  };

  return (
    <div className="chatbot-wrapper">
      <div className="chatbot-container">
        {/* Header */}
        <div className="chat-header">
          <div className="header-content">
            <div className="header-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <div className="header-text">
              <h1>TravelPal Nepal</h1>
              <p>{getGreeting()} Ready to explore?</p>
            </div>
            <div className="header-status">
              <span className="status-dot"></span>
              <span className="status-text">Online</span>
            </div>
          </div>
          <div className="header-badge">AI Travel Assistant</div>
        </div>

        {/* Chat Window */}
        <div className="chat-window" ref={chatWindowRef}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`message-group ${msg.sender}`}
              style={{ animationDelay: `${idx * 0.05}s` }}
            >
              <div className={`avatar ${msg.sender}`}>
                {msg.sender === "user" ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5z" />
                    <path d="M2 17l10 5 10-5" />
                    <path d="M2 12l10 5 10-5" />
                  </svg>
                )}
              </div>
              <div className={`bubble-wrapper ${msg.sender}`}>
                <div className="sender-name">
                  {msg.sender === "user" ? "You" : "TravelPal"}
                </div>
                <div className="bubble">
                  <div className="message-content">
                    {formatMessage(msg.text)}
                  </div>
                </div>
                <div className="message-time">
                  {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="message-group bot typing-group">
              <div className="avatar bot">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
              </div>
              <div className="bubble-wrapper bot">
                <div className="sender-name">TravelPal</div>
                <div className="bubble typing-bubble">
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Quick Suggestions */}
        <div className="quick-suggestions">
          <button onClick={() => setInput("top attraction in kathmandu")}>
            Top Attractions
          </button>
          <button onClick={() => setInput("best hotel in pokhara")}>
            Best Hotels
          </button>
          <button onClick={() => setInput("weather in lumbini")}>
            Weather
          </button>
          <button onClick={() => setInput("tell me about nepal")}>
            About Nepal
          </button>
        </div>

        {/* Input Area */}
        <div className="chat-input-area">
          <div className="input-wrapper">
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask me anything about Nepal..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              className={!input.trim() || loading ? 'disabled' : ''}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;