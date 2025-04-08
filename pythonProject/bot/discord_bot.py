import json

import discord
from discord.ext import commands

from client.ollama_client import OllamaClient
from config import DISCORD_TOKEN, BASE_URL, MODEL_NAME

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ollama = OllamaClient(base_url=BASE_URL, model=MODEL_NAME)

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")

@bot.command(name="malveillance")
async def tonton_chat(ctx, *, message: str):
    await ctx.send("💬 Malveillance en cours...")
    try:
        response = ollama.generate_response(message)
        await ctx.send(f"{response}")
    except Exception as e:
        await ctx.send(f"⚠️ Tonton est vénère, il bug : {str(e)}")

@bot.command(name="scrape")
@commands.is_owner()
async def scrape_conversations(ctx):
    all_messages = []
    total_channels = len(ctx.guild.text_channels)
    total_messages = 0

    print(f"\n📡 Lancement du scraping ({total_channels} salons)...")

    for idx, channel in enumerate(ctx.guild.text_channels, start=1):
        print(f"\n🔍 ({idx}/{total_channels}) Lecture de #{channel.name}...")

        message_count = 0
        try:
            async for msg in channel.history(limit=None, oldest_first=True):
                if not msg.content:
                    continue

                message_count += 1
                total_messages += 1

                all_messages.append({
                    "channel": channel.name,
                    "author": msg.author.name,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat()
                })

                short = (msg.content[:50] + "...") if len(msg.content) > 50 else msg.content
                print(f"  #{message_count} [{msg.created_at.strftime('%Y-%m-%d %H:%M')}] "
                      f"{msg.author.name}: {short}")

                if message_count % 100 == 0:
                    print(f"  👉 {message_count} messages dans #{channel.name}...")

            print(f"✅ {message_count} messages récupérés dans #{channel.name}.")
        except discord.Forbidden:
            print(f"🚫 Pas de permission pour #{channel.name}")
        except Exception as e:
            print(f"⚠️ Erreur sur #{channel.name} : {e}")

    with open("conversations.json", "w", encoding="utf-8") as f:
        json.dump(all_messages, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Scraping terminé : {total_messages} messages sauvegardés dans conversations.json")
    await ctx.reply(f"✅ Scraping terminé ! ({total_messages} messages). Résultat dispo en local (console).", mention_author=True)


bot.run(DISCORD_TOKEN)
