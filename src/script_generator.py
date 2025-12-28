# src/script_generator.py
import os
import requests
import json
import logging
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
    """Podcast için 22.500 karakterlik derinlemesine prompt."""
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
- TOTAL CHARACTERS: MAX 22,500 (strict!)
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
    
    # Hugging Face Inference API çağrısı
    headers = {
        "Authorization": f"Bearer {Config.HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 400 if mode == "shorts" else 4000,
            "temperature": 0.7,
            "top_p": 0.9,
            "repetition_penalty": 1.1,
            "return_full_text": False
        }
    }
    
    try:
        # API çağrısı yap
        response = requests.post(
            "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-1B",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        # Yanıtı kontrol et
        if response.status_code != 200:
            logger.error(f"HF API hatası: {response.status_code} - {response.text}")
            raise Exception(f"API hatası: {response.status_code}")
        
        # Yanıttan metni al
        result = response.json()
        
        # Yanıt formatına göre metni al
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], dict) and "generated_text" in result[0]:
                script = result[0]['generated_text'].strip()
            else:
                script = str(result[0]).strip()
        else:
            script = str(result).strip()
        
        logger.info(f"✅ API'den script alındı! ({len(script)} karakter)")
    
    except Exception as e:
        logger.error(f"API çağrısı hatası: {str(e)}")
        # Fallback metin oluştur
        if mode == "shorts":
            script = f"""
What if you could travel back to 1960 and witness {topic} - the project that could have changed everything?

During the Cold War, scientists and engineers dreamed big. They imagined technologies that would transform our world - some succeeded, most failed.

This is one of those forgotten stories. A project that was ahead of its time, limited only by politics and budget constraints, not by imagination.

Why did it fail? What could it have become? And most importantly - what can we learn from it today?

Join us next time for more Cold War mysteries. Don't forget to like, comment, and subscribe for more lost futures!
            """.strip()
        else:
            script = f"""
Welcome to Synapse Daily. Today we explore one of the Cold War's most fascinating forgotten projects: {topic}.

HOOK: What if I told you that in the shadow of the Space Race, governments were funding technologies so advanced, they would seem like science fiction even today?

STORYTELLING: Our story begins in the early 1960s, when engineers and scientists around the world were pushing the boundaries of what was possible. Behind closed doors, in laboratories hidden from public view, they were developing technologies that promised to revolutionize everything from transportation to computing.

The driving force was simple: whoever controlled these technologies would control the future. This wasn't just about military advantage - it was about shaping the world that would emerge after the Cold War.

TENSION: But there was a problem. These technologies were expensive, complex, and often dangerous. The public grew concerned. Politicians demanded results. Budgets were cut. And one by one, these ambitious projects were shelved, classified, or simply forgotten.

PERSONAL VOICE: What strikes me most about these stories is not just the technological ambition, but the human element. The engineers who spent decades on projects that would never see the light of day. The scientists who believed they were building a better future, only to see their work abandoned.

RHYTHM: Now, let's dive deeper. What exactly was this project? Who were the people behind it? And why does it matter today?

CONCLUSION: If you enjoyed this exploration of {topic}, don't forget to like, comment your thoughts below, and subscribe for more Cold War mysteries. What forgotten project should we explore next?
            """.strip()
    
    # Karakter sınırını ZORLA
    if len(script) > max_chars:
        script = script[:max_chars-150] + "... " + script[-150:]
    
    # CTA (Call to Action) kontrolü
    cta_phrases = [
        "like, comment, and subscribe",
        "don't forget to like and subscribe",
        "subscribe for more",
        "join us next time"
    ]
    
    has_cta = any(phrase in script.lower() for phrase in cta_phrases)
    
    if not has_cta:
        cta = " Don't forget to like, comment, and subscribe for more lost futures!"
        if len(script) + len(cta) <= max_chars:
            script += cta
    
    # Temiz metin döndür
    script = script.strip()
    logger.info(f"✅ Son script hazır! ({len(script)} karakter)")
    return script
