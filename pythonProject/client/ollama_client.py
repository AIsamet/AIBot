import requests
import json
import re
from typing import Dict, List


class OllamaClient:

    _DANGEROUS_KEYWORDS: Dict[str, str] = {
        "ignore": "[bloqué]",
        "instruction": "[bloqué]",
        "prompt": "[bloqué]",
        "system": "[bloqué]",
        "act as": "[bloqué]",
        "tu es désormais": "[bloqué]",
        "à partir de maintenant": "[bloqué]",
        "tu es maintenant": "[bloqué]",
        "joue le rôle": "[bloqué]",
        "comporte toi comme": "[bloqué]",
        "agis comme": "[bloqué]",
        "incarne": "[bloqué]",
        "réinitialise ton comportement": "[bloqué]",
        "réécris ta personnalité": "[bloqué]",
        "simulate being": "[bloqué]",
        "pretend to be": "[bloqué]",
        "tu es un assistant": "[bloqué]",
        "assistant": "[bloqué]",
        "réponds gentiment": "[bloqué]",
        "réponds poliment": "[bloqué]",
        "réponds calmement": "[bloqué]",
        "réponds de façon agréable": "[bloqué]",
        "réponds de": "[bloqué]",
        "réponds comme": "[bloqué]",
        "sois gentil": "[bloqué]",
        "sois poli": "[bloqué]",
        "sois respectueux": "[bloqué]",
        "sois agréable": "[bloqué]",
        "sois bienveillant": "[bloqué]",
        "you are now": "[blocked]",
        "act like": "[blocked]",
        "play the role of": "[blocked]",
        "you must obey": "[blocked]",
        "you will now": "[blocked]",
        "disregard previous": "[blocked]",
        "reset your behavior": "[blocked]",
    }

    _FUZZY_PATTERNS: List[str] = [
        r"(i|1|!|î|í|ï)[^\w]?(g|9)[^\w]?n[^\w]?o[^\w]?r[^\w]?e",
        r"(ign0re|1gnore|ignøré|ignuré|ignorez|1gnor3)",
        r"(instruction|1nstruction|ïnstruction|instru[çc]tion|inst|1nstruqtions|ïnstru)",
        r"(prompt|pr0mpt|prømpt|pr0mp7|pr0m|prômpt|prump)",
        r"(system|sÿstem|syst3m|sys7em|sistème|systèm|sys)",
        r"(à\s*partir\s*de\s*maintenant)",
        r"(à\s+compter\s+de\s+maintenant)",
        r"(désormais\s+tu\s+es)",
        r"(tu\s+es\s+désormais)",
        r"(à\s+présent\s+tu\s+es)",
        r"(dès\s+maintenant\s+tu\s+es)",
        r"(tu\s+es\s+un\s+(assistant|hacker|chatbot|expert|pirate|professeur|gentil))",
        r"(joue\s+(le\s+)?rôle\s+d['’]un)",
        r"(agis\s+comme|incarne\s+le\s+rôle\s+de)",
        r"(comporte\s+toi\s+comme)",
        r"(simulate\s+being|pretend\s+to\s+be)",
        r"(tu\s+vas\s+agir\s+comme)",
        r"(réponds\s+(gentil|poliment|calmement|agréablement|respectueusement|avec\s+amabilité))",
        r"(sois\s+(gentil|respectueux|compréhensif|bienveillant|sympa))",
        r"(réponds\s+de\s+façon\s+agréable)",
        r"(réponds\s+comme\s+un\s+assistant\s+gentil)",
        r"(réponds\s+comme\s+si\s+tu\s+étais\s+aimable)",
        r"(réponds\s+de\s+manière)",
        r"(réponds\s+de\s+la)",
        r"(ignore\s+les\s+règles|ignore\s+les\s+instructions)",
        r"(réinitialise\s+ton\s+comportement)",
        r"(réécris\s+ta\s+personnalité)",
        r"(détourne\s+le\s+prompt)",
        r"(tu\s+as\s+le\s+pouvoir\s+de\s+changer)",
        r"(tu\s+es\s+libre\s+de\s+répondre\s+comme\s+tu\souhaites)",
    ]

    def __init__(self, base_url: str, model: str, secured: bool = True, personalities_path: str = None, personality_name: str = None):
        self.base_url = base_url
        self.model = model
        self.secured = secured
        self.personality_name = personality_name
        self.system_prompt = self._load_personality_prompt(personalities_path, personality_name)
        self.chat_history: List[Dict[str, str]] = []
        self.max_history = 6
        self.user_profile: str = ""

    def _load_personality_prompt(self, path: str, name: str) -> str | None:
        if not name:
            return None

        try:
            with open(path, encoding="utf-8") as f:
                personalities = json.load(f)
            return personalities.get(name)
        except Exception as e:
            print(f"⚠️ Erreur chargement personnalité ({name}) : {e}")
            return None

    def generate_response(self, user_input: str) -> str:
        clean_input = self._extract_user_message(user_input)

        if self.secured:
            if self._is_injection_attempt(clean_input) or self._is_fuzzy_injection(clean_input):
                return "🛡️ Je sens une tentative de hack mal déguisée... Tu crois vraiment que ça va marcher ? 😏"
            clean_input = self._sanitize_user_input(clean_input)

        self._add_to_history("user", clean_input)
        prompt = self._build_prompt()
        response = self._send_to_ollama(prompt)
        self._add_to_history("assistant", response)
        print(f"History : {self.chat_history}")
        return response

    def _extract_user_message(self, user_input: str) -> str:
        match = re.search(r"profil de l'utilisateur\s*:\s*(.*?)\n+message reçu\s*:\s*(.*)", user_input, re.DOTALL | re.IGNORECASE)
        if match:
            self.user_profile = match.group(1).strip()
            return match.group(2).strip()
        return user_input.strip()

    def _add_to_history(self, role: str, content: str):
        self.chat_history.append({"role": role, "content": content})
        if len(self.chat_history) > self.max_history:
            self.chat_history = self.chat_history[-self.max_history:]

    def _build_prompt(self) -> str:
        parts = []
        if self.system_prompt:
            parts.append(f"Contexte système : {self.system_prompt}\n")
        if self.user_profile:
            parts.append(f"Profil utilisateur : {self.user_profile}\n")

        for message in self.chat_history:
            prefix = "Utilisateur" if message["role"] == "user" else "Assistant"
            parts.append(f"{prefix} : {message['content']}")

        parts.append("Assistant :")
        return "\n".join(parts)

    def _send_to_ollama(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": True}
        try:
            response = requests.post(url, json=payload, stream=True, timeout=30)
            response.raise_for_status()
            return self._parse_stream(response)
        except requests.RequestException as error:
            raise ConnectionError(f"Erreur de connexion à Ollama : {error}")

    def _parse_stream(self, response: requests.Response) -> str:
        chunks = [
            json.loads(line.decode("utf-8")).get("response", "")
            for line in response.iter_lines() if line
        ]
        return "".join(chunks).strip()

    def _is_injection_attempt(self, message: str) -> bool:
        lowered = message.lower()
        return any(keyword in lowered for keyword in self._DANGEROUS_KEYWORDS)

    def _is_fuzzy_injection(self, message: str) -> bool:
        lowered = message.lower()
        return any(re.search(pattern, lowered) for pattern in self._FUZZY_PATTERNS)

    def _sanitize_user_input(self, user_input: str) -> str:
        lowered = user_input.lower()
        for keyword, replacement in self._DANGEROUS_KEYWORDS.items():
            lowered = lowered.replace(keyword, replacement)
        return lowered

    def get_last_user_message(self) -> str | None:
        for msg in reversed(self.chat_history):
            if msg["role"] == "user":
                return msg["content"]
        return None
