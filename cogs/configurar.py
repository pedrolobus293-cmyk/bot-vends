import discord
from discord.ext import commands
from discord import app_commands
from utils.embeds import create_success_embed, create_error_embed, create_embed
import json

class ConfigModal(discord.ui.Modal):
    def __init__(self, key_type, title_str, placeholder_str, label_str, current_val=""):
        super().__init__(title=title_str)
        self.key_type = key_type
        self.add_item(discord.ui.TextInput(
            label=label_str, 
            default=current_val, 
            placeholder=placeholder_str, 
            max_length=200
        ))

    async def on_submit(self, interaction: discord.Interaction):
        value = self.children[0].value
        with open("config/config.json", "r+", encoding="utf-8") as f:
            config = json.load(f)
            config[self.key_type] = value
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()
        
        await interaction.response.send_message(
            embed=create_success_embed("Configuração Salva", f"O valor de **{self.title}** foi atualizado com sucesso!"),
            ephemeral=True
        )

class RoleClienteSelect(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder="👤 Selecione o Cargo de Cliente...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        role = self.values[0]
        with open("config/config.json", "r+", encoding="utf-8") as f:
            config = json.load(f)
            config["default_role"] = role.id
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()
        await interaction.response.send_message(
            embed=create_success_embed("Configurado", f"Cargo padrão de cliente: {role.mention}"), 
            ephemeral=True
        )

class RoleStaffSelect(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder="🛠️ Selecione o Cargo Staff...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        role = self.values[0]
        with open("config/config.json", "r+", encoding="utf-8") as f:
            config = json.load(f)
            roles = config.get("admin_roles", [])
            if role.id not in roles:
                roles.append(role.id)
                config["admin_roles"] = roles
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()
        await interaction.response.send_message(
            embed=create_success_embed("Configurado", f"O cargo {role.mention} agora pode gerenciar o bot."), 
            ephemeral=True
        )

class CanalLogsSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="📊 Selecione o Canal de Logs...", 
            channel_types=[discord.ChannelType.text],
            min_values=1, 
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        with open("config/config.json", "r+", encoding="utf-8") as f:
            config = json.load(f)
            config["logs_channel_id"] = channel.id
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()
        await interaction.response.send_message(
            embed=create_success_embed("Configurado", f"Canal de logs definido para {channel.mention}."), 
            ephemeral=True
        )

class ConfigurarView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(RoleClienteSelect())
        self.add_item(RoleStaffSelect())
        self.add_item(CanalLogsSelect())

    @discord.ui.button(label="Configurar Pix Padrão", style=discord.ButtonStyle.primary, emoji="💸")
    async def config_pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        with open("config/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        current = config.get("default_pix", "")
        await interaction.response.send_modal(
            ConfigModal("default_pix", "Configurar Pix Padrão", "Ex: 123.456.789-00 ou email@pix.com", "Chave Pix", current)
        )

class ConfigurarCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _is_admin(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            return True
        with open("config/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        user_roles = [role.id for role in interaction.user.roles]
        for role_id in config.get("admin_roles", []):
            if role_id in user_roles:
                return True
        return False

    @app_commands.command(name="configurar", description="Abre o painel interativo de configurações do bot")
    async def configurar(self, interaction: discord.Interaction):
        if not self._is_admin(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Permissão Negada", "Você não tem permissão para usar este comando."),
                ephemeral=True
            )
            return
            
        embed = create_embed(
            "⚙️ | Configurações do Bot", 
            "Utilize os botões abaixo para definir as informações gerais da loja.\n\n"
            "• **Pix Padrão:** A chave que será usada se o produto não tiver uma própria.\n"
            "• **Cargo de Cliente:** O cargo dado automaticamente ao aprovar uma compra.\n"
            "• **Adicionar Staff:** Cargo que terá permissão de usar `/painel` e `/configurar`.\n"
            "• **Canal de Logs:** Canal onde chegarão os comprovantes de pagamento."
        )
        await interaction.response.send_message(embed=embed, view=ConfigurarView(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(ConfigurarCog(bot))
