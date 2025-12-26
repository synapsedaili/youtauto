# src/script_generator.py
import requests
import json
import time
import re
import urllib.request
import os
from src.config import Config
from src.utils import setup_logging
import random

logger = setup_logging()

def clean_unicode(text: str) -> str:
    """Özel karakterleri temizle (UnicodeEncodeError önlemek için)."""
    # En dash (–) ve em dash (—) gibi karakterleri çıkar
    text = text.replace('\u2013', '-').replace('\u2014', '--')
    # Diğer özel karakterleri temizle
    return ''.join(char for char in text if ord(char) < 128 or char in 'çğıöşüÇĞİÖŞÜ')

def clean_script_text(script: str) -> str:
    """Metni temizler: başlıkları, markdown kalıntılarını kaldırır."""
    script = re.sub(r'\*\*[^*]+\*\*', '', script)
    
    # Markdown kalıntılarını kaldır
    script = re.sub(r'#+', '', script)
    script = re.sub(r'\*+', '', script)
    
    # Özel talimatları kaldır
    patterns = [
        r'\[GÖRSEL:.*?\]',
        r'\[Ses efekti.*?\]',
        r'HOOK:', r'TENSION:', r'STORYTELLING:',
        r'RHYTHM:', r'CONCLUSION:', r'PERSONAL VOICE:'
    ]
    for pattern in patterns:
        script = re.sub(pattern, '', script, flags=re.IGNORECASE)
    
    # Fazla boşlukları düzenle
    script = re.sub(r'\n{3,}', '\n\n', script)
    script = re.sub(r' {2,}', ' ', script)
    
    # İlk satırları temizle
    script = script.strip()
    lines = [line.strip() for line in script.split('\n') if line.strip() and not line.startswith(('**', '#', '-', '*'))]
    script = '\n'.join(lines)
    
    # CTA'yi koru
    if "like, comment, and subscribe" not in script.lower():
        cta = " Don't forget to like, comment, and subscribe for more lost futures!"
        script += cta
    
    # Unicode karakterleri temizle
    script = clean_unicode(script)
    
    return script.strip()

class ScriptGenerator:
    """3 katmanlı metin üretim sistemi"""
    
    def __init__(self):
        self.models = [
            self._generate_with_qwen,
            self._generate_with_llama,
            self._generate_fallback_template
        ]
        self.retry_count = 3
        self.timeout = 180  # 3 dakika
    
    def _generate_with_qwen(self, topic: str, mode: str) -> str:
        """1. Katman: Qwen AI (Hugging Face)"""
        logger.info("🧠 1. Katman: Qwen AI deneniyor...")
        
        # DOĞRU API URL (eski URL artık çalışmıyor!)
        api_url = "https://router.huggingface.co/models/Qwen/Qwen1.5-7B-Chat"
        headers = {
            "Authorization": f"Bearer {Config.HF_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Mode'a göre prompt
        prompt = get_shorts_prompt(topic) if mode == "shorts" else get_podcast_prompt(topic)
        max_tokens = 300 if mode == "shorts" else 4000
        
        for i in range(self.retry_count):
            try:
                response = requests.post(
                    api_url,
                    headers=headers,
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": max_tokens,
                            "temperature": 0.5,
                            "top_p": 0.9,
                            "repetition_penalty": 1.15
                        }
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return clean_script_text(result[0]['generated_text'].strip())
                
                logger.warning(f"⚠️ Qwen API hatası: {response.status_code}")
                
                # Rate limit ise bekle
                if response.status_code == 429:
                    wait_time = 60 * (i + 1)
                    logger.info(f"⏳ Rate limit aşıldı, {wait_time} sn bekleniyor...")
                    time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"❌ Qwen çağrısı hatası: {str(e)}")
            
            time.sleep(5)  # Her denemeden sonra bekle
        
        raise Exception("Qwen API başarısız")
    
    def _generate_with_llama(self, topic: str, mode: str) -> str:
        """2. Katman: Llama 3.2 (Hugging Face)"""
        logger.info("🧠 2. Katman: Llama 3.2 deneniyor...")
        
        # DOĞRU API URL
        api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct"
        headers = {
            "Authorization": f"Bearer {Config.HF_TOKEN}",
            "Content-Type": "application/json"
        }
        
        prompt = get_shorts_prompt(topic) if mode == "shorts" else get_podcast_prompt(topic)
        max_tokens = 300 if mode == "shorts" else 4000
        
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": max_tokens,
                        "temperature": 0.4,
                        "top_p": 0.85,
                        "repetition_penalty": 1.1
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return clean_script_text(result[0]['generated_text'].strip())
            
            logger.warning(f"⚠️ Llama API hatası: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Llama çağrısı hatası: {str(e)}")
        
        raise Exception("Llama API başarısız")
    
    def _generate_fallback_template(self, topic: str, mode: str) -> str:
        """3. Katman: Statik template (limitsiz)"""
        logger.info("🧠 3. Katman: Statik template kullanılıyor...")
        
        if mode == "shorts":
            templates = [
                f"""
What if you could travel back to 1960 and witness {topic}?

In the Cold War era, scientists imagined a world where this technology could change everything.

The concept was revolutionary. It wasn't science fiction — it was real physics, real engineering.

But why was it cancelled? What were the risks?

Join us next time for more Cold War mysteries. Don't forget to like, comment, and subscribe!
                """,
                f"""
Did you know about {topic}?

This secret Cold War project was so advanced that it was decades ahead of its time.

The technology they developed could have changed the course of history.

But something went wrong...

What do you think happened? Comment below! Don't forget to like and subscribe!
                """
            ]
        else:
            templates = [
                f"""
Welcome to Synapse Daily. Today we dive deep into {topic}.

Imagine a world where atomic explosions didn't just destroy — they propelled humanity to the stars. This was the vision behind Project Orion in 1960.

Meet Dr. Freeman Dyson, the brilliant physicist who believed we could reach Mars by 1965 using nuclear pulse propulsion. His team at General Atomics worked tirelessly to make this dream a reality.

The concept was simple yet audacious. A massive spacecraft would drop nuclear bombs behind it. Each explosion would hit a pusher plate, propelling the ship forward. The crew would experience a gentle push - like being on an elevator.

But the project faced enormous challenges. The Partial Test Ban Treaty of 1963 made nuclear tests in space illegal. Political pressure mounted. The Apollo program took priority.

What strikes me most about Orion is how it represents a time when humanity dared to dream big. Today we're limited by safety, cost, and bureaucracy. But in the 1960s, nothing seemed impossible.

If you enjoyed this dive into lost futures, don't forget to like, comment your thoughts below, and subscribe for more Cold War mysteries. What forgotten project should we explore next?
                """,
                f"""
Today we'll have a deep conversation about {topic}.

Our story began in the 1960s. At that time, scientists were dreaming very different dreams compared to today's technology.

This project file on Dr. Freeman Dyson's desk was one of humanity's most ambitious space adventures. Every morning, he would tell his team: "Today we're going to Mars."

But why were they so ambitious? There's a thin line between facts and myths.

When we dive into the details of the project, we'll encounter surprising truths. Some records show that the project actually succeeded. But why was it stopped?

The answer to this question lies hidden in the secret protocols of the Cold War era. We'll share this mystery with you.

In the next episode, we'll examine the technical details of the project and its effects on today's space travel. Stay tuned!
                """
            ]
        
        return clean_script_text(random.choice(templates).strip())
    
    def generate_script(self, topic: str, mode: str = "shorts") -> str:
        """3 katmanlı metin üretimi"""
        for model in self.models:
            try:
                script = model(topic, mode)
                if script and len(script) > 100:  # Geçerli metin kontrolü
                    logger.info(f"✅ {mode.upper()} script başarıyla üretildi!")
                    return script
            except Exception as e:
                logger.error(f"❌ Model hatası: {str(e)}")
                continue
        
        # Tüm modeller başarısız olursa
        logger.critical("🔥 TÜM MODELLER BAŞARISIZ OLDU! Acil fallback devreye giriyor...")
        return self._generate_fallback_template(topic, mode)

