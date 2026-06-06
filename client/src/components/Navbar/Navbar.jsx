import React from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Navbar.scss";
import logo from "../../assets/logo.png";
const Navbar = () => {
  //const navigate =useNavigate();
  //const dispatch= useDispatch();
  //const { user } = useSelector(getUser);

  return (
    <nav className=" navbar navbar-expand-lg">
      <div className="container-fluid ">
        <Link className="navbar-brand" to="/">
          <div className="d-flex">
            <img src={logo} alt="logo" height="50px" />
            <span>
              <p>Travel</p>
              <p>Planner</p>
            </span>
          </div>
        </Link>
        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
          aria-controls="navbarNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <div
          className="collapse navbar-collapse justify-content-evenly"
          id="navbarNav"
        >
          <div className="navbar-nav first justify-content-center">
            <Link to="/" className="nav-item nav-link text-uppercase mx-1">
              HOME
            </Link>
            <Link to="/place" className="nav-item nav-link text-uppercase mx-1">
              Places
            </Link>
            <Link
              to="/generate"className="nav-item nav-link text-uppercase mx-1">
              Generate
            </Link>
            <Link
              to="/chatbot"
              className="nav-item nav-link text-uppercase mx-1"
            >
              Chatbot
            </Link>
           
          </div>
        </div>
      </div>
    </nav>
  );
};
export default Navbar;
