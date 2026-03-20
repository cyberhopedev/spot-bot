"""
    Author:  cyberhopedev
    Date:    March 2026

    Program:  SpotBot (Local Tests)
    Purpose:  Tests the functionality of SpotBot by using mock API tests.

#== ACKNOWLEDGEMENTS =========================================================
Discord.py documentation: https://discordpy.readthedocs.io/en/stable/
Spotipy documentation: https://spotipy.readthedocs.io/en/2.19.0/
Spotify Developer: https://developer.spotify.com/
Discord Developer: https://discord.com/developers/applications
PyTest documentation: https://pypi.org/project/pytest/ 
#==============================================================================

"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def bot():
    """
    Creates a SpotBot instance with all external clients mocked out so no
    real network calls are made during tests.
    """

    #  patch() replaces the named object for the duration of the 'with' block
    with patch("spotbot.SpotifyOAuth"), patch("spotbot.spotipy.Spotify"):
        from spotbot import SpotBot

        instance = SpotBot(
            spotify_client_id     = "fake_id",
            spotify_client_secret = "fake_secret",
            spotify_redirect_uri  = "http://localhost:8888/callback",
            spotify_playlist_id   = "fake_playlist_id",
            discord_token         = "fake_discord_token",
            discord_channel_id    = 123456789,
        )

        # Replace self.sp with a plain MagicMock so every Spotify API call returns a controllable fake value
        instance.sp = MagicMock()
        return instance
    
@pytest.fixture
def mock_message():
    """
    Builds a fake discord.Message object with the attributes SpotBot reads:
      - content       : the text of the message
      - author        : the user who sent it (has .mention for the @ping)
      - channel       : the channel it was sent in (has an async .send())
      - channel.id    : set to match the bot's monitored channel ID

    All send/async operations are AsyncMock so they can be awaited in tests.
    """
    message = MagicMock()

    # channel.id must match bot.discord_channel_id (123456789) for on_message to forward the message to on_music_recs_message
    message.channel.id   = 123456789

    # channel.send is async — it needs AsyncMock so it can be awaited and so we can inspect calls to it with .assert_called() etc
    message.channel.send = AsyncMock()

    # author.mention is what Discord uses for @username pings in messages
    message.author.mention = "@testuser"

    return message

def make_payload(message_id, user_id, emoji, channel_id=123456789):
    """
    Helper that builds a fake discord.RawReactionActionEvent payload.

    on_raw_reaction_add receives a payload object rather than full discord
    objects, so we need to simulate it in tests.

    Parameter(s):
        message_id (int): ID of the message that was reacted to.
        user_id    (int): ID of the user who reacted.
        emoji      (str): The emoji string, e.g. '✅' or '❌'.
        channel_id (int): ID of the channel containing the message.
    Returns:
        MagicMock: A fake payload with the expected attributes.
    """
    payload            = MagicMock()
    payload.message_id = message_id
    payload.user_id    = user_id
    payload.channel_id = channel_id

    # payload.emoji is a PartialEmoji object — str() on it returns the emoji
    # character. We set the name attribute and make str() return the emoji.
    payload.emoji      = MagicMock()
    payload.emoji.__str__ = lambda self: emoji

    return payload

# =============================================================================
# URL Parsing Tests
# =============================================================================
def test_get_song_id_from_url(bot):
    """
    Test getting the song ID from the URL
    """
    # Test with query params
    url = "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC?si=abc123"
    assert bot.get_song_id_from_url(url) == "4uLU6hMCjMI75M1A2tKUQC"

    # Test without query params
    url = "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"
    assert bot.get_song_id_from_url(url) == "4uLU6hMCjMI75M1A2tKUQC"

def test_get_playlist_id_from_url(bot):
    """
    Test getting the playlist ID from the URL
    """
    url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
    assert bot.get_playlist_id_from_url(url) == "37i9dQZF1DXcBWIGoYBM5M"

def test_get_user_id_from_url(bot):
    """
    Test getting the user ID from the URL
    """
    url = "https://open.spotify.com/user/spotifyuser123"
    assert bot.get_user_id_from_url(url) == "spotifyuser123"

def test_get_song_id_invalid_url_raises(bot):
    """
    Test getting the song ID from an invalid URL
    """
    # Incorrect resource type
    with pytest.raises(ValueError):
        bot.get_song_id_from_url("https://open.spotify.com/playlist/wrongtype")
        
    # General incorrect URL
    with pytest.raises(ValueError):
        bot.get_song_id_from_url("https://not-spotify.com/something/abc123")

# =============================================================================
# add_song_to_playlist Tests
# =============================================================================
def test_add_song_to_playlist_calls_api(bot):
    """
    Test adding the song to the correct playlist initialized in __init__
    """
    # Add the song
    bot.add_song_to_playlist("https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC")

    # Make sure the expected playlist was called when adding
    bot.sp.playlist_add_items.assert_called_once_with(
        "fake_playlist_id", ["4uLU6hMCjMI75M1A2tKUQC"]
    )

# =============================================================================
# on_music_recs_message Tests
# =============================================================================
@pytest.mark.asyncio
async def test_spotify_link_sends_confirmation(bot, mock_message):
    """
    Tests valid Spotify track link triggers a confirmation prompt in the
    channel that mentions the user and includes both emoji reactions.
    """
    mock_message.content = "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"

    # Configure the fake Spotify API to return believable track/playlist data.
    # return_value sets what the mock returns when called.
    bot.sp.track.return_value = {
        "name": "Creep",
        "artists": [{"name": "Radiohead"}]
    }
    bot.sp.playlist.return_value = {"name": "My Playlist"}

    # Build a fake prompt message that channel.send() will return.
    prompt = MagicMock()
    prompt.id = 999
    prompt.add_reaction = AsyncMock()
    mock_message.channel.send = AsyncMock(return_value=prompt)

    await bot.on_music_recs_message(mock_message)

    # channel.send should have been called once for the prompt.
    mock_message.channel.send.assert_called_once()

    # The prompt text should @mention the user.
    prompt_text = mock_message.channel.send.call_args.args[0]
    assert "@testuser" in prompt_text

    # Both ✅ and ❌ must have been added as reactions so the user can click them.
    reaction_calls = [call.args[0] for call in prompt.add_reaction.call_args_list]
    assert "✅" in reaction_calls
    assert "❌" in reaction_calls

    # The prompt ID should now be in self.pending with the correct metadata.
    assert 999 in bot.pending
    assert bot.pending[999]["song_url"] == "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"
    assert bot.pending[999]["track_name"] == "Creep"
    assert bot.pending[999]["author_id"] == mock_message.author.id


@pytest.mark.asyncio
async def test_non_spotify_message_is_ignored(bot, mock_message):
    """
    Test using a normal Discord message, messages without a Spotify link 
    should do nothing.
    """
    mock_message.content = "theyre my fav emo band rn"
    await bot.on_music_recs_message(mock_message)

    # Bot should not send anything in this case
    mock_message.channel.send.assert_not_called()

# =============================================================================
# on_raw_reaction_add Tests
# =============================================================================
def seed_pending(bot, prompt_id=999, channel_id=123456789):
    """
    Helper that inserts a fake pending entry into bot.pending so tests
    don't need to go through on_music_recs_message first.

    Parameter(s):
        bot        : The SpotBot fixture instance.
        prompt_id  : The fake prompt message ID to key the entry on.
        author_id  : The Discord user ID of the original poster.
        channel_id : The Discord channel ID where the prompt lives.
    """
    bot.pending[prompt_id] = {
        "song_url":      "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC",
        "track_name":    "Creep",
        "artist_names":  "Radiohead",
        "playlist_name": "My Playlist",
        "author_id":    111,
        "channel_id":    channel_id,
    }

@pytest.mark.asyncio
async def test_confirm_reaction_adds_song_and_notifies_channel(bot, mock_message):
    """
    Tests that when reacting with  ✅ should add the track to the playlist and send a
    success message in the channel.
    """
    seed_pending(bot, prompt_id=999)

    bot.user = MagicMock()
    bot.user.id = 999999

    # Build a fake channel object so we can inspect what was sent.
    channel = MagicMock()
    channel.send = AsyncMock()
    bot.get_channel = MagicMock(return_value=channel)

    payload = make_payload(message_id=999, user_id=111, emoji="✅")

    await bot.on_raw_reaction_add(payload)

    # The Spotify API must have been called to add the track.
    bot.sp.playlist_add_items.assert_called_once_with(
        "fake_playlist_id", ["4uLU6hMCjMI75M1A2tKUQC"]
    )

    # A success message should have been sent to the channel.
    channel.send.assert_called_once()
    success_text = channel.send.call_args.args[0]
    assert "✅" in success_text
    assert "Creep" in success_text
    assert "My Playlist" in success_text

    # The entry must be removed from pending so it can't fire again.
    assert 999 not in bot.pending

@pytest.mark.asyncio
async def test_deny_reaction_does_not_add_song(bot, mock_message):
    """
    Tests that when reacting with ❌ the track should NOT be added to the playlist and should
    send a cancellation message in the channel.
    """
    seed_pending(bot, prompt_id=999)

    bot.user = MagicMock()
    bot.user.id = 999999

    channel = MagicMock()
    channel.send = AsyncMock()
    bot.get_channel = MagicMock(return_value=channel)

    payload = make_payload(message_id=999, user_id=111, emoji="❌")

    await bot.on_raw_reaction_add(payload)

    # The Spotify add API must never have been called.
    bot.sp.playlist_add_items.assert_not_called()

    # A cancellation message should have been sent.
    channel.send.assert_called_once()
    cancel_text = channel.send.call_args.args[0]
    assert "❌" in cancel_text
    assert "Creep" in cancel_text

    # Entry must be removed from pending.
    assert 999 not in bot.pending

@pytest.mark.asyncio
async def test_bot_own_reaction_is_ignored(bot):
    """
    The bot reacts with ✅ and ❌ itself when posting a prompt.
    Those self-reactions must not trigger a confirmation.
    """
    seed_pending(bot, prompt_id=999)

    # Set the bot's own user ID and react as the bot.
    bot.user = MagicMock()
    bot.user.id = 999999  # bot's own ID
    payload = make_payload(message_id=999, user_id=999999, emoji="✅")
    bot.get_channel = MagicMock()

    await bot.on_raw_reaction_add(payload)

    # The pending entry should still be there — bot reactions are ignored.
    assert 999 in bot.pending
    bot.get_channel.assert_not_called()

@pytest.mark.asyncio
async def test_unknown_emoji_is_ignored(bot):
    """
    A reaction with an emoji other than ✅ or ❌ should be silently ignored.
    The entry should remain in pending untouched.
    """
    seed_pending(bot, prompt_id=999)

    bot.user = MagicMock()
    bot.user.id = 999999

    payload = make_payload(message_id=999, user_id=111, emoji="🎵")
    bot.get_channel = MagicMock()

    await bot.on_raw_reaction_add(payload)

    # Entry should still be in pending, unrecognised emoji is ignored.
    assert 999 in bot.pending
    bot.get_channel.assert_not_called()

@pytest.mark.asyncio
async def test_reaction_from_any_user_is_accepted(bot):
    """
    Any user in the channel can confirm or cancel — not just the original poster.
    A ✅ from a different user (222, not the poster 111) should still add the track.
    """
    seed_pending(bot, prompt_id=999)

    bot.user = MagicMock()
    bot.user.id = 999999

    channel = MagicMock()
    channel.send = AsyncMock()
    bot.get_channel = MagicMock(return_value=channel)

    # React as a different user (222) — should still be accepted.
    payload = make_payload(message_id=999, user_id=222, emoji="✅")

    await bot.on_raw_reaction_add(payload)

    # Track should have been added even though user 222 didn't post the link.
    bot.sp.playlist_add_items.assert_called_once_with(
        "fake_playlist_id", ["4uLU6hMCjMI75M1A2tKUQC"]
    )
    assert 999 not in bot.pending


@pytest.mark.asyncio
async def test_confirm_reaction_cannot_fire_twice(bot):
    """
    Once a ✅ reaction is handled and the entry is removed from pending,
    a second ✅ reaction on the same message should do nothing — the track
    should not be added a second time.
    """
    seed_pending(bot, prompt_id=999, author_id=111)

    bot.user = MagicMock()
    bot.user.id = 999999

    channel = MagicMock()
    channel.send = AsyncMock()
    bot.get_channel = MagicMock(return_value=channel)

    payload = make_payload(message_id=999, user_id=111, emoji="✅")

    # First reaction, should add the track.
    await bot.on_raw_reaction_add(payload)
    assert bot.sp.playlist_add_items.call_count == 1

    # Second reaction on the same message, should be ignored entirely.
    await bot.on_raw_reaction_add(payload)
    assert bot.sp.playlist_add_items.call_count == 1  # still 1, not 2

@pytest.mark.asyncio
async def test_reaction_on_untracked_message_is_ignored(bot):
    """
    A reaction on a message ID not in self.pending should be silently ignored.
    No channel send should occur and pending should remain unchanged.
    """
    seed_pending(bot, prompt_id=999)

    # React on a completely different message ID.
    payload = make_payload(message_id=000, user_id=111, emoji="✅")
    bot.get_channel = MagicMock()

    await bot.on_raw_reaction_add(payload)

    # The channel should never have been fetched or messaged.
    bot.get_channel.assert_not_called()

    # The original pending entry should still be there — we didn't touch it.
    assert 999 in bot.pending

@pytest.mark.asyncio
async def test_spotify_api_error_sends_channel_error_message(bot, mock_message):
    """
    Tests that if the Spotify API fails when fetching track info, an error message
    should be posted in the channel and no prompt should be sent.
    """
    # Initialize the mock Discord message
    mock_message.content = "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC i love this sm"

    # Force an exception to simulate an actual Spotify API failute
    bot.sp.track.side_effect = Exception("Spotify API error occured")
    await bot.on_music_recs_message(mock_message)

    # Only the error message should have been called with no prompt to add to a playlist
    mock_message.channel.send.assert_called_once()
    error_message = mock_message.channel.send.call_args.args[0]
    assert "⚠️" in error_message
    bot.sp.playlist_add_items.assert_not_called()

    # Nothing should have been added to pending.
    assert len(bot.pending) == 0

@pytest.mark.asyncio
async def test_spotify_api_error_on_confirm_sends_error(bot):
    """
    If the Spotify API fails when adding a track after ✅ is reacted,
    an error message should be sent to the channel and pending should
    still be cleared.
    """
    seed_pending(bot, prompt_id=999, author_id=111)

    bot.user = MagicMock()
    bot.user.id = 999999

    channel = MagicMock()
    channel.send = AsyncMock()
    bot.get_channel = MagicMock(return_value=channel)

    # Make playlist_add_items fail to simulate an API error at add time.
    bot.sp.playlist_add_items.side_effect = Exception("API error")

    payload = make_payload(message_id=999, user_id=111, emoji="✅")

    await bot.on_raw_reaction_add(payload)

    # An error message should have been sent to the channel.
    channel.send.assert_called_once()
    error_text = channel.send.call_args.args[0]
    assert "❌" in error_text

    # Entry should still be removed from pending even though the API failed.
    assert 999 not in bot.pending
