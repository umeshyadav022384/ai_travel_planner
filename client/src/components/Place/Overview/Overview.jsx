import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { addPlace, getPlace } from "../../../features/placeSlice";
import "./Overview.scss";

const Overview = () => {
  const [location, setLocation] = useState("");
  const dispatch = useDispatch();
  const { place } = useSelector(getPlace);
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    if (location.trim()) {
      dispatch(addPlace(location));
      setLocation("");
    }
  };

  // Fetch Wikipedia 
  useEffect(() => {
    if (!place) return;

    const fetchWikipediaInfo = async () => {
      setLoading(true);
      try {
        // Free Wikipedia APi
        const searchUrl = `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(place)}&format=json&origin=*`;
        const searchResponse = await fetch(searchUrl);
        const searchData = await searchResponse.json();

        if (searchData.query.search.length > 0) {
          const pageId = searchData.query.search[0].pageid;
          
          // Get page content
          const contentUrl = `https://en.wikipedia.org/w/api.php?action=query&pageids=${pageId}&prop=extracts|pageimages&exintro=true&explaintext=true&pithumbsize=400&format=json&origin=*`;
          const contentResponse = await fetch(contentUrl);
          const contentData = await contentResponse.json();
          
          const page = contentData.query.pages[pageId];
          setInfo({
            title: place,
            extract: page.extract || "No description available.",
            image: page.thumbnail?.source || null
          });
        } else {
          setInfo(null);
        }
      } catch (error) {
        console.error("Wikipedia error:", error);
        setInfo(null);
      } finally {
        setLoading(false);
      }
    };

    fetchWikipediaInfo();
  }, [place]);

  return (
    <>
      <div className="search">
        <div className="container">
          <input
            type="text"
            placeholder="Search your destination"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
        </div>
        <button onClick={handleSearch}>Search</button>
      </div>
      
      {place && (
        <div className="information-container">
          <h4>{place.toUpperCase()}</h4>
          {loading && <p>Loading information...</p>}
          {!loading && info && (
            <div className="details">
              <div className="para">
                <p>{info.extract.substring(0, 600)}...</p>
                <a 
                  href={`https://en.wikipedia.org/wiki/${encodeURIComponent(place.replace(/ /g, '_'))}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Read more on Wikipedia →
                </a>
              </div>
              {info.image && (
                <img
                  src={info.image}
                  alt={place}
                  height="300px"
                  width="400px"
                  style={{ objectFit: "cover", borderRadius: "20px" }}
                />
              )}
            </div>
          )}
          {!loading && !info && (
            <p>No information found for {place}. Try another destination.</p>
          )}
        </div>
      )}
    </>
  );
};

export default Overview;