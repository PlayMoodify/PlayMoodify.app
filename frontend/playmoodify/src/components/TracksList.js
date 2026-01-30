import { useState } from 'react';
import './TracksList.css';

const MOOD_NAMES = {
  0: 'Triste',
  1: 'Felice',
  2: 'Energico',
  3: 'Calmo'
};

const MOOD_COLORS = {
  0: '#3498db',
  1: '#f1c40f',
  2: '#e74c3c',
  3: '#2ecc71'
};

const FEATURES = [
  { key: 'danceability', label: 'Danza', color: '#667eea' },
  { key: 'energy', label: 'Energia', color: '#e74c3c' },
  { key: 'speechiness', label: 'Parole', color: '#e67e22' },
  { key: 'acousticness', label: 'Acustica', color: '#f39c12' },
  { key: 'instrumentalness', label: 'Strumenti', color: '#9b59b6' },
  { key: 'liveness', label: 'Live', color: '#1abc9c' },
  { key: 'valence', label: 'Positività', color: '#f1c40f' }
];

function TracksList({ tracks }) {
  const [expandedMood, setExpandedMood] = useState(null);

  const groupedByMood = tracks.reduce((acc, track) => {
    const mood = track.label || 0;
    if (!acc[mood]) {
      acc[mood] = [];
    }
    acc[mood].push(track);
    return acc;
  }, {});

  const moodOrder = [0, 1, 2, 3];

  const getFeatureScore = (value, feature) => {
    if (feature.isPercentage === false) {
      // Per il tempo, normalizza su 200 BPM
      return Math.min((value / feature.max) * 10, 10);
    }
    // Per gli altri, converti da 0-1 a 1-10
    return (value || 0) * 10;
  };

  return (
    <div className="tracks-list-container">
      <h3 className="section-title">Brani per Mood</h3>
      
      <div className="tracks-accordion">
        {moodOrder.map((moodId) => (
          <div key={moodId} className="mood-section">
            <button
              className="mood-section-header"
              style={{ borderLeftColor: MOOD_COLORS[moodId] }}
              onClick={() => setExpandedMood(expandedMood === moodId ? null : moodId)}
            >
              <span className="section-header-content">
                <span className="mood-section-name">{MOOD_NAMES[moodId]}</span>
                <span className="mood-section-count">
                  {groupedByMood[moodId]?.length || 0} brani
                </span>
              </span>
              <span className={`expand-icon ${expandedMood === moodId ? 'open' : ''}`}>
                ▼
              </span>
            </button>

            {expandedMood === moodId && (
              <div className="mood-section-content">
                <div className="tracks-grid">
                  {groupedByMood[moodId]?.map((track, idx) => (
                    <div key={idx} className="track-card">
                      <h4 className="track-card-title">{track.title}</h4>
                      <p className="track-card-artist">{track.artist}</p>
                      
                      <div className="features-grid">
                        {FEATURES.map((feature) => (
                          <div key={feature.key} className="feature-item">
                            <span className="feature-label">{feature.label}</span>
                            <div className="feature-score">
                              <span className="score-value">{getFeatureScore(track[feature.key], feature).toFixed(2)}</span>
                              <span className="score-max">/10</span>
                            </div>
                            <div className="feature-bar">
                              <div 
                                className="feature-fill" 
                                style={{ 
                                  width: `${Math.min((track[feature.key] || 0) * 100, 100)}%`,
                                  backgroundColor: feature.color
                                }}
                              ></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default TracksList;
