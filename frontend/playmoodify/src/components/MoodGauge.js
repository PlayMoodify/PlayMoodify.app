import { useState, useEffect } from 'react';
import './MoodGauge.css';

const MOOD_EMOJIS = {
  0: '😔',
  1: '😊',
  2: '🔥',
  3: '😌'
};

const MOOD_NAMES_MAP = {
  0: 'Triste',
  1: 'Felice',
  2: 'Energico',
  3: 'Calmo'
};

function GaugeMeter({ mood, percentage, color }) {
  const [displayPercentage, setDisplayPercentage] = useState(0);

  // Anima il numero della percentuale da 0 a percentage
  useEffect(() => {
    let animationFrame;
    let currentValue = 0;
    const targetValue = percentage;
    const duration = 2500; // millisecondi - aumentato a 2.5 secondi
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing cubica
      const easeProgress = progress < 0.5 
        ? 4 * progress * progress * progress 
        : 1 - Math.pow(-2 * progress + 2, 3) / 2;
      
      currentValue = Math.round(targetValue * easeProgress);
      setDisplayPercentage(currentValue);

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animationFrame);
  }, [percentage]);

  // Lunghezza dell'arco: circonferenza = 2πr, qui r=80
  // Arco semicircolare = π*80 ≈ 251.33
  const arcLength = 251.33;
  const filledLength = (displayPercentage / 100) * arcLength;

  return (
    <div className="gauge-meter">
      <svg 
        className="gauge-svg" 
        viewBox="0 0 200 120"
      >
        {/* Sfondo arco grigio completo */}
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth="18"
          strokeLinecap="round"
        />

        {/* Arco colorato fino alla percentuale */}
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke={color}
          strokeWidth="18"
          strokeLinecap="round"
          strokeDasharray={`${filledLength} ${arcLength}`}
          opacity="0.9"
        />
      </svg>
      
      <div className="meter-info">
        <span className="meter-emoji">{MOOD_EMOJIS[mood]}</span>
        <span className="meter-percentage">{displayPercentage}%</span>
      </div>
    </div>
  );
}

function MoodGauge({ moodDistribution, moodNames, moodColors }) {
  const data = [0, 1, 2, 3].map((moodId) => ({
    id: moodId,
    name: MOOD_NAMES_MAP[moodId],
    percentage: Math.round((moodDistribution[moodId] || 0) * 100),
    color: moodColors[moodId]
  }));

  return (
    <div className="mood-gauge-container">
      <h3 className="chart-title">Distribuzione Mood</h3>
      
      <div className="gauges-grid">
        {data.map((item) => (
          <div key={item.id} className="gauge-item">
            <GaugeMeter 
              mood={item.id}
              percentage={item.percentage}
              color={item.color}
            />
            <p className="gauge-label">{item.name}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default MoodGauge;
