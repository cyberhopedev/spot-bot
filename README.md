# spot-bot

Discord bot to scan spotify links in a channel and add them to a playlist when the user utilizes reactions to confirm, or does not add the song if the user denies the request to add it to the playlist.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![discord.py](https://img.shields.io/badge/discord.py-2.3%2B-5865F2?logo=discord)
![Spotipy](https://img.shields.io/badge/Spotipy-2.23%2B-1DB954?logo=spotify)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- Detects Spotify track links posted in a designated Discord channel
- Fetches the track name, artist(s), and playlist name from the Spotify API
- Posts a confirmation prompt in the channel mentioning the user
- Reacts with ✅ / ❌ — user clicks to confirm or cancel
- Adds the track to your Spotify playlist on confirmation
- Handles pending confirmations, API errors, and invalid links

---

## Environment Variables

| Variable | Description |
|---|---|
| `SPOTIFY_CLIENT_ID` | Client ID from the Spotify Developer Dashboard |
| `SPOTIFY_CLIENT_SECRET` | Client Secret from the Spotify Developer Dashboard |
| `SPOTIFY_REDIRECT_URI` | OAuth callback URI (e.g. `http://127.0.0.1:8888/callback`) |
| `SPOTIFY_PLAYLIST_ID` | ID of the Spotify playlist to add tracks to |
| `DISCORD_TOKEN` | Bot token from the Discord Developer Portal |
| `DISCORD_CHANNEL_ID` | Integer ID of the Discord channel to monitor |

---
 
## Bot Flow
 
1. A user posts a Spotify track link in the monitored channel
2. SpotBot detects the link using a regex pattern
3. The bot fetches the track name, artist, and playlist name from Spotify
4. A confirmation prompt is posted in the channel, mentioning the user
5. The user reacts with ✅ to add the track or ❌ to cancel
6. If the user reacts, the outcome is posted as a follow-up message in the channel
 
---

## Sources

- [discord.py Documentation](https://discordpy.readthedocs.io/en/stable/)
- [Spotipy Documentation](https://spotipy.readthedocs.io/en/2.26.0/)
- [Spotify Developer Dashboard](https://developer.spotify.com/)
- [Discord Developer Portal](https://discord.com/developers/applications)
