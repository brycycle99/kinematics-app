import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

// New Neon/Dark-Mode friendly colors
const COLORS = ['#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ef4444', '#f43f5e'];

const Browser = ({ bikeList }) => {
  const [selectedBikes, setSelectedBikes] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  
  const [xAxisKey, setXAxisKey] = useState("travel");
  const [yAxisKey, setYAxisKey] = useState("leverage_ratio");

  const handleSelectBike = (bikeId) => {
    if (selectedBikes.some(b => b.metadata.id === bikeId)) {
      setSelectedBikes(selectedBikes.filter(b => b.metadata.id !== bikeId));
      return;
    }

    fetch(`http://localhost:8000/kinematics/${bikeId}`)
      .then(res => res.json())
      .then(data => {
        setSelectedBikes([...selectedBikes, data]);
      })
      .catch(err => console.error("Error fetching kinematics:", err));
  };

  const filteredBikes = bikeList.filter(bike => 
    `${bike.make} ${bike.model}`.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const metricOptions = [
    "travel", "travel_percent", "leverage_ratio", 
    "anti_squat_low", "anti_squat_high", "anti_rise_low", "anti_rise_high", 
    "pedal_kickback_low", "pedal_kickback_high", "chain_growth_low", "chain_growth_high", 
    "shock_compression", "axle_path_x", "axle_path_radius", "axle_path_steepness"
  ];

  const getMetricLabel = (key) => {
    const labels = {
      travel: "Wheel Travel (mm)",
      travel_percent: "Wheel Travel (%)",
      leverage_ratio: "Leverage Ratio",
      anti_squat_low: "Anti-Squat (Climb Gear)",
      anti_squat_high: "Anti-Squat (Descend Gear)",
      anti_rise_low: "Anti-Rise (Climb Gear)",
      anti_rise_high: "Anti-Rise (Descend Gear)",
      pedal_kickback_low: "Pedal Kickback (Climb)",
      pedal_kickback_high: "Pedal Kickback (Descend)",
      chain_growth_low: "Chain Growth (Climb)",
      chain_growth_high: "Chain Growth (Descend)",
      shock_compression: "Shock Compression",
      axle_path_x: "Axle Path X (mm)",
      axle_path_radius: "Axle Path Radius (mm)",
      axle_path_steepness: "Axle Path Steepness (°)"
    };
    return labels[key] || key;
  };

  return (
    <div style={{ padding: '30px', maxWidth: '1400px', margin: '0 auto' }}>
      <nav style={{ marginBottom: '30px' }}>
        <Link to="/" style={{ color: '#3b82f6', textDecoration: 'none', fontWeight: '600', letterSpacing: '0.5px' }}>
          ← Back to Project Home
        </Link>
      </nav>

      <div style={{ display: 'flex', gap: '30px', flexWrap: 'wrap' }}>
        
        {/* Sidebar */}
        <div style={{ flex: '1', minWidth: '300px' }}>
          <h2 style={{ marginBottom: '20px', color: '#fff', fontWeight: '600' }}>Compare Bikes</h2>
          <input 
            type="text" 
            placeholder="Search make or model..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ 
              width: '100%', padding: '14px', marginBottom: '20px', 
              borderRadius: '8px', border: '1px solid #333', 
              backgroundColor: '#1e1e1e', color: '#fff', outline: 'none'
            }}
          />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '70vh', overflowY: 'auto', paddingRight: '10px' }}>
            {filteredBikes.map(bike => {
              const isSelected = selectedBikes.some(b => b.metadata.id === bike.id);
              const colorIndex = selectedBikes.findIndex(b => b.metadata.id === bike.id);
              const activeColor = COLORS[colorIndex % COLORS.length];
              
              return (
                <button 
                  key={bike.id} 
                  onClick={() => handleSelectBike(bike.id)}
                  style={{ 
                    padding: '14px', textAlign: 'left',
                    backgroundColor: isSelected ? activeColor : '#1e1e1e',
                    color: isSelected ? '#fff' : '#b3b3b3',
                    border: `1px solid ${isSelected ? activeColor : '#333'}`, 
                    borderRadius: '8px', cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <div style={{ fontWeight: '600', color: isSelected ? '#fff' : '#e0e0e0' }}>{bike.make} {bike.model}</div>
                  <div style={{ fontSize: '0.85rem', opacity: isSelected ? 0.9 : 0.6, marginTop: '4px' }}>{bike.year} | {bike.suspension_design}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Main Panel */}
        <div style={{ flex: '2.5', minWidth: '600px', backgroundColor: '#1e1e1e', padding: '25px', borderRadius: '12px', border: '1px solid #333' }}>
          {selectedBikes.length > 0 ? (
            <>
              {/* Custom Axis Controls */}
              <div style={{ display: 'flex', gap: '20px', marginBottom: '30px', backgroundColor: '#262626', padding: '20px', borderRadius: '8px', border: '1px solid #333' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px', fontSize: '0.85rem', color: '#a0a0a0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Y-Axis Metric</label>
                  <select 
                    value={yAxisKey} 
                    onChange={(e) => setYAxisKey(e.target.value)}
                    style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #444', backgroundColor: '#121212', color: '#fff', outline: 'none' }}
                  >
                    {metricOptions.map(key => <option key={key} value={key}>{getMetricLabel(key)}</option>)}
                  </select>
                </div>
                
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px', fontSize: '0.85rem', color: '#a0a0a0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>X-Axis Metric</label>
                  <select 
                    value={xAxisKey} 
                    onChange={(e) => setXAxisKey(e.target.value)}
                    style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #444', backgroundColor: '#121212', color: '#fff', outline: 'none' }}
                  >
                    {metricOptions.map(key => <option key={key} value={key}>{getMetricLabel(key)}</option>)}
                  </select>
                </div>
              </div>

              {/* Dynamic Multi-Line Chart */}
              <div style={{ height: '550px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart margin={{ top: 20, right: 30, left: 20, bottom: 40 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                    
                    <XAxis 
                      dataKey={xAxisKey} 
                      type="number" 
                      allowDuplicatedCategory={false} 
                      domain={['auto', 'auto']} 
                      stroke="#888"
                      tick={{ fill: '#888' }}
                      label={{ value: getMetricLabel(xAxisKey), position: 'bottom', offset: 20, fill: '#a0a0a0', fontSize: 14 }} 
                      tickFormatter={(val) => Number.isInteger(val) ? val : val.toFixed(1)}
                    />
                    
                    <YAxis 
                      dataKey={yAxisKey} 
                      type="number"
                      domain={['auto', 'auto']} 
                      stroke="#888"
                      tick={{ fill: '#888' }}
                      label={{ value: getMetricLabel(yAxisKey), angle: -90, position: 'left', offset: 0, fill: '#a0a0a0', fontSize: 14 }} 
                      tickFormatter={(val) => Number.isInteger(val) ? val : val.toFixed(1)}
                    />
                    
                    <Tooltip 
                      formatter={(value, name) => [value, name]}
                      labelFormatter={(label) => `${getMetricLabel(xAxisKey)}: ${label}`}
                      contentStyle={{ backgroundColor: '#262626', borderRadius: '8px', border: '1px solid #444', color: '#fff', boxShadow: '0 8px 24px rgba(0,0,0,0.4)' }}
                      itemStyle={{ color: '#fff', fontWeight: '500' }}
                    />
                    <Legend verticalAlign="top" height={40} wrapperStyle={{ color: '#e0e0e0' }} />
                    
                    {selectedBikes.map((bike, index) => (
                      <Line 
                        key={bike.metadata.id}
                        data={bike.points} 
                        dataKey={yAxisKey} 
                        name={`${bike.metadata.make} ${bike.metadata.model}`}
                        stroke={COLORS[index % COLORS.length]} 
                        strokeWidth={3} 
                        dot={false}
                        activeDot={{ r: 6, fill: '#1e1e1e', stroke: COLORS[index % COLORS.length], strokeWidth: 2 }} 
                        animationDuration={400}
                        connectNulls={true}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          ) : (
            <div style={{ height: '550px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#666', textAlign: 'center' }}>
              <div style={{ fontSize: '3.5rem', marginBottom: '15px', opacity: 0.5 }}>📈</div>
              <p style={{ fontSize: '1.1rem', lineHeight: '1.6' }}>Select one or more bikes from the sidebar<br/>to compare their kinematics.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Browser;