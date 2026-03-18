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
import os
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
    pass
    

if __name__ == "__main__":
    main()