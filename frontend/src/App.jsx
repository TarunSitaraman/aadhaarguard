import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

// --- LEAFLET ICON FIX ---
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// --- DEPLOYMENT URL CONFIG ---
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const formatText = (text) => text ? text.toString().replace(/_/g, ' ') : "";

// --- INDIA BOUNDS ---
const INDIA_BOUNDS = [
  [6.0, 68.0],   
  [37.5, 97.5]   
];

// --- COMPONENTS ---
const NeonInput = ({ label, type = "text", name, value, onChange, options = null, min, max }) => {
  if (type === 'range') {
    return (
      <div className="input-group">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <label style={{ color: '#a099d8', fontWeight: 'bold' }}>{label}</label>
          <span style={{ color: '#fff', fontSize: '0.9rem' }}>{value}</span>
        </div>
        <div className="simple-slider-wrapper">
          <input className="level" type="range" name={name} value={value} onChange={onChange} min={min} max={max} />
        </div>
      </div>
    );
  }
  if (options) {
    return (
      <div className="input-group">
        <label style={{ color: '#a099d8', marginBottom: '8px', display: 'block', fontWeight: 'bold' }}>{label}</label>
        <div className="select" tabIndex="0">
          <div className="selected">
            {formatText(value)}
            <svg xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 512 512" className="arrow">
              <path d="M233.4 406.6c12.5 12.5 32.8 12.5 45.3 0l192-192c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L256 338.7 86.6 169.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l192 192z"></path>
            </svg>
          </div>
          <div className="options">
            {options.map(opt => (
              <div key={opt} className="option" onClick={() => onChange({ target: { name: name, value: opt } })}>
                {formatText(opt)}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="input-group">
      <label style={{ color: '#a099d8', marginBottom: '8px', display: 'block', fontWeight: 'bold' }}>{label}</label>
      <div className="input-container">
        <div className="glow-layer"><div className="white"></div><div className="border"></div><div className="darkBorderBg"></div><div className="glow"></div></div>
        <input className="input" type={type} name={name} value={value} onChange={onChange} />
      </div>
    </div>
  );
};

const GlassButton = ({ text, onClick }) => {
  const letters = text.split("").map((char, index) => <span key={index} className="btn-letter">{char === " " ? "\u00A0" : char}</span>);
  return (<div className="btn-wrapper"><button className="btn" onClick={onClick}>{letters}</button></div>);
};

// --- OPTIMIZED MAP LAYER ---
const OptimizedMapLayer = ({ points }) => {
  const map = useMap();
  const layerRef = useRef(null);
  const rendererRef = useRef(L.canvas({ padding: 0.5 }));

  useEffect(() => {
    if (!map || !points.length) return;

    if (!layerRef.current) {
      layerRef.current = L.layerGroup().addTo(map);
    }

    const drawPoints = () => {
      const layer = layerRef.current;
      layer.clearLayers();
      
      const zoom = map.getZoom();
      const isZoomedOut = zoom < 6;

      const markers = [];
      points.forEach(pt => {
        if (isZoomedOut && pt.health_score >= 40) return;

        let color = '#22c55e';
        if (pt.health_score < 40) color = '#ef4444';
        else if (pt.health_score < 70) color = '#eab308';

        const marker = L.circleMarker([pt.latitude, pt.longitude], {
          renderer: rendererRef.current,
          radius: 4, // Made slightly bigger to be easier to click
          color: color,
          fillColor: color,
          fillOpacity: 0.8,
          stroke: false, 
          interactive: true // CHANGED: Must be true for clicks to work
        });

        // CHANGED: Bind Popup with details
        marker.bindPopup(`
          <div style="font-family: sans-serif; min-width: 150px;">
            <h3 style="margin: 0 0 5px 0; color: #333;">${pt.name}</h3>
            <div style="font-size: 14px; margin-bottom: 3px;"><strong>Score:</strong> <span style="color:${color}; font-weight:bold;">${pt.health_score}</span></div>
            <div style="font-size: 12px; color: #666;">
              Age: ${pt.age} | ${pt.gender}<br/>
              Job: ${pt.occupation}<br/>
              Loc: ${pt.district.replace(/_/g, ' ')}<br/>
              Status: <strong>${pt.auth_status}</strong>
            </div>
          </div>
        `);

        markers.push(marker);
      });

      if (markers.length > 0) {
        L.layerGroup(markers).addTo(layer);
      }
    };

    drawPoints();

    const onZoomEnd = () => requestAnimationFrame(drawPoints);
    map.on('zoomend', onZoomEnd);

    return () => {
      map.off('zoomend', onZoomEnd);
      if (layerRef.current) layerRef.current.clearLayers();
    };
  }, [map, points]);

  return null;
};

// --- MAIN APP ---
function App() {
  const [formData, setFormData] = useState({
    age: 45, days_since_update: 365, district: 'Central_Metro', occupation: 'Farmer', gender: 'Male'
  });
  const [result, setResult] = useState(null);
  const [mapPoints, setMapPoints] = useState([]);

  const districtCoords = {
    'North_District': [28.6139, 77.2090], 'South_Tech_Hub': [12.9716, 77.5946],
    'East_Industrial': [22.5726, 88.3639], 'West_Rural': [19.0760, 72.8777], 'Central_Metro': [23.2599, 77.4126]
  };
  const districts = Object.keys(districtCoords);
  const occupations = ['Farmer', 'Construction', 'Student', 'IT_Professional'];

  useEffect(() => {
    axios.get(`${API_URL}/map_data`)
      .then(res => setMapPoints(res.data))
      .catch(err => console.error("Error fetching map points:", err));
  }, []);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const checkHealth = async () => {
    try {
      const response = await axios.post(`${API_URL}/predict_health_score`, formData);
      setResult(response.data);
    } catch (error) { alert("Backend error. Is the server running?"); }
  };

  const getColor = (score) => {
    if (score < 40) return '#ef4444';
    if (score < 70) return '#eab308';
    return '#22c55e';
  };

  return (
    <div className="container">
      <div style={{
        position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', 
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', 
        backgroundSize: '30px 30px', zIndex: -10 
      }}></div>

      <h1>Aadhaar Guard</h1>
      <p style={{textAlign: 'center', color: '#666'}}>Predictive Resilience System</p>

      <div className="dashboard-grid">
        <div className="card">
          <h2>Simulation Controls</h2>
          <NeonInput label="Select District" name="district" value={formData.district} onChange={handleChange} options={districts} />
          <NeonInput label="Occupation" name="occupation" value={formData.occupation} onChange={handleChange} options={occupations} />
          <NeonInput label="Citizen Age" type="range" name="age" value={formData.age} onChange={handleChange} min="5" max="90" />
          <NeonInput label="Days Since Update" type="range" name="days_since_update" value={formData.days_since_update} onChange={handleChange} min="10" max="3650" />
          <GlassButton text="ANALYZE RISK" onClick={checkHealth} />

          {result && (
            <div style={{ textAlign: 'center', marginTop: '30px', borderTop: '1px solid #333', paddingTop: '20px' }}>
              <div className="score-circle" style={{ color: getColor(result.health_score) }}>{result.health_score}</div>
              <p style={{ color: getColor(result.health_score), fontWeight: 'bold', fontSize: '1.2rem' }}>{formatText(result.status)}</p>
            </div>
          )}
        </div>

        <div className="card" style={{ padding: 0, overflow: 'hidden', background: '#101010', backdropFilter: 'none' }}>
          <MapContainer 
            center={[22.5937, 78.9629]} 
            zoom={5}
            minZoom={5}
            maxBounds={INDIA_BOUNDS}
            maxBoundsViscosity={1.0}
            scrollWheelZoom={true} 
            preferCanvas={true} 
            style={{ height: "100%", width: "100%", background: '#000' }}
          >
            <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" attribution='&copy; CARTO' />
            
            <OptimizedMapLayer points={mapPoints} />

            {result && (
              <Marker position={districtCoords[formData.district]}>
                <Popup><strong>Simulated User</strong><br/>{formatText(formData.district)}<br/>Score: {result.health_score}</Popup>
              </Marker>
            )}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}

export default App;