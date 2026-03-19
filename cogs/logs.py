import discord
from discord.ext import commands
from discord import app_commands
from utils.embeds import create_success_embed, create_embed, create_error_embed
import json
import datetime

class LogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_logs_channel(self):
        with open("config/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            logs_channel_id = config.get("logs_channel_id")
            if logs_channel_id:
                return self.bot.get_channel(logs_channel_id)
        return None

    @app_commands.command(name="logs", description="Define o canal de envio de logs de compras e moderação")
    async def set_logs_channel(self, interaction: discord.Interaction, canal: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Permissão negada.", ephemeral=True)
            
        with open("config/config.json", "r+", encoding="utf-8") as f:
            config = json.load(f)
            config["logs_channel_id"] = canal.id
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()
            
        await interaction.response.send_message(
            embed=create_success_embed("Canal de Logs Configurado", f"Os logs agora serão enviados no canal {canal.mention}"),
            ephemeral=True
        )

    # Event Listeners for logging
    
    @commands.Cog.listener()
    async def on_product_added(self, admin: discord.User, nome: str, preco: float):
        channel = await self.get_logs_channel()
        if channel:
            embed = create_success_embed("➕ | Novo Produto", f"**Criado por:** {admin.mention}\n**Produto:** {nome}\n**Preço:** R$ {preco:.2f}")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_product_edited(self, admin: discord.User, id_produto: int, nome: str):
        channel = await self.get_logs_channel()
        if channel:
            embed = create_embed("✏️ | Produto Editado", f"**Editado por:** {admin.mention}\n**Produto (ID):** {nome} ({id_produto})")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_product_removed(self, admin: discord.User, id_produto: int, nome: str):
        channel = await self.get_logs_channel()
        if channel:
            embed = create_error_embed("🗑️ | Produto Removido", f"**Removido por:** {admin.mention}\n**Produto:** {nome} (ID: {id_produto})")
            await channel.send(embed=embed)
    @commands.Cog.listener()
    async def on_purchase_started(self, user: discord.User, product: dict, purchase_id: int):
        channel = await self.get_logs_channel()
        if channel:
            embed = create_embed(
                "📝 | Compra Iniciada",
                f"**Usuário:** {user.mention} ({user.id})\n**Produto:** {product['name']}\n**Preço:** R$ {product['price']:.2f}\n*Aguardando comprovante...*"
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_purchase_approved(self, user, product, admin: discord.User):
        channel = await self.get_logs_channel()
        if channel:
            user_mention = user.mention if user else "Desconhecido"
            embed = create_success_embed(
                "✅ | Compra Aprovada",
                f"**Produto:** {product['name']}\n**Comprador:** {user_mention}\n**Aprovado por:** {admin.mention}"
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_purchase_rejected(self, user, product, admin: discord.User):
        channel = await self.get_logs_channel()
        if channel:
            user_mention = user.mention if user else "Desconhecido"
            embed = create_error_embed(
                "❌ | Compra Recusada",
                f"**Produto:** {product['name']}\n**Comprador:** {user_mention}\n**Recusado por:** {admin.mention}"
            )
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LogsCog(bot))
