import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio

# Load configuration
def load_config():
    with open("config/config.json", "r", encoding="utf-8") as f:
        return json.load(f)

config = load_config()

class SalesBot(commands.Bot):
    def __init__(self, intents):
        # In discord.py 2.0+, commands.Bot handles the tree automatically.
        super().__init__(command_prefix=config.get("prefix", "!"), intents=intents)

    async def setup_hook(self):
        print("-------------------------------", flush=True)
        print(f"DEBUG: Entering setup_hook. CWD: {os.getcwd()}", flush=True)
        
        # Initialize database
        try:
            from database.db import setup_db
            await setup_db()
            print("✅ Database initialized.", flush=True)
        except Exception as e:
            print(f"❌ Database init failed: {e}", flush=True)
        
        # Load Cogs
        cogs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ Loaded extension: {filename}", flush=True)
                except Exception as e:
                    print(f"❌ Failed to load extension {filename}: {e}", flush=True)
        
        # Sync Slash Commands
        try:
            print("🚀 Syncing slash commands...", flush=True)
            # Global sync
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} global commands.", flush=True)
        except Exception as e:
            print(f"❌ Failed to sync: {e}", flush=True)
        
        print("-------------------------------", flush=True)

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name="Powered by tobyxxzz"))
        print(f"✅ Bot Online: {self.user} (ID: {self.user.id})", flush=True)
        print(f"DEBUG: Message Content Intent: {'ENABLED' if self.intents.message_content else 'DISABLED'}", flush=True)
        print("Bot is ready to sell!", flush=True)

    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Log to verify if the bot can read messages (requires Message Content Intent)
        print(f"DEBUG: Mensagem recebida de {message.author}: '{message.content}'", flush=True)
        
        await self.process_commands(message)

async def main():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    bot = SalesBot(intents=intents)
    async with bot:
        await bot.start(os.getenv("TOKEN"))

if __name__ == "__main__":
    if config["token"] == "SEU_TOKEN_AQUI" or config["token"] == "":
        print("ERRO: Configure o token do bot no arquivo config/config.json", flush=True)
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("Bot finalizado.", flush=True)
        except Exception as e:
            print(f"CRITICAL ERROR: {e}", flush=True)
