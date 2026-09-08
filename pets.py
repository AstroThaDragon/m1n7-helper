import discord
from discord.ext import commands

class Pets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="pet", description="Check on your galactic companion.")
    async def pet(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🥚 Station Pet Bay",
            description="*The incubator hums quietly. Your cosmic egg is dormant and resting safely.*",
            color=discord.Color.from_rgb(120, 140, 160)
        )
        embed.add_field(
            name="🚧 Status: Work in Progress",
            value="Pet feeding, hatching, and evolution systems are currently under construction by station engineers. Check back soon in a future Enceladus update for full pet interaction features!",
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="feed", description="Feed your station pet.")
    async def feed(self, ctx: commands.Context):
        await ctx.send("🚧 **WIP:** The pet cafeteria dispensers are offline for maintenance. Save your Cosmic Bio-Feed packs. Feeding mechanics will be live in a future Enceladus update!")

async def setup(bot):
    await bot.add_cog(Pets(bot))