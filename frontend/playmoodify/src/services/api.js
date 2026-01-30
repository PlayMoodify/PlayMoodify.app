const API_BASE_URL = 'http://127.0.0.1:8000';

export const processPlaylist = async (playlistUrl) => {
  try {
    const response = await fetch(`${API_BASE_URL}/process-playlist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ playlist_url: playlistUrl }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error processing playlist:', error);
    throw error;
  }
};
