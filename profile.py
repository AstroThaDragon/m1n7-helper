import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from easy_pil import Canvas, Editor, Font, load_image_async

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_db_path(self):
        """Fetches the active database path from the Leveling cog or defaults to levels.db."""
        leveling_cog = self.bot.get_cog("Leveling")
        if leveling_cog and hasattr(leveling_cog, "db_path"):
            return leveling_cog.db_path
        return "levels.db"

    def ensure_schema(self, cursor):
        """Ensures all required columns exist in the users table without resetting data."""
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        required_columns = {
            "stardust": "INTEGER DEFAULT 0",
            "bio": "TEXT DEFAULT NULL",
            "profile_card": "TEXT DEFAULT 'default_nebula'"
        }

        for column, column_type in required_columns.items():
            if column not in existing_columns:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column} {column_type}")

    def get_user_profile(self, user_id):
        """Fetches user and pet data from the database and calculates true level from XP."""
        db_path = self.get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Self-heal missing database columns
        self.ensure_schema(cursor)
        conn.commit()

        # Grab main user stats
        cursor.execute("SELECT level, xp, stardust, bio, profile_card FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        # Grab pet data (gracefully handle missing pets table)
        try:
            cursor.execute("SELECT pet_stage FROM pets WHERE user_id = ?", (user_id,))
            pet_data = cursor.fetchone()
        except sqlite3.OperationalError:
            pet_data = None
        
        conn.close()

        # Fallback values if user is not in database yet
        if not user_data:
            return {
                "level": 0, 
                "xp": 0, 
                "stardust": 0, 
                "bio": "Exploring the outer rims of Enceladus Station. 🚀", 
                "bg": "default_nebula", 
                "pet": "egg"
            }

        stored_level, xp, stardust, bio, profile_card = user_data[0], user_data[1], user_data[2] or 0, user_data[3], user_data[4]

        # Calculate true level dynamically from accumulated XP
        leveling_cog = self.bot.get_cog("Leveling")
        calculated_level = stored_level or 0
        if leveling_cog and hasattr(leveling_cog, "get_xp_for_level"):
            temp_level = 0
            while (xp or 0) >= leveling_cog.get_xp_for_level(temp_level + 1):
                temp_level += 1
            calculated_level = temp_level

        final_level = max(stored_level or 0, calculated_level)
            
        return {
            "level": final_level,
            "xp": xp or 0,
            "stardust": stardust,
            "bio": bio or "Exploring the outer rims of Enceladus Station. 🚀",
            "bg": profile_card if profile_card else "default_nebula",
            "pet": pet_data[0] if pet_data else "egg"
        }

    @commands.hybrid_command(name="profile", description="View your cosmic station profile.")
    @app_commands.describe(member="The user whose profile you want to view")
    async def profile(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        await ctx.defer()

        # 1. Fetch user data
        data = self.get_user_profile(target.id)

        # 2. Render Station Viewport (600x300 Environment Window)
        viewport_w, viewport_h = 600, 300
        canvas = Canvas((viewport_w, viewport_h), color="#0B0F19")
        viewport = Editor(canvas)

        bg_name = data['bg']
        if bg_name == "default":
            bg_name = "default_nebula"

        # Load Background Environment
        try:
            bg_image = Editor(f"assets/presets/{bg_name}.png").resize((viewport_w, viewport_h))
            viewport.paste(bg_image, (0, 0))
        except FileNotFoundError:
            viewport.rectangle((0, 0), width=viewport_w, height=viewport_h, fill="#1E2333")

        # Load & Paste Active Companion/Pet Sprite into the environment
        try:
            pet_image = Editor(f"assets/pets/{data['pet']}.png").resize((120, 120))
            viewport.paste(pet_image, (440, 150))
        except FileNotFoundError:
            pass

        # Save canvas to file attachment
        file = discord.File(fp=viewport.image_bytes, filename="viewport.png")

        # 3. Assemble Embed
        embed = discord.Embed(
            title=f"🛸 Personnel Record — {target.display_name}",
            description=f"📜 *{data['bio']}*",
            color=target.color or discord.Color.blue()
        )
        
        # User's avatar in the top-right thumbnail spot
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Native Discord Stat Fields
        embed.add_field(name="⭐ Rank & XP", value=f"Level `{data['level']}` • `{data['xp']:,} XP`", inline=True)
        embed.add_field(name="✨ Stardust", value=f"`{data['stardust']:,}`", inline=True)
        embed.add_field(name="🐉 Companion", value=f"`{data['pet'].capitalize()}`", inline=True)
        
        # Environment Window Image
        embed.set_image(url="attachment://viewport.png")

        await ctx.send(file=file, embed=embed)

    @commands.hybrid_command(name="background", description="Equip an unlocked background voucher for your profile card.")
    @app_commands.describe(background_id="The background style code to equip")
    @app_commands.choices(background_id=[
        app_commands.Choice(name="Default Nebula", value="default"),
        app_commands.Choice(name="Cyberpunk Neon Grid", value="neon_grid"),
        app_commands.Choice(name="Deep Void Galaxy", value="deep_void"),
        app_commands.Choice(name="Solaris Ring System", value="solaris_ring")
    ])
    async def background(self, ctx: commands.Context, background_id: str):
        await ctx.defer()
        user_id = ctx.author.id
        background_id = background_id.lower()

        valid_backgrounds = {
            "default": "Default Nebula",
            "neon_grid": "Cyberpunk Neon Grid",
            "deep_void": "Deep Void Galaxy",
            "solaris_ring": "Solaris Ring System"
        }

        db_path = self.get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        self.ensure_schema(cursor)

        # Check ownership if it's not default
        if background_id != "default":
            try:
                cursor.execute("SELECT 1 FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, background_id))
                has_item = cursor.fetchone()
            except sqlite3.OperationalError:
                has_item = False

            if not has_item:
                conn.close()
                return await ctx.send(f"🔒 **Locked!** You don't own the voucher for `{background_id}` yet. Check the `/shop` or hunt for it while mining!")

        # Update profile card column
        cursor.execute("UPDATE users SET profile_card = ? WHERE user_id = ?", (background_id, user_id))
        conn.commit()
        conn.close()

        await ctx.send(f"🌟 **Profile Updated!** Successfully equipped **{valid_backgrounds.get(background_id, background_id)}** as your active profile background. Run `/profile` to check it out!")

async def setup(bot):
    await bot.add_cog(Profile(bot))