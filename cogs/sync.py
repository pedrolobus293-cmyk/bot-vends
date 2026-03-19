import discord
from discord.ext import commands
from discord import app_commands

class SyncCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sync", description="Sincroniza os comandos slash com o Discord imediatamente")
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx):
        await ctx.send("Sincronizando comandos slash...")
        try:
            synced = await self.bot.tree.sync()
            await ctx.send(f"✅ Sincronizado {len(synced)} comando(s) slash globalmente!")
        except Exception as e:
            await ctx.send(f"❌ Falha ao sincronizar comandos: {e}")

async def setup(bot):
    await bot.add_cog(SyncCog(bot))
