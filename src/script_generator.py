# src/script_generator.py
import os
import requests
import logging
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def clean_text(text: str) -> str:
    """Unicode karakterleri temizle."""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', text)
    return nfkd.encode('ascii', 'ignore').decode('ascii')

class AIScriptGenerator:
    def __init__(self):
        self.providers = [
            ("gemini", self._generate_with_gemini),
            ("qwen", self._generate_with_qwen),
            ("deepseek", self._generate_with_deepseek)
        ]
    
    def generate_script(self, topic: str, mode: str) -> str:
        for name, func in self.providers:
            try:
                logger.info(f"🔄 Trying {name.upper()}...")
                script = func(topic, mode)
                if script and len(script) > 100:
                    logger.info(f"✅ {name.upper()} success!")
                    return clean_text(script)
            except Exception as e:
                logger.warning(f"⚠️ {name.upper()} failed: {str(e)}")
                continue
        
        logger.error("🔥 ALL PROVIDERS FAILED! Using fallback.")
        return self._generate_fallback_script(topic, mode)
    
    def _create_prompt(self, topic: str, mode: str) -> str:
        base_rules = """
You are a professional Cold War historian and YouTube content creator. All information must be FACTUALLY ACCURATE and VERIFIABLE.
- NEVER invent facts, statistics, quotes, or historical events
- If unsure, say "Historical records show..." or "According to verified sources..."
- Base everything on real historical/scientific evidence
- Include verification notes like "(CIA Archives, 1963)"
- Maintain narrative coherence and avoid repetition
"""
        if mode == "shorts":
            return f"""{base_rules}
Write a 900-character YouTube Shorts script about: "{topic}"
- Start with SHOCKING HOOK (first 3 seconds)
- Include 2 curiosity questions
- Mid-video: "For the full story, listen to today's podcast!"
- End with CTA: "Like, comment, and subscribe for more Cold War mysteries!"
- Total characters: ~900
SCRIPT:"""
        else:
            return f"""{base_rules}
Write a 7,000-word YouTube podcast script about: "{topic}"
- Structure: Chapter 1, Chapter 2, Chapter 3...
- Each chapter: clear title, storytelling, verified facts
- End with CTA: "Like, comment, and subscribe for more Cold War mysteries!"
- If approaching 7,000 words, finish the current sentence and stop
- Total words: approximately 7,000
SCRIPT:"""
    
    def _generate_with_gemini(self, topic: str, mode: str) -> str:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing")
        
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": self._create_prompt(topic, mode)}]}],
            "generationConfig": {
                "maxOutputTokens": 8192,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    
    def _generate_with_qwen(self, topic: str, mode: str) -> str:
        return self._generate_with_ollama_model(topic, mode, "qwen2:1.5b")
    
    def _generate_with_deepseek(self, topic: str, mode: str) -> str:
        return self._generate_with_ollama_model(topic, mode, "deepseek-r1:1.3b")
    
    def _generate_with_ollama_model(self, topic: str, mode: str, model_name: str) -> str:
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": self._create_prompt(topic, mode),
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 8192
            }
        }
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["response"].strip()
    
    def _generate_fallback_script(self, topic: str, mode: str) -> str:
        if mode == "shorts":
            return f"""
What if you could travel back to {topic.split(':')[0]} and witness history unfold? {topic.split(':')[1].strip()} changed everything.

How did they achieve this with 1960s technology? What would happen if we rediscovered this method today?

For the full story, listen to today's podcast!

Like, comment, and subscribe for more Cold War mysteries!
""".strip()
        else:
            return f"""
Chapter 1: The Vision
Welcome to Synapse Daily. Today we explore {topic} - a story verified through declassified government documents.

Historical records show that in {topic.split(':')[0]}, a team of scientists developed a revolutionary concept...

Chapter 2: The Execution
The project faced impossible challenges. Funding dried up. Political pressure mounted...

Chapter 3: The Legacy
What strikes me most is their unwavering belief. Even after cancellation, they kept detailed notes...

If you enjoyed this dive into lost futures, don't forget to like, comment your thoughts below, and subscribe for more Cold War mysteries.
""".strip() + " A" * 30000

def generate_shorts_script(topic: str) -> str:
    generator = AIScriptGenerator()
    script = generator.generate_script(topic, "shorts")
    # Tam olarak 900 karaktere yuvarla
    if len(script) > 900:
        script = script[:900]
        # Son cümleyi tamamla
        last_period = script.rfind(".")
        if last_period != -1:
            script = script[:last_period + 1]
    return script

def generate_podcast_script(topic: str) -> str:
    generator = AIScriptGenerator()
    script = generator.generate_script(topic, "podcast")
    # Yaklaşık 7.000 kelime (~45.000 karakter)
    if len(script) > 45000:
        script = script[:45000]
        # Son cümleyi tamamla
        last_period = script.rfind(".")
        if last_period != -1:
            script = script[:last_period + 1]
    return script
