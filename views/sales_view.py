import discord
from database.db import get_product, create_purchase, update_purchase_status
from utils.embeds import create_embed, create_success_embed, create_error_embed
import json
import asyncio

class TicketControlView(discord.ui.View):
    def __init__(self, purchase_id, product, buyer_id):
        super().__init__(timeout=None)
        self.purchase_id = purchase_id
        self.product = product
        self.buyer_id = buyer_id

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Fechando o ticket em 3 segundos...", ephemeral=False)
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete()
        except:
            pass

    @discord.ui.button(label="Finalizar", style=discord.ButtonStyle.success)
    async def finish_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Admin check
        with open("config/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        is_admin = interaction.user.guild_permissions.administrator
        if not is_admin:
            user_roles = [r.id for r in interaction.user.roles]
            for r_id in config.get("admin_roles", []):
                if r_id in user_roles:
                    is_admin = True
                    break
                    
        if not is_admin:
            return await interaction.response.send_message("❌ Apenas administradores podem usar este botão.", ephemeral=True)
            
        await update_purchase_status(self.purchase_id, "APPROVED")
        
        # Give Role
        try:
            guild = interaction.guild
            member = await guild.fetch_member(self.buyer_id)
            role_id = config.get("default_role")
            if role_id:
                role = guild.get_role(role_id)
                if role and member:
                    await member.add_roles(role)
        except Exception as e:
            print(f"Erro ao dar cargo: {e}")

        # Send DM to buyer
        try:
            buyer = await interaction.client.fetch_user(self.buyer_id)
            embed = discord.Embed(
                title="✅ Compra Aprovada!",
                description=f"Sua compra de **{self.product['name']}** foi aprovada!\n\n"
                            f"**Mensagem do Vendedor:**\n{self.product['buyer_message']}",
                color=discord.Color.green()
            )
            await buyer.send(embed=embed)
        except:
            pass
            
        await interaction.response.send_message("Compra finalizada! Produto entregue (DM) e Cargo adicionado. Fechando ticket em 5 segundos...", ephemeral=False)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass

class BuyButton(discord.ui.Button):
    def __init__(self, product_id, label="Comprar"):
        super().__init__(label=label, style=discord.ButtonStyle.success, custom_id=f"buy_{product_id}")
        self.product_id = product_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        product = await get_product(self.product_id)
        if not product:
            return await interaction.followup.send("Produto não encontrado.", ephemeral=True)

        # Create purchase record
        purchase_id = await create_purchase(interaction.user.id, self.product_id)
        
        with open("config/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        pix_key = config.get("default_pix", "Chave não configurada")

        guild = interaction.guild
        
        # Create Ticket Channel Overwrites
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
        }
        
        for admin_role_id in config.get("admin_roles", []):
            role = guild.get_role(admin_role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            ticket_channel = await guild.create_text_channel(
                name=f"🛒・ticket-{interaction.user.name}",
                overwrites=overwrites
            )
            
            await interaction.followup.send(f"✅ Ticket criado em {ticket_channel.mention}!", ephemeral=True)
            
            # Send initial message inside ticket
            embed = discord.Embed(
                title=f"🛒 | Ticket de Compra: {product['name']}",
                description=f"Olá {interaction.user.mention}!\n\n"
                            f"💰 **Valor:** R$ {product['price']:.2f}\n"
                            f"🔑 **Chave Pix:** `{pix_key}`\n\n"
                            "Por favor, efatue o pagamento e **envie o comprovante** (como imagem/anexo) neste chat.\n"
                            "Um administrador confirmará seu pagamento em breve.",
                color=product['embed_color'] or 3447003
            )
            if product['image_url']:
                embed.set_thumbnail(url=product['image_url'])
                
            view = TicketControlView(purchase_id, product, interaction.user.id)
            await ticket_channel.send(content=f"{interaction.user.mention}", embed=embed, view=view)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Não tenho permissão para criar tickets neste servidor (verifique meus cargos/permissões).", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao criar ticket: {e}", ephemeral=True)
