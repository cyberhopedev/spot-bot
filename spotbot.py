"""
    Author:  cyberhopedev
    Date:    March 2026

    Program:  SpotBot
    Purpose:  A Discord bot that reads messages from a specific channel. If that message has
    a Spotify link, it posts a confirmation prompt in the channel. The user can react with
    ✅ or ❌ at any time to add or cancel. Pending confirmations are stored in memory.

#== ACKNOWLEDGEMENTS =========================================================
Discord.py documentation: https://discordpy.readthedocs.io/en/stable/
Spotipy documentation: https://spotipy.readthedocs.io/en/2.19.0/
Spotify Developer: https://developer.spotify.com/
Discord Developer: https://discord.com/developers/applications
PyTest documentation: https://pypi.org/project/pytest/ 
#=============================================================================

"""
import re
from urllib.parse import urlparse
import spotipy
import discord
from spotipy.oauth2 import SpotifyOAuth

# Pattern breakdown:
#   https://open\.spotify\.com/track/  — literal URL prefix (. is escaped
#                                         so it matches a dot, not any char)
#   [A-Za-z0-9]+                       — one or more alphanumeric characters
#                                         (the track ID itself)
SPOTIFY_TRACK_PATTERN = re.compile(r"https://open\.spotify\.com/track/[A-Za-z0-9]+")

# Emojis used for adding or not adding the song to the playlist
CONFIRM_EMOJI = "✅"
DENY_EMOJI    = "❌"

