import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./MapComponent.scss";
import { useSelector } from "react-redux";
import { getPlace } from "../../../features/placeSlice";
import axios from "axios";
import L from "leaflet";

// Fix for default marker icon in Leaflet (required)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

// Trueway Geocoding API
const GEOCODE_URL = "https://trueway-geocoding.p.rapidapi.com/Geocode";

const MapComponent = () => {
  const { place } = useSelector(getPlace);
  const [coordinates, setCoordinates] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Get coordinates when place changes
  useEffect(() => {
    if (!place) {
      setCoordinates(null);
      setLoading(false);
      return;
    }

    const fetchCoordinates = async () => {
      setLoading(true);
      setError(null);

      const options = {
        params: { address: place },
        headers: {
          "X-RapidAPI-Key":
            "1d91e57a6dmsh09e6f02d716fb78p166222jsnabc34d782df3",
          "X-RapidAPI-Host": "trueway-geocoding.p.rapidapi.com",
        },
      };

      try {
        const response = await axios.get(GEOCODE_URL, options);
        const data = response.data;

        if (data.results && data.results.length > 0) {
          const lat = data.results[0].location.lat;
          const lng = data.results[0].location.lng;
          setCoordinates([lat, lng]);
        } else {
          setError("Location not found. Try a different destination.");
        }
      } catch (err) {
        console.error("Geocoding error:", err);
        setError("Failed to get map coordinates. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchCoordinates();
  }, [place]);

  // Loading state
  if (loading) {
    return (
      <div className="map-container loading">
        <p>Loading map for {place}...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="map-container error">
        <p>{error}</p>
      </div>
    );
  }

  // No place selected
  if (!place) {
    return (
      <div className="map-container no-place">
        <p>🔍 Search for a destination to see the map</p>
      </div>
    );
  }

  // No coordinates yet
  if (!coordinates) {
    return (
      <div className="map-container loading">
        <p>Getting coordinates for {place}...</p>
      </div>
    );
  }

  // Display the map
  const [lat, lng] = coordinates;

  return (
    <div className="map-container">
      <MapContainer
        center={[lat, lng]}
        zoom={12}
        style={{ height: "100%", width: "100%" }}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png?language=en"
        />
        <Marker position={[lat, lng]}>
          <Popup>
            <strong>{place}</strong>
            <br />
            Latitude: {lat.toFixed(4)}°
            <br />
            Longitude: {lng.toFixed(4)}°
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
};

export default MapComponent;
