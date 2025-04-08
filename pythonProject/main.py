import sys

from fastapi import FastAPI
from api.endpoints import router

from client.ollama_client import OllamaClient
from chat.chat_session import run_chat_session
from config import MODEL_NAME, BASE_URL


def start_chat():
    ollama = OllamaClient(base_url=BASE_URL, model=MODEL_NAME)
    run_chat_session(ollama)

def main():
    start_chat()

if __name__ == "__main__":
    main()


def start_api():
    app = FastAPI(
        title="Ollama Chat API",
        description="API pour interagir avec un modèle Ollama local",
        version="1.0.0"
    )
    app.include_router(router)
    return app
app = start_api()
# uvicorn main:app --reload --host 192.168.1.4 --port 8000
