// client/src/components/PackingList/PackingList.jsx

import React from 'react';
import './PackingList.scss';

const PackingList = ({ packingData }) => {
  if (!packingData) return null;

  return (
    <div className="packing-list-container">
      <h3>🧳 Packing List</h3>
      
      <div className="packing-grid">
        
        {/* Essentials - Display Only */}
        {packingData.essentials && packingData.essentials.length > 0 && (
          <div className="packing-card essentials">
            <div className="packing-icon">✅</div>
            <h4>Essentials</h4>
            <ul>
              {packingData.essentials.map((item, idx) => (
                <li key={idx}>
                  <label>
                    <input type="checkbox" />
                    <span>{item}</span>
                  </label>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Weather Based - Display Only (from rule-based backend) */}
        {packingData.weather_based && packingData.weather_based.length > 0 && (
          <div className="packing-card weather">
            <div className="packing-icon">🌤️</div>
            <h4>Weather Based</h4>
            <ul>
              {packingData.weather_based.map((item, idx) => (
                <li key={idx}>
                  <label>
                    <input type="checkbox" />
                    <span>{item.item || item}</span>
                    {item.reason && <small>({item.reason})</small>}
                  </label>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Recommended - Display Only */}
        {packingData.recommended && packingData.recommended.length > 0 && (
          <div className="packing-card recommended">
            <div className="packing-icon">👍</div>
            <h4>Recommended</h4>
            <ul>
              {packingData.recommended.map((item, idx) => (
                <li key={idx}>
                  <label>
                    <input type="checkbox" />
                    <span>{item}</span>
                  </label>
                </li>
              ))}
            </ul>
          </div>
        )}
        
      </div>
      
      {/* Alerts - Display Only */}
      {packingData.alerts && packingData.alerts.length > 0 && (
        <div className="packing-alerts">
          <h4>⚠️ Important Alerts</h4>
          {packingData.alerts.map((alert, idx) => (
            <div key={idx} className="alert-item">⚠️ {alert}</div>
          ))}
        </div>
      )}
      
      {/* Tips - Display Only */}
      {packingData.tips && packingData.tips.length > 0 && (
        <div className="packing-tips">
          <h4>💡 Travel Tips</h4>
          <ul>
            {packingData.tips.map((tip, idx) => (
              <li key={idx}>{tip}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default PackingList;