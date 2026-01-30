import { useState } from 'react';
import './PlaylistForm.css';

function PlaylistForm({ onSubmit, disabled }) {
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [inputError, setInputError] = useState('');

  const handleChange = (e) => {
    setPlaylistUrl(e.target.value);
    setInputError('');
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setPlaylistUrl(text);
      setInputError('');
    } catch (err) {
      setInputError('Errore nel leggere gli appunti');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!playlistUrl.trim()) {
      setInputError('Per favore inserisci un link valido');
      return;
    }

    if (!playlistUrl.includes('spotify.com')) {
      setInputError('Il link deve essere da Spotify');
      return;
    }

    onSubmit(playlistUrl);
  };

  return (
    <form className="playlist-form" onSubmit={handleSubmit}>
      <h1 className="form-title">Analizza la tua Playlist</h1>
      <p className="form-subtitle">Inserisci il link della tua playlist Spotify e scopri i mood</p>
      
      <div className="form-group">
        <div className="input-wrapper">
          <input
            type="text"
            className={`form-input ${inputError ? 'error' : ''}`}
            placeholder="Incolla il link della playlist Spotify..."
            value={playlistUrl}
            onChange={handleChange}
            disabled={disabled}
          />
          <button
            type="button"
            className="paste-button"
            onClick={handlePaste}
            disabled={disabled}
            title="Incolla dal clipboard"
          >
            📋
          </button>
        </div>
        {inputError && <span className="form-error">{inputError}</span>}
      </div>

      <button 
        type="submit" 
        className="form-button"
        disabled={disabled}
      >
        {disabled ? 'Elaborazione in corso...' : 'Analizza Playlist'}
      </button>
    </form>
  );
}

export default PlaylistForm;
