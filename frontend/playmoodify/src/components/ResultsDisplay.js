import './ResultsDisplay.css';
import MoodGauge from './MoodGauge';
import TracksList from './TracksList';

const MOOD_NAMES = {
  0: 'Triste',
  1: 'Felice',
  2: 'Energico',
  3: 'Calmo'
};

const MOOD_MAPPING = {
  'sad': 0,
  'happy': 1,
  'energetic': 2,
  'calm': 3
};

const MOOD_EMOJIS = {
  0: '😔',
  1: '😊',
  2: '🔥',
  3: '😌'
};

const MOOD_COLORS = {
  0: '#3498db',
  1: '#f1c40f',
  2: '#e74c3c',
  3: '#2ecc71'
};

const API_BASE_URL = 'http://127.0.0.1:8000';

// Funzione per convertire URL Deezer in proxy URL
const getProxyImageUrl = (imageUrl) => {
  if (!imageUrl) return null;
  return `${API_BASE_URL}/api/image?url=${encodeURIComponent(imageUrl)}`;
};

function ResultsDisplay({ results, onReset }) {
  const overallMood = results.overall_mood;
  const moodMode = overallMood.mood_mode;
  const moodName = MOOD_NAMES[moodMode];
  const moodEmoji = MOOD_EMOJIS[moodMode];

  return (
    <div className="results-container">
      <div className="results-header">
        <h1 className="results-title">Analisi Completata!</h1>
        <button className="back-button" onClick={onReset}>← Nuova Analisi</button>
      </div>

      <div className="overall-mood-card" style={{ background: `linear-gradient(135deg, ${MOOD_COLORS[moodMode]}f0, ${MOOD_COLORS[moodMode]}e0)` }}>
        <div className="mood-emoji-container">
          <div className="mood-emoji">{moodEmoji}</div>
        </div>
        <div className="mood-info">
          <p className="mood-label">Mood Principale</p>
          <h2 className="mood-name">{moodName}</h2>
          <p className="mood-stats">
            {overallMood.total_tracks} brani analizzati
          </p>
        </div>
      </div>

      <MoodGauge 
        moodDistribution={overallMood.mood_distribution}
        moodNames={MOOD_NAMES}
        moodColors={MOOD_COLORS}
      />

      <div className="recommendations-section">
        <h3 className="section-title">Brani Consigliati per Mood</h3>
        <div className="recommendations-grid">
          {Object.entries(results.similar_songs_by_mood).map(([moodName, rec], idx) => {
            const moodIndex = MOOD_MAPPING[moodName] !== undefined ? MOOD_MAPPING[moodName] : 0;
            
            return (
              <div key={idx} className="recommendation-card" style={{ borderTopColor: MOOD_COLORS[moodIndex] }}>
                <div className="rec-header">
                  <span className="rec-emoji">{MOOD_EMOJIS[moodIndex]}</span>
                  <span className="rec-mood">{MOOD_NAMES[moodIndex]}</span>
                </div>
                {rec.image && (
                  <div className="rec-image-container">
                    <img 
                      src={getProxyImageUrl(rec.image)} 
                      alt={rec.track} 
                      className="rec-image"
                    />
                  </div>
                )}
                <div className="rec-content">
                  {rec.track ? (
                    <>
                      <p className="rec-track">{rec.track}</p>
                      <p className="rec-artist">{rec.artist}</p>
                    </>
                  ) : rec.error ? (
                    <p className="rec-error">{rec.error}</p>
                  ) : (
                    <p className="rec-error">Nessun dato disponibile</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <TracksList tracks={results.tracks} />
    </div>
  );
}

export default ResultsDisplay;
