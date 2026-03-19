import discord
from discord.ext import commands
from discord import app_commands
from database.db import add_product, edit_product, remove_product, get_all_products, get_product
from utils.embeds import create_success_embed, create_error_embed, create_embed
import json

class ProductModal(discord.ui.Modal):
    def __init__(self, product_id=None, title_val="", desc_val="", price_val="", msg_val=""):
        super().__init__(title="Gerenciar Produto")
        self.product_id = product_id
        
        self.add_item(discord.ui.TextInput(label="Título do Produto", default=title_val, placeholder="Ex: Netflix 30 dias", max_length=100))
        self.add_item(discord.ui.TextInput(label="Descrição", default=desc_val, placeholder="Ex: Entrega imediata...", style=discord.TextStyle.paragraph))
        self.add_item(discord.ui.TextInput(label="Preço (Apenas números)", default=str(price_val), placeholder="Ex: 15.90"))
        self.add_item(discord.ui.TextInput(label="Mensagem de Entrega", default=msg_val, placeholder="Mensagem enviada após aprovação", style=discord.TextStyle.paragraph))

    async def on_submit(self, interaction: discord.Interaction):
        name = self.children[0].value
        desc = self.children[1].value
        try:
            price = float(self.children[2].value.replace(",", "."))
        except:
            return await interaction.response.send_message("Preço inválido.", ephemeral=True)
            
        msg = self.children[3].value
        
        # We pass dummy values to DB since we now read them directly from config globally
        dummy_pix = "Global"
        dummy_role = 0
        
        if self.product_id:
            old = await get_product(self.product_id)
            await edit_product(self.product_id, name, desc, price, dummy_pix, msg, dummy_role, old['button_name'], old['image_url'], old['embed_color'])
            await interaction.response.send_message(embed=create_success_embed("Sucesso", f"Produto {name} editado!"), ephemeral=True)
        else:
            await add_product(name, desc, price, dummy_pix, msg, dummy_role)
            await interaction.response.send_message(embed=create_success_embed("Sucesso", f"Produto {name} criado!"), ephemeral=True)

class ProductSelect(discord.ui.Select):
    def __init__(self, products, action_type):
        options = [discord.SelectOption(label=p['name'], value=str(p['id']), description=f"R$ {p['price']:.2f}") for p in products]
        super().__init__(placeholder="Escolha um produto...", options=options)
        self.action_type = action_type # 'edit', 'delete'

    async def callback(self, interaction: discord.Interaction):
        product_id = int(self.values[0])
        product = await get_product(product_id)
        
        if self.action_type == 'delete':
            await remove_product(product_id)
            await interaction.response.send_message(embed=create_success_embed("Removido", f"Produto {product['name']} removido."), ephemeral=True)
        
        elif self.action_type == 'edit':
            modal = ProductModal(
                product_id=product_id, 
                title_val=product['name'], 
                desc_val=product['description'], 
                price_val=product['price'], 
                msg_val=product['buyer_message']
            )
            await interaction.response.send_modal(modal)

class PublishConfirmButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Confirmar Publicação", style=discord.ButtonStyle.success, row=2)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        view = self.view
        if not getattr(view, 'selected_channel', None) or not getattr(view, 'selected_product', None):
            return await interaction.followup.send("Selecione um canal e um produto nas opções acima primeiro!", ephemeral=True)
        
        product = view.selected_product
        
        # ChannelSelect might return an AppCommandChannel which doesn't have .send()
        channel_id = view.selected_channel.id
        channel = interaction.client.get_channel(channel_id)
        if not channel:
            try:
                channel = await interaction.client.fetch_channel(channel_id)
            except:
                return await interaction.followup.send("❌ Não foi possível encontrar o canal selecionado.", ephemeral=True)
        
        embed = discord.Embed(
            title=str(product['name']), 
            description=str(product['description']), 
            color=int(product['embed_color'] or 3447003)
        )
        img = product['image_url']
        if img and str(img).startswith("http"):
            embed.set_image(url=img)
            
        embed.add_field(name="Preço", value=f"R$ {product['price']:.2f}")
        
        # Lazy import of BuyButton
        from views.sales_view import BuyButton
        product_view = discord.ui.View(timeout=None)
        btn_name = product['button_name'] or "Comprar"
        product_view.add_item(BuyButton(product['id'], str(btn_name)))
        
        try:
            await channel.send(embed=embed, view=product_view)
            await interaction.followup.send(f"✅ Painel publicado com sucesso em {channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ Não tenho permissão para enviar mensagens nesse canal.", ephemeral=True)
        except Exception as e:
            print(f"Erro ao publicar: {e}")
            await interaction.followup.send(f"❌ Ocorreu um erro interno: {e}", ephemeral=True)

class PublishChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder="Selecione o canal...", channel_types=[discord.ChannelType.text], min_values=1, max_values=1, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_channel = self.values[0]
        await interaction.response.defer()

class PublishProductSelect(discord.ui.Select):
    def __init__(self, products):
        options = [discord.SelectOption(label=p['name'], value=str(p['id'])) for p in products]
        super().__init__(placeholder="Selecione o produto...", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        product_id = int(self.values[0])
        self.view.selected_product = await get_product(product_id)
        await interaction.response.defer()

class PublishSelectsView(discord.ui.View):
    def __init__(self, products):
        super().__init__(timeout=120)
        self.selected_channel = None
        self.selected_product = None
        self.add_item(PublishChannelSelect())
        self.add_item(PublishProductSelect(products))
        self.add_item(PublishConfirmButton())

class PainelGerenciarView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Criar Produto", style=discord.ButtonStyle.success)
    async def create_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ProductModal())

    @discord.ui.button(label="Editar Produto", style=discord.ButtonStyle.primary)
    async def edit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        products = await get_all_products()
        if not products: return await interaction.response.send_message("Nenhum produto.", ephemeral=True)
        view = discord.ui.View()
        view.add_item(ProductSelect(products, 'edit'))
        await interaction.response.send_message("Selecione o produto para editar:", view=view, ephemeral=True)

    @discord.ui.button(label="Apagar Produto", style=discord.ButtonStyle.danger)
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        products = await get_all_products()
        if not products: return await interaction.response.send_message("Nenhum produto.", ephemeral=True)
        view = discord.ui.View()
        view.add_item(ProductSelect(products, 'delete'))
        await interaction.response.send_message("Selecione o produto para apagar:", view=view, ephemeral=True)

    @discord.ui.button(label="Publicar Produto", style=discord.ButtonStyle.secondary)
    async def publish_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        products = await get_all_products()
        if not products: return await interaction.response.send_message("Nenhum produto.", ephemeral=True)
        await interaction.response.send_message(
            "Selecione o **Canal** e o **Produto** que deseja publicar e depois clique em *Confirmar*:", 
            view=PublishSelectsView(products), 
            ephemeral=True
        )

class PainelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painel", description="Gerencia os produtos e painéis de venda")
    async def painel(self, interaction: discord.Interaction):
        # Admin check
        with open("config/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        if not interaction.user.guild_permissions.administrator:
            is_staff = False
            for r in interaction.user.roles:
                if r.id in config.get("admin_roles", []):
                    is_staff = True
                    break
            if not is_staff:
                return await interaction.response.send_message(embed=create_error_embed("Acesso Negado", "Você não é staff."), ephemeral=True)
        
        embed = create_embed("🏷️ | Gerenciamento de Vendas", "Escolha uma das opções abaixo para gerenciar seus produtos digitais.")
        await interaction.response.send_message(embed=embed, view=PainelGerenciarView(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(PainelCog(bot))
