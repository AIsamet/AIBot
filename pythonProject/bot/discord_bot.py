import json
import random
import discord
from discord.ext import commands

from client.ollama_client import OllamaClient
from config import DISCORD_TOKEN, BASE_URL, MODEL_NAME, PERSONALITIES_PATH, USER_PERSONAS_PATH

# --- Configuration ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
ollama = OllamaClient(
    base_url=BASE_URL,
    model=MODEL_NAME,
    personalities_path=PERSONALITIES_PATH,
    personality_name="malveillance",
    secured=False
)

# --- Chargement des personas ---
try:
    with open(USER_PERSONAS_PATH, encoding="utf-8") as f:
        USER_PERSONAS = json.load(f)
    print(f"✅ {len(USER_PERSONAS)} personas chargés.")
except FileNotFoundError:
    USER_PERSONAS = {}
    print("⚠️ Aucun fichier personas.json trouvé.")

# --- Utilitaires ---
MAX_DISCORD_LENGTH = 2000
PROBA_REPONSE = 0

def build_prompt(message_text: str, author_name: str) -> str:
    persona = USER_PERSONAS.get(author_name)
    if persona:
        return f"Profil de l'utilisateur :\n{persona}\n\nMessage reçu :\n{message_text}"
    return message_text

def split_response(response: str) -> list[str]:
    return [response[i:i + MAX_DISCORD_LENGTH] for i in range(0, len(response), MAX_DISCORD_LENGTH)]

async def send_response(channel, response: str):
    chunks = split_response(response)
    for chunk in chunks:
        await channel.send(chunk)

# --- Events ---
@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    print(f"Personnalité active : {ollama.personality_name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    if random.random() < PROBA_REPONSE:
        try:
            await message.channel.typing()
            prompt = build_prompt(message.content, message.author.name)
            response = ollama.generate_response(prompt)
            await send_response(message.channel, response)
        except Exception as e:
            await message.channel.send(f"⚠️ Tonton a crashé : {str(e)}")

    await bot.process_commands(message)

# --- Commandes ---
@bot.command(name="malveillance")
async def tonton_chat(ctx, *, message: str):
    await ctx.send("💬 Malveillance en cours...")
    try:
        prompt = build_prompt(message, ctx.author.name)
        response = ollama.generate_response(prompt)
        await send_response(ctx, response)
    except Exception as e:
        await ctx.send(f"⚠️ Tonton est vénère, il bug : {str(e)}")

@bot.command(name="profil")
async def show_persona(ctx, *, username: str = None):
    target = username or ctx.author.name
    persona = USER_PERSONAS.get(target)

    if persona:
        await ctx.send(f"🧠 Profil de **{target}** :")
        chunks = [persona[i:i + MAX_DISCORD_LENGTH] for i in range(0, len(persona), MAX_DISCORD_LENGTH)]
        for chunk in chunks:
            await ctx.send(chunk)
    else:
        if username:
            await ctx.send(f"❌ Tonton connaît pas ce clown : **{username}**.")
        else:
            await ctx.send("❌ Tonton te connaît pas encore. Parle un peu plus qu’on te dresse le portrait 😏")


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
    await ctx.reply(f"✅ Scraping terminé ! ({total_messages} messages).", mention_author=True)

# --- Démarrage ---
bot.run(DISCORD_TOKEN)