import json
import os
from collections import defaultdict
from typing import List
from client.ollama_client import OllamaClient
from config import BASE_URL, MODEL_NAME

ollama = OllamaClient(base_url=BASE_URL, model=MODEL_NAME, secured=False)

CHUNK_SIZE = 60
MAX_CHUNKS = 30  # limite pour éviter de faire 100 appels
MSG_PATH = "../conversations.json"
OUT_PATH = "personas.json"
TMP_CHUNKS_DIR = "chunk_profiles"

os.makedirs(TMP_CHUNKS_DIR, exist_ok=True)

def load_messages(filepath: str = MSG_PATH) -> dict:
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    grouped = defaultdict(list)
    for msg in data:
        grouped[msg["author"]].append(msg["content"])
    return grouped

def chunk_messages(messages: List[str], chunk_size: int = CHUNK_SIZE) -> List[List[str]]:
    return [messages[i:i + chunk_size] for i in range(0, len(messages), chunk_size)]

def generate_partial_profile(messages: List[str], username: str, index: int) -> str:
    joined = f"Tous les messages ci-dessous ont été écrits par **{username}** :\n\n" + \
             "\n".join(f"- {m}" for m in messages)

    prompt = (
        f"L'utilisateur Discord nommé **{username}** a posté les messages suivants sur le serveur :\n"
        f"{joined}\n\n"
        "Tu es un analyste comportemental expert en analyse d'individus en ligne.\n"
        "Ces messages ont TOUS été écrits par **la même personne**.\n"
        "À partir de ces messages, rédige un **profil partiel individuel** de cet utilisateur :\n"
        "- Quel est son style d'écriture ?\n"
        "- Quelle est son attitude générale ?\n"
        "- Quels sujets ou obsessions ressortent ?\n"
        "- Quelles phrases pourraient le définir ou le caricaturer ?\n\n"
        "Ne généralise pas. Ne parle pas de 'plusieurs utilisateurs'. Analyse **un seul individu**. Ne te censure pas."
    )

    print(f"🧩 Génération du chunk {index} pour {username}")
    return ollama.generate_response(prompt)

def synthesize_full_profile(partials: List[str], username: str) -> str:
    prompt = (
        f"Voici plusieurs analyses partielles de la même personne : **{username}**.\n"
        "Tous les résumés suivants concernent **le même utilisateur Discord**.\n"
        "À partir de ces résumés, génère un **profil de personnalité unique**, en suivant ce format :\n"
        "1. Style d'expression\n2. Tempérament général\n3. Thèmes favoris\n4. Punchlines typiques\n\n"
        "Le ton peut être imagé, satirique ou moqueur. Mais n'écris jamais comme s’il s’agissait de plusieurs personnes."
    )

    print(f"🧠 Synthèse finale pour {username}")
    return ollama.generate_response(prompt)

def generate_persona(messages: List[str], username: str) -> str:
    chunks = chunk_messages(messages)
    partial_profiles = []

    for i, chunk in enumerate(chunks if MAX_CHUNKS is None else chunks[:MAX_CHUNKS]):
        try:
            partial = generate_partial_profile(chunk, username, i + 1)
            partial_profiles.append(partial.strip())
            with open(f"{TMP_CHUNKS_DIR}/{username}_chunk_{i+1}.txt", "w", encoding="utf-8") as f:
                f.write(partial)
        except Exception as e:
            print(f"⚠️ Échec chunk {i+1} pour {username} : {e}")

    return synthesize_full_profile(partial_profiles, username)

def main():
    all_personas = {}
    messages_by_user = load_messages()

    for user, messages in messages_by_user.items():
        print(f"📦 Traitement de {user} ({len(messages)} messages)")
        try:
            persona = generate_persona(messages, user)
            all_personas[user] = persona.strip()
        except Exception as e:
            print(f"❌ Persona échoué pour {user} : {e}")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_personas, f, indent=2, ensure_ascii=False)

    print("✅ Tous les profils générés dans personas.json")

if __name__ == "__main__":
    main()
