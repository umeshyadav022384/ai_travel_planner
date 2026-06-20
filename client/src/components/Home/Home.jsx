import React, { useState, useEffect } from "react";
import Card from "./Card/Card";
import Recommendation from "./Recommendation/Recommendation";
import "./Home.scss";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { addPlace } from "../../features/placeSlice";

// Import slider images
import slider1 from "../../assets/bhaktapur_1.png";
import slider2 from "../../assets/chitwan_1.png";
import slider3 from "../../assets/everest_1.jpg";
import slider4 from "../../assets/lumbini_1.png";
import slider5 from "../../assets/pokhara_1.png";
import slider6 from "../../assets/mustang_1.jpg";
import slider7 from "../../assets/kathmandu_1.png";
import slider8 from "../../assets/lalitpur_1.jpg";
import slider9 from "../../assets/Janaki-Mandir.jpg";


const slides = [
  {
    name: "Everest",
    image: slider3,
  },
  {
    name: "Janaki Mandir",
    image: slider9,
  },
  {
    name: "Lumbini",
    image: slider4,
  },
  {
    name: "Pokhara",
    image: slider5,
  },
  {
    name: "Mustang",
    image: slider6,
  },
  {
    name: "Bhaktapur",
    image: slider1,
  },
  {
    name: "Chitwan",
    image: slider2,
  },
  
  {
    name: "Kathmandu",
    image: slider7,
  },
  {
    name: "Lalitpur",
    image: slider8,
  },
];

const Home = () => {
  const [place, setPlace] = useState("");
  const [slideIndex, setSlideIndex] = useState(0);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  // Auto-slide every 3 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setSlideIndex((i) => (i + 1) % slides.length);
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  const handleMove = () => {
    window.scroll(0, 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    dispatch(addPlace(place));
    setPlace("");
    navigate("/place");
  };

  return (
    <div className="container-fluid">
      {/* Hero Slider Section */}
      <div 
        className="hero-slider"
        style={{ backgroundImage: `url(${slides[slideIndex].image})` }}
      >
        <div className="slider-overlay">
          <div className="slider-content">
            <h1>{slides[slideIndex].name}</h1>
            <p>Still round the corner, there may wait, a new road or a secret gate !</p>
            <div className="search">
              <input
                type="text"
                placeholder="Search your destination"
                value={place}
                onChange={(e) => setPlace(e.target.value)}
              />
              <button onClick={handleSubmit}>Search</button>
            </div>
          </div>
        </div>
      </div>

      <div className="move" onClick={handleMove}>
        <i className="fa-solid fa-angles-up"></i>
      </div>
      
      <div className="container">
        <Card />
      </div>
      <div className="container">
        <Recommendation />
      </div>
    </div>
  );
};

export default Home;