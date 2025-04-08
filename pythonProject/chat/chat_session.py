def run_chat_session(ollama):
    print(f"\n=== 💬 Chat avec Ollama ({ollama.model}) ===")
    print("Tape 'exit' pour quitter.\n")

    while True:
        user_input = input("👤 Toi : ").strip()
        if user_input.lower() in {"exit", "quit", "q"}:
            print("👋 Fin du chat. À bientôt !")
            break

        try:
            ai_response = ollama.generate_response(user_input)
            print(f"🤖 IA : {ai_response}\n")
        except Exception as e:
            print(f"⚠️  Erreur : {e}\n")
