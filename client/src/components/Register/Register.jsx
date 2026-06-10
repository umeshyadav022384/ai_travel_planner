import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { getUser, reset, userRegister } from "../../features/userSlice";
import { toast } from "react-toastify";
import "./Register.scss";

const Register = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    bio: "",
  });
  const [touched, setTouched] = useState({
    name: false,
    email: false,
    password: false,
    bio: false,
  });
  const [showPassword, setShowPassword] = useState(false);

  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { user, isError, isLoading, isSuccess, message } = useSelector(getUser);

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
    if (!formData.name) errors.name = "Name is required";
    if (!formData.email) errors.email = "Email is required";
    if (!formData.password) errors.password = "Password is required";
    if (formData.password && formData.password.length < 6) 
      errors.password = "Password must be at least 6 characters";
    if (!formData.bio) errors.bio = "Bio is required";
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      Object.values(errors).forEach(toast.error);
      return;
    }

    const result = await dispatch(userRegister(formData));
    
    if (userRegister.rejected.match(result)) {
      toast.error(result.payload || "Registration failed. Please try again.");
    }
  };

  useEffect(() => {
    if (isError && message) {
      toast.error(message);
    }
    
    if (isSuccess || user) {
      toast.success("Account created successfully! 🎉");
      navigate("/");
    }
    
    return () => {
      dispatch(reset());
    };
  }, [isError, isSuccess, user, message, navigate, dispatch]);

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Creating your account...</p>
      </div>
    );
  }

  return (
    <div className="register-container">
      <div className="register-card">
        {/* Left Side - Brand Section */}
        <div className="brand-section">
          <div className="brand-content">
            <div className="logo">
              <span className="logo-icon">✈️</span>
              <h2>Travel Planner</h2>
            </div>
            <h1>Join the Adventure</h1>
            <p>Create an account to start planning your dream trips with AI-powered recommendations.</p>
            <div className="features">
              <div className="feature">
                <span className="feature-icon">✓</span>
                <span>AI-powered itineraries</span>
              </div>
              <div className="feature">
                <span className="feature-icon">✓</span>
                <span>Smart recommendations</span>
              </div>
              <div className="feature">
                <span className="feature-icon">✓</span>
                <span>Save your bucket list</span>
              </div>
              <div className="feature">
                <span className="feature-icon">✓</span>
                <span>Ask Questions with Chatbot</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Form Section */}
        <div className="form-section">
          <div className="form-header">
            <h2>Create Account</h2>
            <p>Join thousands of travelers exploring the world</p>
          </div>

          <form onSubmit={handleSubmit} autoComplete="off">
            {/* Name Field */}
            <div className="input-group">
              <div className="input-icon">
                <svg className="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div className="input-field">
                <input
                  type="text"
                  id="name"
                  className={touched.name && !formData.name ? "error" : ""}
                  placeholder=" "
                  value={formData.name}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  autoComplete="off"
                />
                <label htmlFor="name">Full Name</label>
                {touched.name && !formData.name && (
                  <span className="error-msg">Name is required</span>
                )}
              </div>
            </div>

            {/* Email Field */}
            <div className="input-group">
              <div className="input-icon">
                <svg className="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="input-field">
                <input
                  type="email"
                  id="email"
                  className={touched.email && !formData.email ? "error" : ""}
                  placeholder=" "
                  value={formData.email}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  autoComplete="off"
                />
                <label htmlFor="email">Email Address</label>
                {touched.email && !formData.email && (
                  <span className="error-msg">Email is required</span>
                )}
              </div>
            </div>

            {/* Password Field */}
            <div className="input-group">
              <div className="input-icon">
                <svg className="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <div className="input-field">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  className={touched.password && (!formData.password || formData.password.length < 6) ? "error" : ""}
                  placeholder=" "
                  value={formData.password}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  autoComplete="off"
                />
                <label htmlFor="password">Password</label>
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  
                </button>
                {touched.password && !formData.password && (
                  <span className="error-msg">Password is required</span>
                )}
                {touched.password && formData.password && formData.password.length < 6 && (
                  <span className="error-msg">Password must be at least 6 characters</span>
                )}
              </div>
            </div>

            {/* Bio Field */}
            <div className="input-group">
              <div className="input-icon">
                <svg className="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                </svg>
              </div>
              <div className="input-field">
                <textarea
                  id="bio"
                  className={touched.bio && !formData.bio ? "error" : ""}
                  placeholder=" "
                  rows="3"
                  value={formData.bio}
                  onChange={handleChange}
                  onBlur={handleBlur}
                />
                <label htmlFor="bio">Tell us about yourself</label>
                {touched.bio && !formData.bio && (
                  <span className="error-msg">Bio is required</span>
                )}
              </div>
            </div>

            <button type="submit" className="submit-btn" disabled={isLoading}>
              {isLoading ? (
                <>
                  <span className="btn-spinner"></span>
                  Creating account...
                </>
              ) : (
                "Create Account"
              )}
            </button>

            <div className="form-footer">
              <p>
                Already have an account? <Link to="/login">Sign in</Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Register;