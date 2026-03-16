import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Browser from './Browser'; 

const Home = ({ bikeCount }) => (
  <div style={{ 
    padding: '100px 20px', 
    textAlign: 'center', 
    maxWidth: '800px', 
    margin: '0 auto',
  }}>
    <h1 style={{ fontSize: '3.5rem', marginBottom: '10px', color: '#ffffff', letterSpacing: '-1px' }}>
      The Open Kinematics Project
    </h1>
    <h3 style={{ color: '#a0a0a0', fontWeight: '400', marginBottom: '40px', fontSize: '1.4rem' }}>
      Standardizing Mountain Bike Suspension Data
    </h3>
    
    <p style={{ fontSize: '1.15rem', lineHeight: '1.7', color: '#b3b3b3', marginBottom: '50px' }}>
      We are building an open-source, high-fidelity database of kinematics. 
      From leverage ratios to axle paths, our goal is to provide clean data for 
      comparative analysis and engineering research.
    </p>
    
    <div style={{ margin: '60px 0' }}>
      <div style={{ fontSize: '6rem', fontWeight: '800', color: '#3b82f6', lineHeight: '1' }}>
        {bikeCount}
      </div>
      <div style={{ fontSize: '1rem', color: '#666', letterSpacing: '3px', marginTop: '15px', fontWeight: '600' }}>
        BIKES INDEXED
      </div>
    </div>

    <Link to="/explore">
      <button style={{ 
        padding: '16px 45px', 
        fontSize: '1.1rem', 
        backgroundColor: '#3b82f6', 
        color: 'white', 
        border: 'none', 
        borderRadius: '8px', 
        cursor: 'pointer',
        fontWeight: '600',
        letterSpacing: '0.5px',
        transition: 'background-color 0.2s',
        boxShadow: '0 4px 14px 0 rgba(59, 130, 246, 0.39)'
      }}>
        Explore the Database
      </button>
    </Link>
  </div>
);

const App = () => {
  const [bikeList, setBikeList] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8000/bikes')
      .then(res => res.json())
      .then(data => setBikeList(data))
      .catch(err => console.error("Database connection error:", err));
  }, []);

  return (
    <div style={{ 
      backgroundColor: '#121212', 
      minHeight: '100vh', 
      color: '#e0e0e0', 
      fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' 
    }}>
      {/* Global Wrapper for Dark Mode & Sleek Fonts */}
      <Router>
        <Routes>
          <Route path="/" element={<Home bikeCount={bikeList.length} />} />
          <Route path="/explore" element={<Browser bikeList={bikeList} />} />
        </Routes>
      </Router>
    </div>
  );
};

export default App;