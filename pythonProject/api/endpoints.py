from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from client.ollama_client import OllamaClient
from config import BASE_URL, MODEL_NAME

router = APIRouter()

ollama = OllamaClient(base_url=BASE_URL, model=MODEL_NAME)

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        response_text = ollama.generate_response(request.prompt)
        return ChatResponse(response=response_text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
