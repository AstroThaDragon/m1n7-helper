import discord
from discord.ext import commands
import sqlite3
from easypil import Canvas, Editor, Font

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_user_profile(self, user_id):
        """Fetches user and pet data from the database."""
        conn = sqlite3.connect("levels.db")
        cursor = conn.cursor()
        
        # Grab main user stats
        cursor.execute("SELECT level, xp, stardust, bio, active_background FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        # Grab pet data
        cursor.execute("SELECT pet_stage FROM pets WHERE user_id = ?", (user_id,))
        pet_data = cursor.fetchone()
        
        conn.close()

        # If user isn't in the database yet, return default placeholder values
        if not user_data:
            return {"level": 1, "xp": 0, "stardust": 0, "bio": "Exploring the outer rims of Enceladus Station. 🚀", "bg": "default_nebula", "pet": "egg"}
            
        return {
            "level": user_data[0],
            "xp": user_data[1],
            "stardust": user_data[2],
            "bio": user_data[3],
            "bg": user_data[4] if user_data[4] else "default_nebula",
            "pet": pet_data[0] if pet_data else "egg"
        }

    @commands.hybrid_group(name="profile", description="Manage your station profile and card appearance.")
    async def profile(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            # Fallback if someone just runs /profile: default to viewing their own card
            await ctx.invoke(self.profile_view, member=ctx.author)

    @profile.command(name="view", description="View your cosmic station profile and pet.")
    @commands.describe(member="The user whose profile you want to view")
    async def profile_view(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        await ctx.defer() # Defers the interaction so it doesn't timeout while rendering

        # 1. Fetch data
        data = self.get_user_profile(target.id)

        # 2. Setup the EasyPIL Canvas (930x400)
        canvas = Canvas((930, 400), color="#141722") # Dark space base color
        background = Editor(canvas)

        # -- TOP SECTION: Rank Card Area (0 to 250) --
        bg_name = data['bg']
        if bg_name == "default":
            bg_name = "default_nebula"

        try:
            bg_image = Editor(f"assets/presets/{bg_name}.png").resize((930, 250))
            background.paste(bg_image, (0, 0))
        except FileNotFoundError:
            background.rectangle((0, 0, 930, 250), color="#1E2333") 
        
        # Avatar (Top Left)
        avatar_image = await target.display_avatar.read()
        avatar = Editor(avatar_image).resize((150, 150)).circle_image()
        background.paste(avatar, (50, 50))

        # Basic Stats (Level & XP)
        font_large = Font.poppins(size=40, variant="bold")
        font_small = Font.poppins(size=25, variant="regular")
        
        background.text((230, 60), f"{target.display_name}", font=font_large, color="white")
        background.text((230, 120), f"Level: {data['level']}  |  XP: {data['xp']}", font=font_small, color="#A0A5B5")

        # -- LOWER DECK: Profile Data (250 to 400) --
        # Dark panel overlay for the lower section
        background.rectangle((20, 260, 890, 120), color="#0B0F19", radius=15)
        
        # Stardust Balance & Bio
        background.text((40, 280), f"✨ Stardust: {data['stardust']}", font=font_small, color="#00E5FF")
        background.text((40, 330), f"📜 {data['bio']}", font=font_small, color="white")

        # Pet Sprite (Bottom Right)
        try:
            pet_image = Editor(f"assets/pets/{data['pet']}.png").resize((90, 90))
            background.paste(pet_image, (790, 275))
        except FileNotFoundError:
            pass # Skips drawing the pet if the image file doesn't exist yet

        # 3. Send to Discord
        file = discord.File(fp=background.image_bytes, filename="profile.png")
        embed = discord.Embed(color=target.color)
        embed.set_image(url="attachment://profile.png")
        
        await ctx.send(file=file, embed=embed)

    @profile.command(name="background", description="Equip an unlocked background voucher for your profile card.")
    @discord.app_commands.describe(background_id="The background style code to equip")
    @discord.app_commands.choices(background_id=[
        discord.app_commands.Choice(name="Default Nebula", value="default"),
        discord.app_commands.Choice(name="Cyberpunk Neon Grid", value="neon_grid"),
        discord.app_commands.Choice(name="Deep Void Galaxy", value="deep_void"),
        discord.app_commands.Choice(name="Solaris Ring System", value="solaris_ring")
    ])
    async def profile_background(self, ctx: commands.Context, background_id: str):
        await ctx.defer()
        user_id = ctx.author.id
        background_id = background_id.lower()

        valid_backgrounds = {
            "default": "Default Nebula",
            "neon_grid": "Cyberpunk Neon Grid",
            "deep_void": "Deep Void Galaxy",
            "solaris_ring": "Solaris Ring System"
        }

        conn = sqlite3.connect("levels.db")
        cursor = conn.cursor()

        # Check ownership if it's not the default
        if background_id != "default":
            cursor.execute("SELECT 1 FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, background_id))
            if not cursor.fetchone():
                conn.close()
                return await ctx.send(f"🔒 **Locked!** You don't own the voucher for `{background_id}` yet. Check the `/shop` or hunt for it while mining!")

        # Update active background
        cursor.execute("UPDATE users SET active_background = ? WHERE user_id = ?", (background_id, user_id))
        conn.commit()
        conn.close()

        await ctx.send(f"🌟 **Profile Updated!** Successfully equipped **{valid_backgrounds.get(background_id, background_id)}** as your active profile background. Run `/profile view` to check it out!")

async def setup(bot):
    await bot.add_cog(Profile(bot))