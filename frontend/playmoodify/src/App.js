import { useState } from 'react';
import logo from './assets/PlayMoodify3.png';
import './App.css';
import { processPlaylist } from './services/api';
import PlaylistForm from './components/PlaylistForm';
import ResultsDisplay from './components/ResultsDisplay';
import LoadingSpinner from './components/LoadingSpinner';

function App() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handlePlaylistSubmit = async (playlistUrl) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const data = await processPlaylist(playlistUrl);
      
      if (data.status === 'success') {
        setResults(data);
      } else {
        setError(data.error || 'Errore sconosciuto');
      }
    } catch (err) {
      setError(err.message || 'Errore nel processing della playlist');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResults(null);
    setError(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="PlayMoodify Logo" />
      </header>

      <main className="App-main">
        {!results ? (
          <>
            <PlaylistForm onSubmit={handlePlaylistSubmit} disabled={loading} />
            {loading && <LoadingSpinner />}
            {error && <div className="error-message">{error}</div>}
          </>
        ) : (
          <>
            <ResultsDisplay results={results} onReset={handleReset} />
          </>
        )}
      </main>
    </div>
  );
}

export default App;
