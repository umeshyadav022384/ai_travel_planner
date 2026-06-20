import React from "react";
import "./Recommendation.scss";
import Template from "./Template/Template";
import kathmanduImg from "../../../assets/recommended_image/kathmandu.png";
import pokharaImg from "../../../assets/recommended_image/pokhara.png";
import chitwanImg from "../../../assets/recommended_image/chitwan.png";
import mustangImg from "../../../assets/recommended_image/mustang.png";
import lumbiniImg from "../../../assets/recommended_image/lumbini.png";
import janakpurImg from "../../../assets/recommended_image/dhanusha.jpg";
const Recommendation = () => {
  return (
    <div className="recommendation">
      <h4>Explore Major Touriste Places</h4>
      <div className="dest">
 
<Template
  place="Janakpur"
  text="Historic city, Janaki Temple, Mithila art, and religious pilgrimage site"
  url={janakpurImg}
/>
<Template
  place="Pokhara"
  text="Stunning lake city, Annapurna views, adventure sports, and peaceful atmosphere."
  url={pokharaImg}
/>

<Template
  place="Chitwan"
  text="Jungle safari, one-horned rhinos, elephants, and Tharu culture experience."
  url={chitwanImg}
/>

<Template
  place="Mustang"
  text="Mustang, also known as the 'Kingdom of Lo', is a remote region with ancient Buddhist monasteries and caves carved into cliffs, resembling the Tibetan plateau."
  url={mustangImg}
/>

<Template
place="Lumbini"
 text="Sacred birthplace of Lord Buddha, monasteries, Ashoka Pillar, and peaceful gardens."
  url={lumbiniImg}
/>
       <Template
  place="Kathmandu"
  text="Capital city with UNESCO temples, Durbar Squares, and vibrant Newari culture."
  url={kathmanduImg}
/>

      </div>
    </div>
  );
};

export default Recommendation;