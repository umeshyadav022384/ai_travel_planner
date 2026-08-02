import React, { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { deleteBucketList } from "../../../features/bucketListSlice";
import "./BucketList.scss";
import { addPlace } from "../../../features/placeSlice";
import { useNavigate } from "react-router-dom";

const BucketList = ({ place }) => {
  const dispatch = useDispatch();
  const [imageUrl, setImageUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const handleDelete = () => {
    dispatch(deleteBucketList(place._id));
  };

  const handleBucketListPlace = () => {
    dispatch(addPlace(place.place));
    navigate("/place");
  };

  // Fetch Wikipedia image using FREE API (no API key needed)
  useEffect(() => {
    const fetchWikipediaImage = async () => {
      setLoading(true);
      try {
        // Step 1: Search for the place
        const searchUrl = `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(place.place)}&format=json&origin=*`;
        const searchResponse = await fetch(searchUrl);
        const searchData = await searchResponse.json();

        if (searchData.query.search.length > 0) {
          const pageId = searchData.query.search[0].pageid;

          // Step 2: Get page content and image
          const contentUrl = `https://en.wikipedia.org/w/api.php?action=query&pageids=${pageId}&prop=extracts|pageimages&exintro=true&explaintext=true&pithumbsize=400&format=json&origin=*`;
          const contentResponse = await fetch(contentUrl);
          const contentData = await contentResponse.json();

          const page = contentData.query.pages[pageId];
          
          
          if (page.thumbnail && page.thumbnail.source) {
            setImageUrl(page.thumbnail.source);
          } else {
            
            setImageUrl(`https://via.placeholder.com/400x300/3498db/white?text=${encodeURIComponent(place.place)}`);
          }
        } else {
          setImageUrl(`https://via.placeholder.com/400x300/e74c3c/white?text=${encodeURIComponent(place.place)}`);
        }
      } catch (error) {
        console.error("Error fetching Wikipedia image:", error);
        setImageUrl(`https://via.placeholder.com/400x300/95a5a6/white?text=${encodeURIComponent(place.place)}`);
      } finally {
        setLoading(false);
      }
    };

    if (place && place.place) {
      fetchWikipediaImage();
    }
  }, [place]);

  return (
    <div className="card bucket">
      {loading ? (
        <div className="image-placeholder loading">
          <span>Loading...</span>
        </div>
      ) : (
        <img 
          src={imageUrl} 
          alt={place.place} 
          onClick={handleBucketListPlace}
          onError={() => setImageUrl(`https://via.placeholder.com/400x300/95a5a6/white?text=${encodeURIComponent(place.place)}`)}
        />
      )}
      <div className="places" onClick={handleBucketListPlace}>
        <h4>{place.place}</h4>
      </div>
      <div className="icons">
        <i className="fa-solid fa-trash-can" onClick={handleDelete}></i>
      </div>
    </div>
  );
};

export default BucketList;