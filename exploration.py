import discord
from discord.ext import commands
import sqlite3
import time
import random

class Exploration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.COOLDOWN_SECONDS = 4 * 3600  # 4-hour cooldown

    @commands.hybrid_command(name="mine", description="Deploy your starship mining laser to scout for stardust and rare loot.")
    async def mine(self, ctx: commands.Context):
        await ctx.defer()
        user_id = ctx.author.id
        current_time = time.time()

        conn = sqlite3.connect("levels.db")
        cursor = conn.cursor()

        cursor.execute("SELECT mining_charges, last_mined, stardust, xp FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if not row:
            cursor.execute("""
                INSERT OR IGNORE INTO users (user_id, mining_charges, last_mined, stardust, xp) 
                VALUES (?, 5, 0, 0, 0)
            """, (user_id,))
            conn.commit()
            charges, last_mined, stardust, current_xp = 5, 0, 0, 0
        else:
            charges, last_mined, stardust, current_xp = row

        elapsed = current_time - last_mined
        if elapsed < self.COOLDOWN_SECONDS:
            remaining = int(self.COOLDOWN_SECONDS - elapsed)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            conn.close()
            return await ctx.send(f"⚠️ **Mining laser is recharging!** Next charge ready in **{hours}h {minutes}m**.")

        if charges <= 0:
            conn.close()
            return await ctx.send("🚨 **Laser Depleted!** You are out of fuel charges. Visit the station shop for an emergency refill.")

        # --- TIERED LOOT ROLL ---
        roll = random.random()
        new_charges = charges - 1
        
        found_stardust = random.randint(40, 100)
        new_stardust = stardust + found_stardust
        
        loot_description = f"✨ **Stardust Collected:** `{found_stardust}`"
        rarity_badge = "common"

        if roll < 0.40:
            # Tier 1: Common (Just Stardust)
            pass

        elif roll < 0.60:
            # Tier 2: Uncommon (Stardust + XP Data Shard)
            found_xp = random.randint(75, 200)
            cursor.execute("UPDATE users SET xp = xp + ? WHERE user_id = ?", (found_xp, user_id))
            loot_description += f"\n📊 **XP Data Shard:** `+{found_xp} XP`"
            rarity_badge = "uncommon"

        elif roll < 0.75:
            # Tier 3: Rare (Space Junk Artifact!)
            junk_items = {
                "space_pizza": "🍕 Dehydrated Space Pizza (Slightly freezer-burned)",
                "floppy_disk": "💾 Ancient Alien Floppy Disk (Contains mysterious code)",
                "meteorite": "🪨 Suspiciously Warm Meteorite Chunk",
                "rubber_duck": "🐤 Rubber Duck in a Micro-Spacesuit"
            }
            item_id, item_name = random.choice(list(junk_items.items()))
            
            cursor.execute("""
                INSERT INTO inventory (user_id, item_id, item_type) 
                VALUES (?, ?, 'space_junk')
                ON CONFLICT(user_id, item_id) DO UPDATE SET item_type = 'space_junk'
            """, (user_id, item_id))
            
            loot_description += f"\n🛸 **Space Junk Salvaged:** Found a `{item_name}`!"
            rarity_badge = "rare"

        elif roll < 0.88:
            # Tier 4: Rare/Epic (Arcade Token for future minigames)
            cursor.execute("""
                INSERT INTO inventory (user_id, item_id, item_type) 
                VALUES (?, 'arcade_token', 'currency')
                ON CONFLICT(user_id, item_id) DO NOTHING
            """, (user_id,))
            loot_description += f"\n🪙 **Holodeck Find:** Discovered a shiny **Arcade Token**!"
            rarity_badge = "rare"

        elif roll < 0.96:
            # Tier 5: Epic (Time Crystal)
            cursor.execute("UPDATE users SET time_crystals = time_crystals + 1 WHERE user_id = ?", (user_id,))
            loot_description += f"\n💎 **Rare Discovery:** Acquired a stable **Time Crystal**!"
            rarity_badge = "epic"

        else:
            # Tier 6: Legendary (Secret Background Voucher)
            voucher_id = random.choice(["neon_grid", "deep_void", "solaris_ring"])
            cursor.execute("""
                INSERT INTO inventory (user_id, item_id, item_type) 
                VALUES (?, ?, 'background_voucher')
                ON CONFLICT(user_id, item_id) DO NOTHING
            """, (user_id, voucher_id))
            loot_description += f"\n🌟 **Legendary Find:** Unlocked blueprint voucher `[{voucher_id}]`!"
            rarity_badge = "legendary"

        cursor.execute("""
            UPDATE users 
            SET mining_charges = ?, last_mined = ?, stardust = ? 
            WHERE user_id = ?
        """, (new_charges, current_time, new_stardust, user_id))

        conn.commit()
        conn.close()

        colors = {
            "common": discord.Color.from_rgb(120, 140, 160),
            "uncommon": discord.Color.from_rgb(0, 229, 255),
            "rare": discord.Color.from_rgb(50, 205, 50),
            "epic": discord.Color.from_rgb(186, 85, 211),
            "legendary": discord.Color.from_rgb(255, 215, 0)
        }

        embed = discord.Embed(
            title="🌌 Starship Mining Log",
            description=f"Laser beam fired into the sector debris field...\n\n{loot_description}",
            color=colors.get(rarity_badge, discord.Color.blue())
        )
        embed.set_footer(text=f"Fuel Charges Remaining: {new_charges}/5 • Cooldown: 4h")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Exploration(bot))