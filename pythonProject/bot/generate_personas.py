import json
from collections import defaultdict
from client.ollama_client import OllamaClient
from config import BASE_URL, MODEL_NAME

ollama = OllamaClient(base_url=BASE_URL, model=MODEL_NAME)

def load_messages(filepath="../conversations.json"):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    grouped = defaultdict(list)
    for msg in data:
        grouped[msg["author"]].append(msg["content"])
    return grouped

def generate_persona(messages: list[str], username: str) -> str:
    joined_messages = "\n".join(f"- {msg}" for msg in messages[:20])

    prompt = (
        f"Voici des extraits de messages de l'utilisateur Discord nommé **{username}** :\n"
        f"{joined_messages}\n\n"
        "Analyse et synthétise ces messages pour générer un **profil de personnalité complet**. "
        "Réponds en 4 points clairs :\n\n"
        "1. **Style d'écriture** (ex : direct, ironique, vulgaire, soutenu...)\n"
        "2. **État d'esprit général** (ex : optimiste, rageux, passif-agressif...)\n"
        "3. **Sujets favoris ou récurrents** (ex : politique, tech, drague, blagues douteuses...)\n"
        "4. **Anecdotes ou phrases typiques** (réutilisables dans un contexte RP ou humouristique)\n\n"
        "Sois concis mais imagé, comme si tu devais résumer cet utilisateur à un pote qui ne le connaît pas. "
        "Utilise un ton neutre et précis, mais n’hésite pas à sortir un ou deux exemples de phrases marquantes."
    )

    return ollama.generate_response(prompt)

def main():
    all_personas = {}
    messages_by_user = load_messages()

    for user, messages in messages_by_user.items():
        print(f"🧠 Génération du persona pour {user} ({len(messages)} messages)...")
        try:
            persona = generate_persona(messages, user)
            all_personas[user] = persona.strip()
        except Exception as e:
            print(f"⚠️ Erreur pour {user} : {e}")

    with open("personas.json", "w", encoding="utf-8") as f:
        json.dump(all_personas, f, indent=2, ensure_ascii=False)

    print("✅ Personas générés et enregistrés dans personas.json")

if __name__ == "__main__":
    main()
