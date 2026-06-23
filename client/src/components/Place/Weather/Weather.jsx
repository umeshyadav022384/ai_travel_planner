import React, { useEffect, useState } from "react";
import axios from "axios";
import "./Weather.scss";
import { useSelector } from "react-redux";
import { getPlace } from "../../../features/placeSlice";

const URL = "https://weatherapi-com.p.rapidapi.com/forecast.json";

const Weather = () => {
  const [weather, setWeather] = useState();
  const { place } = useSelector(getPlace);

  useEffect(() => {
    const options = {
      params: { q: place, days: "3" },
      headers: {
        "X-RapidAPI-Key": "cce1cee0b2msh18ecb2e9fbee23fp10f85djsn6d68b7519c30",
        "X-RapidAPI-Host": "weatherapi-com.p.rapidapi.com",
      },
    };

    const getWeather = async () => {
      try {
        const { data } = await axios.get(URL, options);
        setWeather(data);
      } catch (error) {
        console.error("Error fetching weather data:", error.response?.data || error.message);
      }
    };

    if (place !== "") {
      getWeather();
    }
  }, [place]);

  const giveDate = (date) => {
    const formattedDate = new Date(date).toDateString();
    return formattedDate;
  };

  return (
    <>
      {weather ? (
        <>
          <h6>{weather.location.name}</h6>
          {weather.forecast.forecastday.map((d, i) => (
            <div className="card" key={i}>
              <p style={{ fontWeight: "700" }}>{giveDate(d.date)}</p>
              <div className="weather-info">
                <div className="weath">
                  <img src={d.day.condition.icon} alt="icon" />
                  <h6 className="text-capitalize">{d.day.condition.text}</h6>
                </div>
                <div className="temp">
                  <p style={{ fontWeight: "500" }}>
                    Max:{" "}
                    <span style={{ fontWeight: "normal" }}>
                      {d.day.maxtemp_c} &#176;C
                    </span>
                  </p>
                  <p style={{ fontWeight: "500" }}>
                    Min:{" "}
                    <span style={{ fontWeight: "normal" }}>
                      {d.day.mintemp_c} &#176;C
                    </span>
                  </p>
                </div>
              </div>
            </div>
          ))}
        </>
      ) : (
        <h6>Loading ...</h6>
      )}
    </>
  );
};

export default Weather;