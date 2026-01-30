import vinyle from '../assets/vinilePlayMoodify.png';
import './LoadingSpinner.css';

function LoadingSpinner() {
  return (
    <div className="loading-container">
      <img src={vinyle} alt="Loading" className="vinyl-spinner" />
      <p className="loading-text">Analizzando la playlist...</p>
    </div>
  );
}

export default LoadingSpinner;
