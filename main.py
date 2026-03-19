"""
    Author:  cyberhopedev
    Date:    March 2026

    Program:  SpotBot (Entry Point)
    Purpose:  Loads credentials from the environment and starts the SpotBot.

#== ACKNOWLEDGEMENTS =========================================================
Discord.py documentation: https://discordpy.readthedocs.io/en/stable/
Spotipy documentation: https://spotipy.readthedocs.io/en/2.19.0/
Spotify Developer: https://developer.spotify.com/
Discord Developer: https://discord.com/developers/applications
PyTest documentation: https://pypi.org/project/pytest/ 
#=============================================================================

"""
import os, sys
from dotenv import load_dotenv
from spotbot import SpotBot

def main():
    """
    Entry point for the SpotBot application. Reads credentials and configuration
    from environment variables (or a .env file), instantiates a SpotBot, and
    starts the Discord event loop by calling bot.run().

    Expected environment variables:
        SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI,
        SPOTIFY_PLAYLIST_ID, DISCORD_TOKEN, DISCORD_CHANNEL_ID
    Returns:
        None
    """
    # Load the environment
    load_dotenv()
    
    # Make sure all of the variables needed for the bot exists
    required_variables = [
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "SPOTIFY_REDIRECT_URI",
        "SPOTIFY_PLAYLIST_ID",
        "DISCORD_TOKEN",
        "DISCORD_CHANNEL_ID",
    ]
    missing = [variable for variable in required_variables if not os.getenv(variable)]
    # If any are missing, print error message to console and exit immediately with an error
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        print("Make sure your .env file is present and contains all required values.")
        sys.exit(1)

    # Initialize the bot with the now loaded credentials
    bot = SpotBot(
        spotify_client_id     = os.getenv("SPOTIFY_CLIENT_ID"),
        spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET"),
        spotify_redirect_uri  = os.getenv("SPOTIFY_REDIRECT_URI"),
        spotify_playlist_id   = os.getenv("SPOTIFY_PLAYLIST_ID"),
        discord_token         = os.getenv("DISCORD_TOKEN"),
        discord_channel_id    = int(os.getenv("DISCORD_CHANNEL_ID")),
    )

    # Start the bot using discord token
    bot.run(bot.discord_token)

if __name__ == "__main__":
    main()