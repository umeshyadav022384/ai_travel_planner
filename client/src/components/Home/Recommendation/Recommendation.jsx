import React from "react";
import "./Recommendation.scss";
import Template from "./Template/Template";

const Recommendation = () => {
  return (
    <div className="recommendation">
      <h4>Recommended Destinations</h4>
      <div className="dest">
        <Template
          place="Paris"
          text="Paris ('City of Lights' ) is the capital city of France, and the largest city in France."
          url="https://burst.shopifycdn.com/photos/the-eiffel-tower-paris.jpg?width=1000&format=pjpg&exif=0&iptc=0"
        />
        <Template
          place="Maldives"
          text="Maldives, officially the Republic of Maldives, is an archipelagic country located in Southern Asia, situated in the Indian Ocean."
          url="https://lp-cms-production.imgix.net/2020-09/The%20Nautilus%20Maldives_July19-9335.jpg"
        />
        <Template
          place="Jammu and Kashmir"
          text=" It is located to the north of Himachal Pradesh & Punjab and to the west of Ladakh and are termed as Heaven on earth."
          url="https://i.pinimg.com/736x/42/22/05/422205100239091e942c766cd13d012d.jpg"
        />
        <Template
          place="Bali"
          text="Bali, officially the Bali Province is a province of Indonesia and the westernmost of the Lesser Sunda Islands."
          url="https://media.timeout.com/images/105240189/image.jpg"
        />
        <Template
          place="Singapore"
          text="Singapore is famous for Southeast Asia's first and only Universal Studios theme park, attracting over four million visitors annually."
          url="https://dynamic-media-cdn.tripadvisor.com/media/photo-o/2e/0a/92/56/sands-skypark.jpg?w=500&h=400&s=1"
        />
        <Template
          place="Sydney"
          text="Sydney, capital of New South Wales and one of Australia's largest cities, is best known for its harbourfront Sydney Opera House."
          url="https://static.toiimg.com/photo/58515800.cms"
        />
      </div>
    </div>
  );
};

export default Recommendation;