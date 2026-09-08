import discord
from discord.ext import commands
import sqlite3

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Define shop items, costs, and descriptions
        self.SHOP_ITEMS = {
            "fuel_refill": {
                "name": "⚡ Emergency Fuel Cell (5 Charges)",
                "cost": 250,
                "type": "consumable",
                "desc": "Instantly refills your starship mining laser back to 5/5 charges."
            },
            "pet_snack": {
                "name": "🧬 Cosmic Bio-Feed (Pet Snack)",
                "cost": 400,
                "type": "consumable",
                "desc": "Nutrient pack used to feed your station pet companion."
            },
            "neon_grid": {
                "name": "🌆 Background Voucher: Neon Grid",
                "cost": 1000,
                "type": "background_voucher",
                "desc": "Unlocks the Cyberpunk Neon Grid background preset for your /profile card."
            },
            "deep_void": {
                "name": "🌌 Background Voucher: Deep Void",
                "cost": 1200,
                "type": "background_voucher",
                "desc": "Unlocks the Deep Void galaxy background preset for your /profile card."
            }
        }

    @commands.hybrid_command(name="shop", description="Browse the Enceladus Station vendor catalog.")
    async def shop(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🛒 Enceladus Station Trading Post",
            description="Use `/buy <item_id>` to purchase upgrades, fuel, and background vouchers with your Stardust.",
            color=discord.Color.from_rgb(0, 229, 255)
        )

        for item_id, details in self.SHOP_ITEMS.items():
            embed.add_field(
                name=f"{details['name']} (`{item_id}`)",
                value=f"💰 Price: **{details['cost']} Stardust**\n📖 {details['desc']}",
                inline=False
            )

        embed.set_footer(text="Tip: Check your wallet balance using /profile")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="buy", description="Purchase an item from the station shop.")
    async def buy(self, ctx: commands.Context, item_id: str):
        await ctx.defer()
        user_id = ctx.author.id
        item_id = item_id.lower()

        if item_id not in self.SHOP_ITEMS:
            return await ctx.send(f"❌ Invalid item ID! Check available items using `/shop`.")

        item = self.SHOP_ITEMS[item_id]
        cost = item["cost"]

        conn = sqlite3.connect("levels.db")
        cursor = conn.cursor()

        # Check user's stardust balance
        cursor.execute("SELECT stardust, mining_charges FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return await ctx.send("❌ You don't have an active station profile yet. Run `/profile` or `/mine` first!")

        stardust, charges = row

        if stardust < cost:
            conn.close()
            return await ctx.send(f"💸 **Insufficient Stardust!** You have `{stardust}` Stardust, but this item costs `{cost}`.")

        # Process the purchase based on item type
        new_stardust = stardust - cost

        if item["type"] == "consumable" and item_id == "fuel_refill":
            if charges >= 5:
                conn.close()
                return await ctx.send("⚠️ Your mining laser fuel charges are already full (`5/5`)!")
            
            # Refill charges and deduct stardust
            cursor.execute("UPDATE users SET stardust = ?, mining_charges = 5 WHERE user_id = ?", (new_stardust, user_id))
            conn.commit()
            conn.close()
            return await ctx.send(f"⚡ **Purchase Successful!** Refilled your mining laser charges back to `5/5` for `{cost}` Stardust.")

        elif item["type"] == "consumable" and item_id == "pet_snack":
            # Add to inventory table
            cursor.execute("""
                INSERT INTO inventory (user_id, item_id, item_type) 
                VALUES (?, ?, 'consumable')
                ON CONFLICT(user_id, item_id) DO NOTHING
            """, (user_id, item_id))
            cursor.execute("UPDATE users SET stardust = ? WHERE user_id = ?", (new_stardust, user_id))
            conn.commit()
            conn.close()
            return await ctx.send(f"🧬 **Purchase Successful!** Added a Cosmic Bio-Feed to your inventory for `{cost}` Stardust.")

        elif item["type"] == "background_voucher":
            # Check if user already owns this background
            cursor.execute("SELECT 1 FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            if cursor.fetchone():
                conn.close()
                return await ctx.send("⚠️ You already own this background voucher!")

            cursor.execute("""
                INSERT INTO inventory (user_id, item_id, item_type) 
                VALUES (?, ?, 'background_voucher')
            """, (user_id, item_id))
            cursor.execute("UPDATE users SET stardust = ? WHERE user_id = ?", (new_stardust, user_id))
            conn.commit()
            conn.close()
            return await ctx.send(f"🌟 **Purchase Successful!** Unlocked background voucher `{item_id}` for `{cost}` Stardust! Use your inventory items to deck out your profile.")

        conn.close()
        await ctx.send("❌ An error occurred processing your transaction.")

    @commands.hybrid_command(name="item", description="Inspect an item from the station database to check its properties.")
    async def item_lookup(self, ctx: commands.Context, item_id: str):
        item_id = item_id.lower()
        # Pulls from the same master registry
        from inventory import ITEM_REGISTRY

        if item_id not in ITEM_REGISTRY:
            return await ctx.send(f"❌ Unknown item code `'{item_id}'`. Check the `/shop` or your `/inventory` for valid item IDs.")

        info = ITEM_REGISTRY[item_id]
        
        embed = discord.Embed(
            title=f"{info['emoji']} {info['name']}",
            description=f"**Category:** {info['type']}\n**Description:** {info['desc']}",
            color=discord.Color.from_rgb(120, 140, 160)
        )
        embed.set_footer(text=f"System Item ID: {item_id}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))