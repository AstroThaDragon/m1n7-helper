import discord
from discord.ext import commands
import sqlite3

# Master Item Registry used across inventory, shop, and exploration
ITEM_REGISTRY = {
    # Currencies & Consumables
    "fuel_refill": {"name": "Emergency Fuel Cell (5 Charges)", "emoji": "⚡", "type": "Consumable", "desc": "Instantly refills your starship mining laser back to 5/5 charges."},
    "pet_snack": {"name": "Cosmic Bio-Feed", "emoji": "🧬", "type": "Consumable", "desc": "Nutrient pack for your station pet."},
    "arcade_token": {"name": "Arcade Token", "emoji": "🪙", "type": "Currency", "desc": "Shiny token for future station mini-games."},

    # Space Junk
    "space_pizza": {"name": "Dehydrated Space Pizza", "emoji": "🍕", "type": "Space Junk", "desc": "Slightly freezer-burned."},
    "floppy_disk": {"name": "Ancient Alien Floppy Disk", "emoji": "💾", "type": "Space Junk", "desc": "Contains mysterious code. Highly ancient tbh."},
    "meteorite": {"name": "Suspiciously Warm Meteorite Chunk", "emoji": "🪨", "type": "Space Junk", "desc": "Emits a faint ambient heat."},
    "rubber_duck": {"name": "Rubber Duck in a Micro-Spacesuit", "emoji": "🐤", "type": "Space Junk", "desc": "Ready for zero-gravity bath time."},
    
    # Background Vouchers
    "neon_grid": {"name": "Background Voucher: Neon Grid", "emoji": "🌆", "type": "Voucher", "desc": "Unlocks the Cyberpunk Neon Grid profile card."},
    "deep_void": {"name": "Background Voucher: Deep Void", "emoji": "🌌", "type": "Voucher", "desc": "Unlocks the Deep Void galaxy profile card."},
    "solaris_ring": {"name": "Background Voucher: Solaris Ring", "emoji": "☀️", "type": "Voucher", "desc": "Unlocks the Solaris Ring star system profile card."}
}

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="inventory", description="Open your station storage locker to view collected items and vouchers.")
    async def inventory(self, ctx: commands.Context):
        await ctx.defer()
        user_id = ctx.author.id

        conn = sqlite3.connect("levels.db")
        cursor = conn.cursor()
        cursor.execute("SELECT item_id, item_type FROM inventory WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return await ctx.send("📦 **Your storage locker is completely empty!** Head out and deploy your mining laser with `/mine` or check the `/shop`.")

        embed = discord.Embed(
            title=f"📦 {ctx.author.display_name}'s Storage Locker",
            description="Here is a manifest of all rare artifacts, tokens, and background vouchers you've secured:",
            color=discord.Color.from_rgb(0, 229, 255)
        )

        # Group items by type for a clean display
        categories = {"Space Junk": [], "Consumable": [], "Voucher": [], "Currency": []}

        for item_id, item_type in rows:
            item_info = ITEM_REGISTRY.get(item_id, {"name": item_id, "emoji": "📦", "type": "Unknown", "desc": "A mysterious object."})
            cat = item_info["type"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(f"{item_info['emoji']} **{item_info['name']}**\n└ *{item_info['desc']}* (`{item_id}`)")

        for cat_name, items in categories.items():
            if items:
                embed.add_field(name=f"✨ {cat_name}s", value="\n".join(items), inline=False)

        embed.set_footer(text="Tip: Vouchers can be used to customize your /profile card layout.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Inventory(bot))