import React from "react";
import "./Footer.scss";
import {
  FaFacebookF,
  FaTwitter,
  FaInstagram,
  FaLinkedinIn,
} from "react-icons/fa";

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-container">
        {/* About Section */}
        <div className="footer-about">
          <h3>Travel Companion</h3>
          <p>
            Your ultimate travel planner for personalized experiences and
            memorable journeys. Explore the world with ease and comfort.
          </p>
        </div>

        {/* Social Media Links */}
        <div className="footer-socials">
          <h4>Follow Us</h4>
          <div className="social-icons">
            <a
              href="https://facebook.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              <FaFacebookF />
            </a>
            <a
              href="https://twitter.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              <FaTwitter />
            </a>
            <a
              href="https://instagram.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              <FaInstagram />
            </a>
          </div>
        </div>

        {/* Contact Section */}
        <div className="footer-contact">
          <h4>Contact Us</h4>
          <p>Email: aitravel@gmail.com</p>
          <p>Phone: +9822222222</p>
          <p>Address: Nepal Engineering college</p>
        </div>
      </div>
      <div className="footer-bottom">
        &copy; {new Date().getFullYear()} Travel Companion | All Rights Reserved
      </div>
    </footer>
  );
};

export default Footer;