def get_shorts_prompt(topic: str) -> str:
    """Shorts için 60 saniyelik güçlü prompt."""
    return f"""
You are the narrator of 'Synapse Daily' – a channel about Cold War tech and lost futures.
Write a **YouTube Shorts script** about: {topic}

RULES:
✅ Start with a SHOCKING HOOK in the first 3 seconds
✅ Use REAL AND ACCURATE INFORMATION
✅ Include 1 PERSONAL TOUCH: "I couldn't believe this existed!"
✅ End with: "Don't forget to like, comment, and subscribe for more lost futures!"
✅ Tone: Thoughtful, nostalgic, curious — but FAST-PACED.
✅ TOTAL CHARACTERS: MAX 1000 (strict!)
✅ NO markdown, NO explanations — just the script.

EXAMPLE:
"What if you could travel back to 1960 and witness Project Orion — the nuclear-powered spaceship that almost changed everything?"

SCRIPT:
""".strip()

def get_podcast_prompt(topic: str) -> str:
    """Podcast için 15-20 dakikalık derinlemesine prompt."""
    return f"""
You are the narrator of 'Synapse Daily', exploring Cold War oddities and unbuilt utopias.
Write a **podcast script** about: {topic}

RULES:
✅ Start with a POWERFUL HOOK in the first 15 seconds
✅ Frame facts around a PERSON, DECISION, or CONFLICT
✅ Ask "Why?" and "What happened next?" to create tension
✅ Use 2-3 subjective phrases: "I find this haunting...", "What strikes me is..."
✅ Short sentences with smooth transitions: "But here's the twist...", "Now, the real story begins..."
✅ End with: "If you enjoyed this dive into lost futures, don't forget to like, comment, and subscribe."
✅ TOTAL CHARACTERS: MAX 15,000 (strict!)
✅ Language: Fluent English
✅ NO markdown, NO section headers — just pure script.
✅ NO visual instructions like [GÖRSEL: ...]

EXAMPLE HOOK:
"Imagine a world where atomic explosions didn't just destroy — they propelled humanity to the stars. This was the vision behind Project Orion in 1960."

SCRIPT:
""".strip()

def generate_script(topic: str, mode: str = "shorts") -> str:
    """Ana fonksiyon: 3 katmanlı sistem"""
    generator = ScriptGenerator()
    return generator.generate_script(topic, mode)
