# src/script_generator.py
import os
import requests
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def get_shorts_prompt(topic: str) -> str:
    """Shorts için 1000 karakterlik güçlü prompt."""
    return f"""
You are the narrator of 'Synapse Daily' – a channel about Cold War tech and lost futures.
Write a **YouTube Shorts script** about: {topic}

RULES:
- Start with a HOOK that grabs attention in 5 seconds: "What if you could...?" or "Imagine..."
- Include 1 PERSONAL TOUCH: "I couldn't believe this existed!" or "Shocking, right?"
- End with: "Don't forget to like, comment, and subscribe for more lost futures!"
- Tone: Thoughtful, nostalgic, curious — but FAST-PACED.
- NO markdown, NO explanations — just the script.
- TOTAL CHARACTERS: MAX 1000 (strict!).

Script:
""".strip()

def get_podcast_prompt(topic: str) -> str:
    """Podcast için 15.000 karakterlik derinlemesine prompt."""
    return f"""
You are the narrator of 'Synapse Daily', exploring Cold War oddities and unbuilt utopias.
Write a **podcast script** about: {topic}

STRUCTURE:
1. **HOOK (0:00-0:15)**: Start with a vivid, cinematic question or image. Example: "If you had 20 minutes to explore a city before vanishing forever, which would you choose? In the 1970s, Soviet architects dreamed of exactly that..."

2. **STORYTELLING**: Frame facts around a PERSON, DECISION, or CONFLICT. Example: "Meet Dr. Ivan Petrov – the engineer who risked his life to build..."

3. **TENSION & CURIOSITY**: Ask "Why?" and "What happened next?" Reveal information in layers.

4. **PERSONAL VOICE**: Use 2-3 subjective phrases: "I find this haunting...", "What strikes me is...", "I couldn't sleep after reading this..."

5. **RHYTHM**: Short sentences. Use transitions: "But here's the twist...", "Now, the real story begins..."

6. **CALL TO ACTION (LAST 15 SECONDS)**: 
   "If you enjoyed this dive into lost futures, don't forget to like, comment your thoughts below, and subscribe for more Cold War mysteries. What forgotten project should we explore next?"

7. **TONE**: Thoughtful, nostalgic, curious — never dry or academic. Speak to history lovers who crave depth but hate boredom.

RULES:
- TOTAL CHARACTERS: MAX 15,000 (strict!)
- Language: Fluent English
- NO markdown, NO section headers — just pure script.
- END WITH CTA.

Script:
""".strip()

def generate_script(topic: str, mode: str = "shorts") -> str:
    """
    Konuya göre script üret.
    mode: 'shorts' veya 'podcast'
    """
    if mode == "shorts":
        prompt = get_shorts_prompt(topic)
        max_chars = Config.SHORTS_CHAR_LIMIT
    else:
        prompt = get_podcast_prompt(topic)
        max_chars = Config.PODCAST_CHAR_LIMIT

    logger.info(f"🧠 Script oluşturuluyor ({mode})...")
    
    # Hugging Face Inference API çağrısı (DOĞRU URL!)
    headers = {
        "Authorization": f"Bearer {Config.HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300 if mode == "shorts" else 4000,
            "temperature": 0.75,
            "top_p": 0.9,
            "repetition_penalty": 1.15,
            "return_full_text": False
        }
    }
    
    # DOĞRU API URL
    response = requests.post(
        "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-1B",
        headers=headers,
        json=payload
    )
    
    # Yanıtı kontrol et
    if response.status_code != 200:
        logger.error(f"HF API hatası: {response.status_code} - {response.text}")
        # Hata durumunda örnek script döndür
        fallback_script = f"This is a test script for {topic}. Don't forget to like, comment, and subscribe!"
        return fallback_script[:max_chars]
    
    # Yanıttan metni al
    try:
        result = response.json()
        script = result[0]['generated_text'].strip()
    except Exception as e:
        logger.error(f"JSON parse hatası: {str(e)}")
        fallback_script = f"This is a test script for {topic}. Don't forget to like, comment, and subscribe!"
        return fallback_script[:max_chars]
    
    # Karakter sınırını ZORLA
    if len(script) > max_chars:
        script = script[:max_chars-50] + "... " + script[-50:]
    
    # CTA eksikse EKLE (güvenlik önlemi)
    cta_phrases = [
        "like, comment, and subscribe",
        "don't forget to like and subscribe",
        "subscribe for more"
    ]
    
    if not any(phrase in script.lower() for phrase in cta_phrases):
        cta = " Don't forget to like, comment, and subscribe for more lost futures!"
        if len(script) + len(cta) <= max_chars:
            script += cta
    
    logger.info(f"✅ Script hazır! ({len(script)} karakter)")
    return script
