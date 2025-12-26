# src/script_generator.py
import requests
import json
import time
import re
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def clean_script_text(script: str) -> str:
    """Metni temizler: başlıkları, markdown kalıntılarını kaldırır."""
    # Başlıkları temizle (**HOOK**, **STORYTELLING** vb.)
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
    
    return script.strip()

class QwenAPI:
    """Qwen AI entegrasyonu - Hugging Face üzerinden çalışıyor"""
    
    def __init__(self):
        """Qwen API ayarları"""
        self.api_url = "https://api-inference.huggingface.co/models/Qwen/Qwen1.5-1.8B-Chat"
        
    def generate_content(self, prompt: str, max_tokens: int = 1000) -> str:
        """Qwen API ile içerik üret"""
        headers = {
            "Authorization": f"Bearer {Config.HF_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
                "repetition_penalty": 1.15,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=120  # 2 dakika timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0]['generated_text'].strip()
                elif isinstance(result, dict) and 'generated_text' in result:
                    return result['generated_text'].strip()
            
            logger.error(f"❌ Qwen API hatası: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Qwen API çağrısı hatası: {str(e)}")
            return None

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
    """
    Qwen AI ile dinamik script üret.
    mode: 'shorts' veya 'podcast'
    """
    logger.info(f"🧠 {mode.upper()} script oluşturuluyor: '{topic}'")
    
    # Qwen API başlat
    qwen_api = QwenAPI()
    
    # Prompt seç
    if mode == "shorts":
        prompt = get_shorts_prompt(topic)
        max_tokens = 300  # ~1000 karakter
        max_chars = Config.SHORTS_CHAR_LIMIT
    else:
        prompt = get_podcast_prompt(topic)
        max_tokens = 4000  # ~15,000 karakter
        max_chars = Config.PODCAST_CHAR_LIMIT
    
    # Qwen ile script üret
    raw_script = qwen_api.generate_content(prompt, max_tokens)
    
    # Fallback mekanizması
    if not raw_script or len(raw_script.strip()) < 100:
        logger.warning("⚠️ Qwen API başarısız oldu, Fallback script kullanılıyor...")
        if mode == "shorts":
            fallback = f"""
What if you could travel back to 1960 and witness {topic}?

In the Cold War era, scientists imagined a world where this technology could change everything.

The concept was revolutionary. It wasn't science fiction — it was real physics, real engineering.

But why was it cancelled? What were the risks?

Join us next time for more Cold War mysteries. Don't forget to like, comment, and subscribe!
            """
        else:
            fallback = f"""
Welcome to Synapse Daily. Today we dive deep into {topic}.

HOOK: Imagine a world where {topic.lower()} could change the course of human history.

STORYTELLING: The story begins with a single scientist who dared to dream big. His name was... [Continue with detailed historical facts]

TENSION: But the project faced enormous challenges. Political pressure mounted. Safety concerns grew.

PERSONAL VOICE: What strikes me most is how this represents a time when humanity dared to dream big.

CONCLUSION: If you enjoyed this dive into lost futures, don't forget to like, comment, and subscribe for more Cold War mysteries.
            """
        raw_script = fallback
    
    # Metni temizle
    cleaned_script = clean_script_text(raw_script)
    
    # Karakter sınırını ZORLA
    if len(cleaned_script) > max_chars:
        cleaned_script = cleaned_script[:max_chars-50] + "... " + cleaned_script[-50:]
    
    logger.info(f"✅ {mode.upper()} script hazır! ({len(cleaned_script)} karakter)")
    return cleaned_script
