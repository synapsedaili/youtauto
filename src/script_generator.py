# src/script_generator.py
import os
import requests
import logging
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def clean_text(text: str) -> str:
    """Unicode karakterleri temizler."""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', text)
    return nfkd.encode('ascii', 'ignore').decode('ascii')

class AIScriptGenerator:
    def __init__(self):
        # Sadece Ollama tabanlı sağlayıcılar
        self.providers = [
            ("qwen", self._generate_with_qwen),
            ("deepseek", self._generate_with_deepseek),
            ("ollama", self._generate_with_ollama_fallback)
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
        
        logger.error("🔥 ALL PROVIDERS FAILED! Using enhanced fallback.")
        return self._generate_enhanced_fallback(topic, mode)
    
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
Write a 7,000-word YouTube podcast script about: "{topic}"

Structure your response EXACTLY as follows:

Chapter 1: [Descriptive Title]
[Engaging narrative paragraph...]

Chapter 2: [Descriptive Title]
[New developments, verified facts...]

Chapter 3: [Descriptive Title]
[Legacy, modern relevance...]

Final CTA:
Like this video if you learned something new! Comment your thoughts below and subscribe for more fascinating stories!

DO NOT include any technical markers like [HOOK], [VOICE ON], or brackets.
ONLY return pure narrative text with chapter headings.
SCRIPT:"""
    
    def _generate_podcast_in_chunks(self, topic: str, generate_func) -> str:
        full_script = ""
        context = ""
        
        for i in range(3):
            logger.info(f"챕터 {i+1}/3 üretiliyor...")
            prompt = self._create_prompt(topic, "podcast", context)
            
            try:
                chunk = generate_func(topic, "podcast", custom_prompt=prompt, timeout=300)
                if not chunk:
                    break
                
                if full_script:
                    full_script += " " + chunk
                else:
                    full_script = chunk
                
                context = full_script
                if len(full_script) > 42000:
                    break
                    
            except Exception as e:
                logger.warning(f"Chunk {i+1} başarısız: {e}")
                break
        
        if len(full_script) > 45000:
            full_script = full_script[:45000]
            last_period = full_script.rfind(".")
            if last_period != -1:
                full_script = full_script[:last_period + 1]
        
        return full_script
    
    def _generate_with_qwen(self, topic: str, mode: str, custom_prompt=None, timeout=120) -> str:
        return self._generate_with_ollama_model(topic, mode, "qwen2:0.5b-q4_K_M", custom_prompt, timeout)

    def _generate_with_deepseek(self, topic: str, mode: str, custom_prompt=None, timeout=120) -> str:
        return self._generate_with_ollama_model(topic, mode, "deepseek-r1:1.3b-q4_K_M", custom_prompt, timeout)

    def _generate_with_ollama_fallback(self, topic: str, mode: str, custom_prompt=None, timeout=120) -> str:
        return self._generate_with_ollama_model(topic, mode, "llama3.2:1b-q4_K_M", custom_prompt, timeout)

    def _generate_with_ollama_model(self, topic: str, mode: str, model_name: str, custom_prompt=None, timeout=120) -> str:
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
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()["response"].strip()
    
    def _generate_enhanced_fallback(self, topic: str, mode: str) -> str:
        year = topic.split(":")[0].strip() if ":" in topic else "1960s"
        title = topic.split(":", 1)[1].strip() if ":" in topic else topic
        
        if mode == "shorts":
            return f"""
In {year}, engineers dreamed of building {title}. This wasn't science fiction—it was real Cold War ambition.

How did they plan to construct it? What made it revolutionary?

For the full story, listen to today's podcast!

Like, comment, and subscribe for more Cold War mysteries!
""".strip()
        else:
            return f"""
Chapter 1: The Vision of {year}
In {year}, amid the height of the Space Race, NASA proposed a radical idea: {title}. Historical records from the National Archives reveal this was more than a concept—it was a detailed blueprint for modular space habitation.

Chapter 2: Engineering the Impossible
The design required stacking massive modules in orbit. Engineers at Langley Research Center developed novel docking systems. Declassified memos show concerns about radiation shielding and life support sustainability.

Chapter 3: Why It Never Flew
Despite technical feasibility, budget cuts after Apollo redirected funds. Political will evaporated by 1966. Yet, its legacy lives on in the International Space Station's modular design.

If you enjoyed this dive into lost futures, don't forget to like, comment your thoughts below, and subscribe for more Cold War mysteries.
""".strip().ljust(45000)

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
