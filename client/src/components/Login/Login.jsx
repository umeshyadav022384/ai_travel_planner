import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link, useNavigate } from "react-router-dom";
import { getUser, reset, userLogin } from "../../features/userSlice";
import { clear } from "../../features/placeSlice";
import { toast } from "react-toastify";
import "./Login.scss";

const Login = () => {
  // ===== STATE =====
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [touched, setTouched] = useState({
    email: false,
    password: false,
  });

  // ===== HOOKS =====
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user, isError, isLoading, isSuccess, message } = useSelector(getUser);

  // ===== HANDLERS =====
  const handleChange = (e) => {
    const { id, value } = e.target;
    setFormData((prev) => ({ ...prev, [id]: value }));
  };

  const handleBlur = (e) => {
    const { id } = e.target;
    setTouched((prev) => ({ ...prev, [id]: true }));
  };

  const validateForm = () => {
    const errors = {};
    if (!formData.email) errors.email = "Email is required";
    if (!formData.password) errors.password = "Password is required";
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      Object.values(errors).forEach(toast.error);
      return;
    }

    dispatch(clear());
      await dispatch(userLogin(formData)); 

  };

  // ===== EFFECTS =====
  useEffect(() => {
    if (isError && message) {
      toast.error(message);
    }
    
    if (isSuccess || user) {
      navigate("/");
    }
    
    return () => {
      dispatch(reset());
    };
  }, [isError, isSuccess, user, message, navigate, dispatch]);

  // Clear form on unmount
  useEffect(() => {
    return () => {
      setFormData({ email: "", password: "" });
    };
  }, []);

  // ===== LOADING STATE =====
  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Logging in...</p>
      </div>
    );
  }

  // ===== RENDER =====
  return (
    <div className="login-container">
      <div className="login-wrapper">
        <div className="login-image">
          <img
            src="https://images.unsplash.com/photo-1564648351416-3eec9f3e85de?w=800"
            alt="Travel"
          />
        </div>
        
        <div className="login-form">
          <div className="form-header">
            <h2>Welcome Back! 👋</h2>
            <p>Login to continue your travel journey</p>
          </div>

          <form onSubmit={handleSubmit} autoComplete="off">
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <div className="input-wrapper">
                <i className="fas fa-envelope"></i>
                <input
                  type="email"
                  id="email"
                  className={`form-control ${touched.email && !formData.email ? 'error' : ''}`}
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleChange}
                  onBlur={handleBlur}
                
                />
              </div>
              {touched.email && !formData.email && (
                <small className="error-message">Email is required</small>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <div className="input-wrapper">
                <i className="fas fa-lock"></i>
                <input
                  type="password"
                  id="password"
                  className={`form-control ${touched.password && !formData.password ? 'error' : ''}`}
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  autoComplete="off"
                />
              </div>
              {touched.password && !formData.password && (
                <small className="error-message">Password is required</small>
              )}
            </div>

            <button 
              type="submit" 
              className="btn-login"
              disabled={isLoading}
            >
              {isLoading ? "Logging in..." : "Login"}
            </button>

            <div className="form-footer">
              <p>
                Don't have an account? <Link to="/register">Register here</Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;