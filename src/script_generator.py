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
                if mode == "podcast":
                    script = self._generate_podcast_in_chunks(topic, func)
                else:
                    script = func(topic, mode)
                if script and len(script) > 100:
                    logger.info(f"✅ {name.upper()} success!")
                    return clean_text(script)
            except Exception as e:
                logger.warning(f"⚠️ {name.upper()} failed: {str(e)}")
                continue
        
        logger.error("🔥 ALL PROVIDERS FAILED! Using fallback.")
        return self._generate_fallback_script(topic, mode)
    
    def _create_prompt(self, topic: str, mode: str, context: str = "") -> str:
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
            if context:
                return f"""{base_rules}
Continue the following podcast script naturally. Maintain Chapter structure and factual accuracy.

Previous context (do not repeat):
"{context[-500:]}"...

Now continue the story about: "{topic}"

- Keep storytelling style
- Add new verified facts
- Do NOT summarize or conclude yet
- Stop mid-sentence if approaching limit

CONTINUATION:"""
            else:
                return f"""{base_rules}
Write the BEGINNING of a 7,000-word YouTube podcast script about: "{topic}"
- Structure: Chapter 1, Chapter 2, ...
- Each chapter: clear title, storytelling, verified facts
- Do NOT conclude; this is only the first part
- Stop mid-sentence if approaching limit

BEGINNING:"""
    
    def _generate_podcast_in_chunks(self, topic: str, generate_func) -> str:
        """Podcast metnini 3 parçada üret ve birleştir."""
        full_script = ""
        context = ""
        
        for i in range(3):
            logger.info(f"챕터 {i+1}/3 üretiliyor...")
            prompt = self._create_prompt(topic, "podcast", context)
            
            # Token sınırına göre tahmini maks karakter
            max_chars = 18000  # ~12.000 token
            
            try:
                chunk = generate_func.__func__(self, topic, "podcast", custom_prompt=prompt)
                if not chunk:
                    break
                
                # Önceki bağlamı tekrar etme
                if full_script:
                    full_script += " " + chunk
                else:
                    full_script = chunk
                
                # Sonraki parça için bağlam
                context = full_script
                
                # Eğer içerik yeterliyse dur
                if len(full_script) > 42000:
                    break
                    
            except Exception as e:
                logger.warning(f"Chunk {i+1} başarısız: {e}")
                break
        
        # Son cümleyi tamamla
        if len(full_script) > 45000:
            full_script = full_script[:45000]
            last_period = full_script.rfind(".")
            if last_period != -1:
                full_script = full_script[:last_period + 1]
        
        return full_script
    
    def _generate_with_gemini(self, topic: str, mode: str, custom_prompt=None) -> str:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing")
        
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": custom_prompt or self._create_prompt(topic, mode)}]}],
            "generationConfig": {
                "maxOutputTokens": 8192,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    
    def _generate_with_qwen(self, topic: str, mode: str, custom_prompt=None) -> str:
        return self._generate_with_ollama_model(topic, mode, "qwen2:1.5b", custom_prompt)
    
    def _generate_with_deepseek(self, topic: str, mode: str, custom_prompt=None) -> str:
        return self._generate_with_ollama_model(topic, mode, "deepseek-r1:1.3b", custom_prompt)
    
    def _generate_with_ollama_model(self, topic: str, mode: str, model_name: str, custom_prompt=None) -> str:
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": custom_prompt or self._create_prompt(topic, mode),
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
    if len(script) > 900:
        script = script[:900]
        last_period = script.rfind(".")
        if last_period != -1:
            script = script[:last_period + 1]
    return script

def generate_podcast_script(topic: str) -> str:
    generator = AIScriptGenerator()
    script = generator.generate_script(topic, "podcast")
    return script
