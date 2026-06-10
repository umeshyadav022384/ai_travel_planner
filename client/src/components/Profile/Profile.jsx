import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { getUser } from "../../features/userSlice";
import { getBucketList, getBucketListItems } from "../../features/bucketListSlice";
import { toast } from "react-toastify";
import "./Profile.scss";

const Profile = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector(getUser);
  const { bucketList } = useSelector(getBucketListItems);

  useEffect(() => {
    if (!user) {
      navigate("/login");
      toast.warning("Please login to view your profile");
    }
    if (user) {
      dispatch(getBucketList());
    }
  }, [user, navigate, dispatch]);

  if (!user) {
    return (
      <div className="profile-loading">
        <div className="spinner"></div>
        <p>Redirecting to login...</p>
      </div>
    );
  }

  // Get initials for avatar
  const getInitials = () => {
    const nameParts = user.name?.split(" ") || [];
    if (nameParts.length >= 2) {
      return `${nameParts[0][0]}${nameParts[1][0]}`.toUpperCase();
    }
    return user.name?.charAt(0).toUpperCase() || "U";
  };

  // Get random gradient for avatar
  const gradients = [
    "gradient-1",
    "gradient-2",
    "gradient-3",
    "gradient-4",
    "gradient-5",
  ];
  const randomGradient = gradients[Math.floor(Math.random() * gradients.length)];

  return (
    <div className="profile-container">
      {/* Hero Section with Gradient */}
      <div className="profile-hero">
        <div className="hero-overlay"></div>
        <div className="hero-content">
          <div className={`avatar-wrapper ${randomGradient}`}>
            <div className="avatar-initials">{getInitials()}</div>
          </div>
          <h1 className="user-name">{user.name}</h1>
          <p className="user-email">{user.email}</p>
          <div className="user-badge">
            <span className="badge-icon">✈️</span>
            <span>Travel Enthusiast</span>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="stats-section">
        <div className="stat-card">
          <div className="stat-icon">📌</div>
          <div className="stat-info">
            <h3>{bucketList?.length || 0}</h3>
            <p>Bucket List</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🌍</div>
          <div className="stat-info">
            <h3>{user.bio ? "Active" : "New"}</h3>
            <p>Traveler Status</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⭐</div>
          <div className="stat-info">
            <h3>Explorer</h3>
            <p>Member Type</p>
          </div>
        </div>
      </div>

      {/* Profile Info Card */}
      <div className="profile-card">
        <div className="card-header">
          <h3>
            <span className="header-icon">👤</span>
            Personal Information
          </h3>
        </div>
        <div className="card-body">
          <div className="info-row">
            <div className="info-label">
              <i className="fas fa-user"></i>
              <span>Full Name</span>
            </div>
            <div className="info-value">
              <p>{user.name}</p>
            </div>
          </div>
          <div className="info-row">
            <div className="info-label">
              <i className="fas fa-envelope"></i>
              <span>Email Address</span>
            </div>
            <div className="info-value">
              <p>{user.email}</p>
            </div>
          </div>
          <div className="info-row">
            <div className="info-label">
              <i className="fas fa-pen"></i>
              <span>Bio</span>
            </div>
            <div className="info-value">
              <p>{user.bio || "Travel enthusiast exploring the world!"}</p>
            </div>
          </div>
          <div className="info-row">
            <div className="info-label">
              <i className="fas fa-calendar"></i>
              <span>Member Since</span>
            </div>
            <div className="info-value">
              <p>{new Date(user.createdAt).toLocaleDateString() || "2024"}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Bucket List Section */}
      <div className="bucketlist-section">
        <div className="section-header">
          <h3>
            <span className="header-icon">📋</span>
            My Bucket List
          </h3>
          <button className="explore-btn" onClick={() => navigate("/")}>
            + Add More Places
          </button>
        </div>
        <div className="bucketlist-grid">
          {bucketList && Array.isArray(bucketList) && bucketList.length > 0 ? (
            bucketList.map((item) => (
              <div className="bucketlist-card" key={item._id}>
                <div className="card-icon">📍</div>
                <div className="card-content">
                  <h4>{item.place}</h4>
                  <p>Dream destination</p>
                </div>
                <button className="card-action" onClick={() => navigate(`/place?dest=${item.place}`)}>
                  Explore →
                </button>
              </div>
            ))
          ) : (
            <div className="empty-state">
              <div className="empty-icon">🗺️</div>
              <h4>Your bucket list is empty</h4>
              <p>Start adding your dream destinations!</p>
              <button className="explore-btn" onClick={() => navigate("/")}>
                Explore Destinations
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Scroll to top button */}
      <button
        className="scroll-top"
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      >
        ↑
      </button>
    </div>
  );
};

export default Profile;