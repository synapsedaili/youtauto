# src/script_generator.py
import os
import random
import requests
import json
import logging
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def clean_text(text: str) -> str:
    """Unicode karakterleri ASCII uyumlu hale getirir."""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', text)
    return nfkd.encode('ascii', 'ignore').decode('ascii')

class AIScriptGenerator:
    def __init__(self):
        self.providers = [
            ("gemini", self._generate_with_gemini),
            ("qwen", self._generate_with_qwen),
            ("ollama", self._generate_with_ollama)
        ]
    
    def generate_script(self, topic: str, mode: str) -> str:
        """AI sağlayıcılarını sırayla dener."""
        for name, func in self.providers:
            try:
                logger.info(f"🔄 {name.upper()} ile script deneniyor...")
                script = func(topic, mode)
                if script and len(script) > 100:
                    logger.info(f"✅ {name.upper()} başarıyla çalıştı!")
                    return clean_text(script)
            except Exception as e:
                logger.warning(f"⚠️ {name.upper()} başarısız: {str(e)}")
                continue
        
        # Tümü başarısızsa fallback
        logger.error("🔥 TÜM SAĞLAYICILAR BAŞARISIZ! Fallback script kullanılıyor.")
        return self._generate_fallback_script(topic, mode)
    
    def _generate_with_gemini(self, topic: str, mode: str) -> str:
        """Google Gemini API ile script üretimi."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY eksik")
        
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        prompt = self._create_prompt(topic, mode)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 8000 if mode == "podcast" else 1000,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    
    def _generate_with_qwen(self, topic: str, mode: str) -> str:
        """Qwen API ile script üretimi."""
        api_key = os.environ.get("QWEN_API_KEY")
        if not api_key:
            raise ValueError("QWEN_API_KEY eksik")
        
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        prompt = self._create_prompt(topic, mode)
        payload = {
            "model": "qwen-max",
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {
                "max_tokens": 8000 if mode == "podcast" else 1000,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["output"]["choices"][0]["message"]["content"].strip()
    
    def _generate_with_ollama(self, topic: str, mode: str) -> str:
        """Ollama API ile script üretimi (localhost)."""
        url = "http://localhost:11434/api/generate"
        prompt = self._create_prompt(topic, mode)
        
        payload = {
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 8000 if mode == "podcast" else 1000
            }
        }
        
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result["response"].strip()
    
    def _create_prompt(self, topic: str, mode: str) -> str:
        """Profesyonel YouTube script prompt'u."""
        base_rules = """
You are a professional Cold War historian and YouTube content creator. All information must be FACTUALLY ACCURATE and VERIFIABLE.
- NEVER invent facts, statistics, quotes, or historical events
- If unsure, say "Historical records show..." or "According to verified sources..."
- Base everything on real historical/scientific evidence
- Include verification notes like "(CIA Archives, 1963)"
"""
        if mode == "shorts":
            return f"""{base_rules}
Write a 60-second YouTube Shorts script about: "{topic}"
- Start with SHOCKING HOOK (first 3 seconds)
- Include 2-3 curiosity questions
- Use vivid storytelling
- Short sentences (max 8 words)
- End with CTA: "Like, comment, subscribe!"
- Total characters: 800-1000
SCRIPT:"""
        else:
            return f"""{base_rules}
Write a 45,000-character YouTube podcast script about: "{topic}"
- Start with POWERFUL HOOK (first 30 seconds)
- Include REAL human stories with names/dates
- 4-5 rhetorical questions
- Technical details with context
- Verification notes in parentheses
- End with CTA
- EXACTLY 45,000 characters
SCRIPT:"""
    
    def _generate_fallback_script(self, topic: str, mode: str) -> str:
        """Acil durum fallback script'i."""
        if mode == "shorts":
            templates = [f"What if you could travel back to {topic.split(':')[0]}... Like this video if you learned something new!"]
            return random.choice(templates)
        else:
            return f"Welcome to Synapse Daily. Today we explore {topic}..." + "A" * 44000

# Ana fonksiyonlar
def generate_shorts_script(topic: str) -> str:
    generator = AIScriptGenerator()
    script = generator.generate_script(topic, "shorts")
    if len(script) > Config.SHORTS_CHAR_LIMIT:
        script = script[:Config.SHORTS_CHAR_LIMIT]
    return script

def generate_podcast_script(topic: str) -> str:
    generator = AIScriptGenerator()
    script = generator.generate_script(topic, "podcast")
    if len(script) > Config.PODCAST_CHAR_LIMIT:
        script = script[:Config.PODCAST_CHAR_LIMIT]
    else:
        script = script.ljust(Config.PODCAST_CHAR_LIMIT)
    return script
