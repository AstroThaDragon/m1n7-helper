import discord
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import asyncio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=os.getenv('SPOTIPY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIPY_CLIENT_SECRET')
        ))

    @commands.command(name="join")
    async def join(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                await ctx.voice_client.move_to(channel)
            else:
                await channel.connect()
        else:
            await ctx.send("You need to be in a voice channel first! 🎧")

    @commands.command(name="leave")
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        else:
            await ctx.send("I'm not in a voice channel!")

    @commands.command(name="play")
    async def play(self, ctx, *, search: str):
        if not ctx.voice_client:
            await ctx.invoke(self.join)
            # Give the bot a second to settle into the channel
            await asyncio.sleep(1) 

        query = search
        if "open.spotify.com/track/" in search:
            try:
                track = self.sp.track(search)
                query = f"{track['artists'][0]['name']} - {track['name']}"
            except Exception as e:
                await ctx.send("I couldn't read that Spotify link! Check your API keys.")
                return

        ydl_opts = {'format': 'bestaudio', 'noplaylist': 'True'}
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        
        async with ctx.typing():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
                    url = info['url']
                    title = info['title']
                
                if ctx.voice_client:
                    ctx.voice_client.stop()
                    source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                    ctx.voice_client.play(source)
                    await ctx.send(f"🎶 Now playing: **{title}**")
            except Exception as e:
                await ctx.send(f"Error playing audio: {e}")

async def setup(bot):
    await bot.add_cog(Music(bot))