class SpotBot(discord.Client):
    """
    A Discord bot that reads messages from a specific channel. If that message has
    a Spotify link, it will add it to a specified Spotify playlist.

    Inherits from discord.Client, which is the base class for all Discord bots in discord.py. 
    By inheriting it, we get all the connection logic for free and just override the event methods we care about.
    """
    def __init__(self, spotify_client_id, spotify_client_secret, spotify_redirect_uri, spotify_playlist_id, discord_token, discord_channel_id):
        """
        Initializes the SpotBot with the necessary credentials and configuration for
        both Spotify and Discord

        Parameter(s):
            spotify_client_id (str): The client ID for the Spotify API.
            spotify_client_secret (str): The client secret for the Spotify API.
            spotify_redirect_uri (str): The redirect URI for the Spotify API.
            spotify_playlist_id (str): The ID of the Spotify playlist to which songs will be added.
            discord_token (str): The token for the Discord bot.
            discord_channel_id (int): The ID of the Discord channel to monitor for messages.
        Returns:
            None
        """
        # Discord intents that communicate which events Spotbot wants
        intents = discord.Intents.default()
        # Ensure that message content and reactions are within the intents
        intents.message_content = True
        intents.reactions = True
        super().__init__(intents=intents)

        # Stores credentials so we can use them later
        self.discord_token = discord_token
        self.discord_channel_id  = discord_channel_id
        self.spotify_playlist_id = spotify_playlist_id

        # Store pending confirmations in a dictionary, entry is deleted once confirmation is recieved
        self.pending = {}

        # Spotify OAuth
        auth_manager = SpotifyOAuth(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret,
            redirect_uri=spotify_redirect_uri,
            scope="playlist-modify-public playlist-modify-private",
        )

        # Create the Spotipy client using the auth manager
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    # =============================================================================
    # Discord event handler methods
    # =============================================================================
    async def on_ready(self):
        """
        Called automatically by discord.py once the bot has finished connecting
        to Discord and is ready to receive events.
        Prints a confirmation message to the console.
        Parameter(s):
            None
        Returns:
            None
        """
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"Monitoring channel ID: {self.discord_channel_id}")

    async def on_message(self, message):
        """
        Discord event handler called automatically every time a message is sent
        in any channel the bot can see. Ignores messages from the bot itself,
        then delegates to on_music_recs_message if the message is in the
        monitored channel.

        Parameter(s):
            message (discord.Message): The Discord message object.
        Returns:
            None
        """
        # If I am the author, ignore me
        if message.author == self.user:
            return
        # Otherwise, if I am in the expected channel run then wait for on_music_recs_message to finish before continuing
        if message.channel.id == self.discord_channel_id:
            await self.on_music_recs_message(message)

    async def on_raw_reaction(self, payload):
        """
        Called every time any reaction is added to any message the bot can see.
        Checks whether the reaction is on a tracked confirmation prompt, from
        the correct user, and with a valid emoji. If all checks pass, removes
        the entry from self.pending and either adds the track or cancels.

        Parameter(s):
            payload (discord.RawReactionActionEvent): Contains message_id,
                user_id, emoji, channel_id, and guild_id.
        Returns:
            None
        Raises:
            spotipy.SpotifyException: If the Spotify API call to add the track fails.
        """
        # Lookup tracks that are pending confirmation, if not stop here
        if payload.message_id not in self.pending:
            return
        # Ignore the bot's own reactions
        if payload.user_id == self.user.id:
            return
        # Now get the entry and ensure only ✅ and ❌ emoji, otherwise return
        entry = self.pending[payload.message_id]
        emoji = str(payload.emoji)
        if emoji not in (CONFIRM_EMOJI, DENY_EMOJI):
            return

        # Passed all conditions, we can delete it from pending
        del self.pending[payload.message_id]
        # Get the channel ID so we know where to send the follow-up confirmation msg
        channel = self.get_channel(payload.channel_id)
        
        # Handle the user's choice for this track
        if emoji == CONFIRM_EMOJI:
            # Try to add the track to the playlist.
            try:
                self.add_song_to_playlist(entry["song_url"])
                await channel.send(
                    f'✅ **{entry["track_name"]}** — {entry["artist_names"]} '
                    f'has been added to **{entry["playlist_name"]}**!'
                )
                print(f'Added to playlist: {entry["track_name"]} ({entry["song_url"]})')
            except Exception as e:
                # The Spotify API call failed — notify the channel and log the error.
                await channel.send(
                    f'❌ Something went wrong adding **{entry["track_name"]}** '
                    f'to **{entry["playlist_name"]}**. Please try again.'
                )
                print(f'Failed to add track {entry["song_url"]}: {e}')
        else:
            # Do nothing and let the channel know.
            await channel.send(
                f'❌ Got it, **{entry["track_name"]}** was **not** added '
                f'to **{entry["playlist_name"]}**.'
            )
            print(f'User declined to add: {entry["track_name"]} ({entry["song_url"]})')

    async def on_music_recs_message(self, message):
        """
        Called when a message is posted in the monitored channel (music-recs).

        If the message contains a Spotify track URL, retrieves the track's name
        and artist from Spotify and sends a message in the same channel asking
        the user to confirm adding it to the playlist by reacting with ✅ or ❌.

        Waits up to REACTION_TIMEOUT seconds for a reaction. If the user reacts
        with ✅ the track is added and a follow-up channel message is sent. If the
        user reacts with ❌ or the timeout expires, a cancellation message is sent.

        Parameter(s):
            message (discord.Message): The Discord message object to inspect.
        Returns:
            None
        Raises:
            spotipy.SpotifyException: If the Spotify API call fails.
        """
        # Find the track pattern using regex
        match = SPOTIFY_TRACK_PATTERN.search(message.content)
        if not match:
            return # No Spotify link found, stop here
        
        # Get the full text that matched the pattern, AKA complete Spotify track URL, then get just the track ID
        song_url = match.group(0)
        track_id = self.get_song_id_from_url

        # Fetch the track and playlist info from Spotify
        try:
            # Extract the name and list of artists
            track_info = self.sp.track(track_id)
            track_name = track_info["name"]

            # Extract the artist names into a comma list
            artist_names = ", ".join(a["name"] for a in track_info["artists"])

            # Fetch metadata about the target playlist
            playlist_info = self.sp.playlist(self.spotify_playlist_id, fields="name")
            playlist_name = playlist_info["name"]
        except Exception as e:
            # An error occured :(, print an error to console and post a message to channel
            print(f"Failed to fetch track/playlist info: {e}")
            await message.channel.send(
                "⚠️ SpotBot couldn't retrieve that track's details from Spotify. "
                "Please check the link and try again."
            )
            return
        
        # Post the confirmation prompt in the channel
        prompt = await message.channel.send(
            f'{message.author.mention} 🎵 **{track_name}** — {artist_names}\n\n'
            f'Would you like to add this to **{playlist_name}**?\n\n'
            f'React with {CONFIRM_EMOJI} to add it, or {DENY_EMOJI} to cancel.'
        )
        # Pre-add reactions
        await prompt.add_reaction(CONFIRM_EMOJI)
        await prompt.add_reaction(DENY_EMOJI)

        # Store the pending confirmation so it can be added/denied whenever a choice is made
        self.pending[prompt.id] = {
            "song_url":      song_url,
            "track_name":    track_name,
            "artist_names":  artist_names,
            "playlist_name": playlist_name,
            "author_id":     message.author.id,
            "channel_id":    message.channel.id,
        }

    # =============================================================================
    # Helper methods
    # =============================================================================
    def add_song_to_playlist(self, song_url):
        """
        Extracts the Spotify track ID from the given URL and appends the track to
        the configured Spotify playlist using the Spotipy client.

        Parameter(s):
            song_url (str): A full Spotify track URL, e.g.
            'https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC'
        Returns:
            None
        Raises:
            ValueError: If the URL does not contain a valid Spotify track ID.
            spotipy.SpotifyException: If the Spotify API call to add the track fails.
        """
        # Get the track ID from the URL
        track_id = self.get_song_id_from_url(song_url)

        # Add the track to the target playlist stored in __init__
        self.sp.playlist_add_items(self.spotify_playlist_id, [track_id])

    def get_song_id_from_url(self, song_url):
        """
        Parses a Spotify track URL and returns the track ID component.

        Spotify track URLs follow the pattern:
        https://open.spotify.com/track/<track_id>[?si=...]
        This method extracts and returns the <track_id> portion, stripping any
        query parameters.

        Parameter(s):
            song_url (str): A full Spotify track URL.
        Returns:
            str: The Spotify track ID extracted from the URL.
        Raises:
            ValueError: If the URL is not a recognizable Spotify track URL.
        """
        return self._extract_id_from_url(song_url, "track")

    def get_playlist_id_from_url(self, playlist_url):
        """
        Parses a Spotify playlist URL and returns the playlist ID component.

        Spotify playlist URLs follow the pattern:
            https://open.spotify.com/playlist/<playlist_id>[?si=...]

        Parameter(s):
            playlist_url (str): A full Spotify playlist URL.
        Returns:
            str: The Spotify playlist ID extracted from the URL.
        Raises:
            ValueError: If the URL is not a recognizable Spotify playlist URL.
        """
        return self._extract_id_from_url(playlist_url, "playlist")

    def get_user_id_from_url(self, user_url):
        """
        Parses a Spotify user profile URL and returns the user ID component.

        Spotify user URLs follow the pattern:
            https://open.spotify.com/user/<user_id>

        Parameter(s):
            user_url (str): A full Spotify user profile URL.
        Returns:
            str: The Spotify user ID extracted from the URL.
        Raises:
            ValueError: If the URL is not a recognizable Spotify user URL.
        """
        return self._extract_id_from_url(user_url, "user")

    def _extract_id_from_url(self, url, resource_type):
        """
        Shared helper that parses any Spotify URL and extracts the ID for the
        given resource type. The leading underscore in the name is a Python
        convention indicating this is an internal method not intended to be
        called from outside the class.

        Parameter(s):
            url (str): A full Spotify URL.
            resource_type (str): One of 'track', 'playlist', or 'user'.
        Returns:
            str: The extracted Spotify resource ID.
        Raises:
            ValueError: If the URL structure does not match the expected pattern.
        """
        parsed_url = urlparse(url)
        tokens = parsed_url.path.strip("/").split("/")

        # Check that the path has at least two segments and the first matches the expected type of track/playlist/user/etc.
        if len(tokens) >= 2 and tokens[0] == resource_type:
            return tokens[1]
        # Otherwise, if it doesn't, raise a ValueError
        raise ValueError(f"Could not extract {resource_type} ID from URL: {url}")