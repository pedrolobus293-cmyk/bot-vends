import discord
import json

def get_embed_color():
    try:
        with open("config/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("embed_color", 3447003)
    except:
        return 3447003 # Default to blue if error

def create_embed(title, description, color=None):
    if color is None:
        color = get_embed_color()
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    return embed

def create_success_embed(title, description):
    embed = discord.Embed(
        title=f"✅ | {title}",
        description=description,
        color=discord.Color.green()
    )
    return embed

def create_error_embed(title, description):
    embed = discord.Embed(
        title=f"❌ | {title}",
        description=description,
        color=discord.Color.red()
    )
    return embed
