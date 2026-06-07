import React, { useEffect, useState } from "react";
import axios from "axios";
import "./News.scss";
import { useSelector } from "react-redux";
import { getPlace } from "../../../features/placeSlice";

const News = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(false);
  const { place } = useSelector(getPlace);

  useEffect(() => {
    if (!place) return;

    const getNews = async () => {
      setLoading(true);
      try {
        // Search for the specific place in the query parameter
        const response = await axios.get("https://newsdata.io/api/1/news", {
          params: {
            apikey: "pub_32b8791c947347f79849dec2f355642e",
            q: place,  // This searches for the specific place name
            language: 'en',
            size: 10,
          },
        });

        // Filter to ensure news is about the specific place
        let articles = response.data.results || [];
        
        // Additional filter to make sure news contains the place name
        const filteredArticles = articles.filter(article => {
          const title = (article.title || '').toLowerCase();
          const description = (article.description || '').toLowerCase();
          const placeLower = place.toLowerCase();
          return title.includes(placeLower) || description.includes(placeLower);
        });
        
        setNews(filteredArticles.slice(0, 6));
      } catch (error) {
        console.error("News error:", error);
        setNews([]);
      } finally {
        setLoading(false);
      }
    };

    getNews();
  }, [place]);

  if (loading) return <div className="news-container"><h5>Loading news for {place}...</h5></div>;
  
  if (news.length === 0) {
    return (
      <div className="news-container">
        <h5>News from {place?.toUpperCase()}</h5>
        <p>No recent news found for {place}. Try searching for a larger city.</p>
      </div>
    );
  }

  return (
    <div className="news-container">
      <h5 style={{ fontWeight: "700" }}>News from {place.toUpperCase()}</h5>
      {news.map((article, index) => (
        <div className="card" key={index}>
          <div className="headline">
            <a href={article.link} target="_blank" rel="noreferrer noopener">
              {article.title}
            </a>
            <p>{article.description}</p>
          </div>
          {article.image_url && (
            <div className="img">
              <img src={article.image_url} alt="news" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default News;