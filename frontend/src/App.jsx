import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

const App = () => {
  const [bikeList, setBikeList] = useState([]);
  const [selectedBikeData, setSelectedBikeData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initial Fetch: Get the list of bikes
  useEffect(() => {
    fetch('http://localhost:8000/bikes')
      .then(res => res.json())
      .then(data => {
        setBikeList(data);
        setLoading(false);
      })
      .catch(err => console.error("Error fetching bike list:", err));
  }, []);

  // Action: Fetch specific kinematics when a bike is clicked
  const handleSelectBike = (bikeId) => {
    fetch(`http://localhost:8000/kinematics/${bikeId}`)
      .then(res => res.json())
      .then(data => {
        setSelectedBikeData(data);
      })
      .catch(err => console.error("Error fetching kinematics:", err));
  };

  if (loading) return <div style={{ padding: '40px' }}>Connecting to Kinematics Database...</div>;

  return (
    <div style={{ padding: '40px', fontFamily: 'sans-serif', maxWidth: '1000px', margin: '0 auto' }}>
      <h1>MTB Kinematics Browser</h1>
      
      {/* Bike Selection Buttons */}
      <div style={{ marginBottom: '30px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        {bikeList.map(bike => (
          <button 
            key={bike.id} 
            onClick={() => handleSelectBike(bike.id)}
            style={{ 
              padding: '10px 15px',
              backgroundColor: selectedBikeData?.model === bike.model ? '#4CAF50' : '#f0f0f0',
              color: selectedBikeData?.model === bike.model ? 'white' : 'black',
              border: '1px solid #ccc',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {bike.brand} {bike.model}
          </button>
        ))}
      </div>

      {/* Chart Section */}
      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
        {selectedBikeData ? (
          <>
            <h3>{selectedBikeData.model} - Leverage Ratio</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={selectedBikeData.points}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis 
                  dataKey="travel" 
                  type="number"
                  label={{ value: 'Travel (mm)', position: 'insideBottom', offset: -10 }} 
                />
                <YAxis 
                  domain={['auto', 'auto']} 
                  label={{ value: 'Ratio', angle: -90, position: 'insideLeft' }} 
                />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="ratio" 
                  stroke="#4CAF50" 
                  strokeWidth={3} 
                  dot={{ r: 4 }} 
                />
              </LineChart>
            </ResponsiveContainer>
          </>
        ) : (
          <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666' }}>
            Select a bike above to visualize its leverage curve.
          </div>
        )}
      </div>
    </div>
  );
};

export default App;