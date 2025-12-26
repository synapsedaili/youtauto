# src/script_generator.py
import requests
import json
import time
import re
import urllib.request
import os
import random
from src.config import Config
from src.utils import setup_logging

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
        
        
        api_url = "https://api-inference.huggingface.co/models/Qwen/Qwen1.5-7B-Chat"
        headers = {
            "Authorization": f"Bearer {Config.HF_TOKEN}",
            "Content-Type": "application/json"
        }
        
        
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
            
            time.sleep(5)  
        
        raise Exception("Qwen API başarısız")
    
    def _generate_with_llama(self, topic: str, mode: str) -> str:
        """2. Katman: Llama 3.2 (Hugging Face)"""
        logger.info("🧠 2. Katman: Llama 3.2 deneniyor...")
        
        
        api_url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
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
        """3. Katman: Statik template (limitsiz ve her gün farklı)"""
        logger.info("🧠 3. Katman: Statik template kullanılıyor...")
        
        if mode == "shorts":
            templates = [
                f"""
What if you could travel back to 1960 and witness {topic}?

In the Cold War era, scientists imagined a world where this technology could change everything.

The concept was revolutionary. It wasn't science fiction — it was real physics, real engineering.

But why was it cancelled? What were the risks?

🔥 For the FULL PODCAST episode with exclusive archives, check our channel!
Don't forget to like, comment, and subscribe!
                """,
                f"""
Did you know about {topic}?

This secret Cold War project was so advanced that it was decades ahead of its time.

The technology they developed could have changed the course of history.

But something went wrong...

🔥 Listen to our FULL PODCAST to uncover the hidden documents!
Comment below! Don't forget to like and subscribe!
                """,
                f"""
Imagine walking into a room in 1960 and seeing {topic} for the first time.

The scientists who built it believed they were shaping the future of humanity.

Every detail was calculated with precision that seems impossible today.

What they discovered changed everything — and then it was buried.

🔥 The full story is in our PODCAST episode this week!
Like, comment, and subscribe to never miss a lost future!
                """,
                f"""
{topic} is a Cold War mystery that even CIA files couldn't fully explain.

The project was so secret that only 12 people knew its true purpose.

When the documents were finally declassified, historians were shocked.

What they found wasn't just a machine — it was a vision of a different future.

🔥 Want the full story? Listen to our PODCAST for never-before-seen archives!
Don't forget to like and subscribe for more lost futures!
                """,
                f"""
In a hidden laboratory in Nevada, scientists spent 5 years building {topic}.

The goal wasn't just technology — it was about controlling humanity's destiny.

Every test brought them closer to success, but also deeper into danger.

What happened on that final day in 1965 changed everything.

🔥 The complete investigation is in our PODCAST episode.
Like, comment your theories below! Subscribe for more!
                """,
                f"""
Have you ever heard of {topic}?

This Cold War technology was so advanced that it makes today's AI look primitive.

The engineers who designed it were decades ahead of their time.

But the project was cancelled under mysterious circumstances.

🔥 The untold story is in our FULL PODCAST episode this week!
Don't forget to like, comment, and subscribe for more lost futures!
                """,
                f"""
{topic} was one of the most ambitious projects of the 1960s.

The scientists involved believed they could change the course of human history.

Their work was so secret that even their families didn't know what they were doing.

What happened to their research is still classified today.

🔥 Discover the truth in our FULL PODCAST episode!
Like, comment, and subscribe to uncover more lost futures!
                """,
                f"""
What if I told you {topic} was real?

The evidence has been hidden for decades, but we've found the documents.

This technology could have revolutionized space travel, medicine, and energy.

But someone made sure it never saw the light of day.

🔥 The complete story is in our PODCAST episode this week.
Don't forget to like, comment, and subscribe!
                """,
                f"""
{topic} represents humanity's boldest attempt to control the future.

The project cost billions of dollars and involved the world's top scientists.

For 5 years, they worked in complete secrecy, away from public eyes.

Why was it shut down? The answer will shock you.

🔥 Listen to our FULL PODCAST for the untold story!
Like, comment, and subscribe for more lost futures!
                """,
                f"""
Deep in a Cold War bunker, scientists worked on {topic}.

Their mission: to create technology that would secure dominance for decades.

Every discovery they made was classified at the highest level.

Some say the project was successful — and its legacy lives on today.

🔥 The truth is in our FULL PODCAST episode this week!
Don't forget to like, comment, and subscribe!
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
                """,
                f"""
{topic} represents one of the most audacious dreams of the Cold War era.

We begin our journey in 1962, when a small team of engineers presented a blueprint that would change space travel forever. Their leader, Dr. Elena Morozova, had grown up watching Sputnik launch, and she dreamed of going further.

The project was code-named "Starlight". It wasn't just about reaching Mars — it was about creating a permanent human presence beyond Earth.

But behind the scenes, politics was unraveling their dream. The cost estimates grew, international tensions mounted, and by 1965, the project was cancelled.

What if Starlight had succeeded? We might be living on Mars today.

Join us next time as we explore more lost futures. If you enjoyed this episode, don't forget to like, comment, and subscribe!
                """,
                f"""
Welcome to Synapse Daily, where we uncover the technology that never was.

Today's topic: {topic}. This is a story of ambition, secrecy, and what could have been.

Picture this: It's 1964. A team of brilliant engineers at the height of the Cold War has developed a technology so advanced that it would take us another 50 years to rediscover it. Their leader, Dr. Vladimir Petrov, believed his invention could change the world.

The project was given unlimited funding and complete secrecy. For three years, they worked around the clock in a hidden facility beneath the Rocky Mountains.

But in 1967, everything changed. The project was shut down overnight. All records were classified, and the team was sworn to silence. What happened that day remains a mystery to this day.

What makes this story particularly haunting is that Dr. Petrov's notes suggest he knew something was coming. In his final journal entry, he wrote: "They don't understand what we've created. I fear for my family. Burn everything."

Join us next time as we explore more lost futures. If you enjoyed this episode, don't forget to like, comment your thoughts below, and subscribe for more Cold War mysteries.
                """,
                f"""
Today on Synapse Daily, we explore {topic}, a technology that could have rewritten human history.

In 1961, as the space race heated up, a small group of scientists at MIT began working on a revolutionary propulsion system. Their leader, Dr. Sarah Chen, was just 29 years old but already a pioneer in her field.

The concept was astonishingly simple yet brilliant. Instead of relying on chemical reactions, they would harness the power of quantum vacuum fluctuations. In layman's terms, they would sail on the fabric of spacetime itself.

The team made incredible progress. By 1963, they had built a working prototype that levitated silently in their laboratory. Dr. Chen's notes show she believed they could have a human-rated system ready by 1970.

But then came the political pressure. The military wanted weaponization. The budget was slashed. And in 1965, Dr. Chen disappeared from public records. Her final message to her team read: "Continue the work. The future depends on it."

We may never know what happened to Dr. Chen and her team. But their dream lives on in the pages of declassified documents and in the hearts of those who believe humanity's greatest achievements are still to come.

If you enjoyed this dive into lost futures, don't forget to like, comment, and subscribe. What forgotten project should we explore next?
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
✅ Mention: "Listen to our FULL PODCAST for more details!"
✅ Include 1 question to spark curiosity

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
✅ Mention connections to today's world
✅ Include at least one surprising fact that will shock listeners

EXAMPLE HOOK:
"Imagine a world where atomic explosions didn't just destroy — they propelled humanity to the stars. This was the vision behind Project Orion in 1960."

SCRIPT:
""".strip()

def generate_script(topic: str, mode: str = "shorts") -> str:
    """Ana fonksiyon: 3 katmanlı sistem"""
    generator = ScriptGenerator()
    return generator.generate_script(topic, mode)# src/script_generator.py
import requests
import json
import time
import re
import urllib.request
import os
import random
from src.config import Config
from src.utils import setup_logging

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
        
        
        api_url = "https://api-inference.huggingface.co/models/Qwen/Qwen1.5-7B-Chat"
        headers = {
            "Authorization": f"Bearer {Config.HF_TOKEN}",
            "Content-Type": "application/json"
        }
        
        
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
            
            time.sleep(5)  
        
        raise Exception("Qwen API başarısız")
    
    def _generate_with_llama(self, topic: str, mode: str) -> str:
        """2. Katman: Llama 3.2 (Hugging Face)"""
        logger.info("🧠 2. Katman: Llama 3.2 deneniyor...")
        
        
        api_url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
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
        """3. Katman: Statik template (limitsiz ve her gün farklı)"""
        logger.info("🧠 3. Katman: Statik template kullanılıyor...")
        
        if mode == "shorts":
            templates = [
                f"""
What if you could travel back to 1960 and witness {topic}?

In the Cold War era, scientists imagined a world where this technology could change everything.

The concept was revolutionary. It wasn't science fiction — it was real physics, real engineering.

But why was it cancelled? What were the risks?

🔥 For the FULL PODCAST episode with exclusive archives, check our channel!
Don't forget to like, comment, and subscribe!
                """,
                f"""
Did you know about {topic}?

This secret Cold War project was so advanced that it was decades ahead of its time.

The technology they developed could have changed the course of history.

But something went wrong...

🔥 Listen to our FULL PODCAST to uncover the hidden documents!
Comment below! Don't forget to like and subscribe!
                """,
                f"""
Imagine walking into a room in 1960 and seeing {topic} for the first time.

The scientists who built it believed they were shaping the future of humanity.

Every detail was calculated with precision that seems impossible today.

What they discovered changed everything — and then it was buried.

🔥 The full story is in our PODCAST episode this week!
Like, comment, and subscribe to never miss a lost future!
                """,
                f"""
{topic} is a Cold War mystery that even CIA files couldn't fully explain.

The project was so secret that only 12 people knew its true purpose.

When the documents were finally declassified, historians were shocked.

What they found wasn't just a machine — it was a vision of a different future.

🔥 Want the full story? Listen to our PODCAST for never-before-seen archives!
Don't forget to like and subscribe for more lost futures!
                """,
                f"""
In a hidden laboratory in Nevada, scientists spent 5 years building {topic}.

The goal wasn't just technology — it was about controlling humanity's destiny.

Every test brought them closer to success, but also deeper into danger.

What happened on that final day in 1965 changed everything.

🔥 The complete investigation is in our PODCAST episode.
Like, comment your theories below! Subscribe for more!
                """,
                f"""
Have you ever heard of {topic}?

This Cold War technology was so advanced that it makes today's AI look primitive.

The engineers who designed it were decades ahead of their time.

But the project was cancelled under mysterious circumstances.

🔥 The untold story is in our FULL PODCAST episode this week!
Don't forget to like, comment, and subscribe for more lost futures!
                """,
                f"""
{topic} was one of the most ambitious projects of the 1960s.

The scientists involved believed they could change the course of human history.

Their work was so secret that even their families didn't know what they were doing.

What happened to their research is still classified today.

🔥 Discover the truth in our FULL PODCAST episode!
Like, comment, and subscribe to uncover more lost futures!
                """,
                f"""
What if I told you {topic} was real?

The evidence has been hidden for decades, but we've found the documents.

This technology could have revolutionized space travel, medicine, and energy.

But someone made sure it never saw the light of day.

🔥 The complete story is in our PODCAST episode this week.
Don't forget to like, comment, and subscribe!
                """,
                f"""
{topic} represents humanity's boldest attempt to control the future.

The project cost billions of dollars and involved the world's top scientists.

For 5 years, they worked in complete secrecy, away from public eyes.

Why was it shut down? The answer will shock you.

🔥 Listen to our FULL PODCAST for the untold story!
Like, comment, and subscribe for more lost futures!
                """,
                f"""
Deep in a Cold War bunker, scientists worked on {topic}.

Their mission: to create technology that would secure dominance for decades.

Every discovery they made was classified at the highest level.

Some say the project was successful — and its legacy lives on today.

🔥 The truth is in our FULL PODCAST episode this week!
Don't forget to like, comment, and subscribe!
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
                """,
                f"""
{topic} represents one of the most audacious dreams of the Cold War era.

We begin our journey in 1962, when a small team of engineers presented a blueprint that would change space travel forever. Their leader, Dr. Elena Morozova, had grown up watching Sputnik launch, and she dreamed of going further.

The project was code-named "Starlight". It wasn't just about reaching Mars — it was about creating a permanent human presence beyond Earth.

But behind the scenes, politics was unraveling their dream. The cost estimates grew, international tensions mounted, and by 1965, the project was cancelled.

What if Starlight had succeeded? We might be living on Mars today.

Join us next time as we explore more lost futures. If you enjoyed this episode, don't forget to like, comment, and subscribe!
                """,
                f"""
Welcome to Synapse Daily, where we uncover the technology that never was.

Today's topic: {topic}. This is a story of ambition, secrecy, and what could have been.

Picture this: It's 1964. A team of brilliant engineers at the height of the Cold War has developed a technology so advanced that it would take us another 50 years to rediscover it. Their leader, Dr. Vladimir Petrov, believed his invention could change the world.

The project was given unlimited funding and complete secrecy. For three years, they worked around the clock in a hidden facility beneath the Rocky Mountains.

But in 1967, everything changed. The project was shut down overnight. All records were classified, and the team was sworn to silence. What happened that day remains a mystery to this day.

What makes this story particularly haunting is that Dr. Petrov's notes suggest he knew something was coming. In his final journal entry, he wrote: "They don't understand what we've created. I fear for my family. Burn everything."

Join us next time as we explore more lost futures. If you enjoyed this episode, don't forget to like, comment your thoughts below, and subscribe for more Cold War mysteries.
                """,
                f"""
Today on Synapse Daily, we explore {topic}, a technology that could have rewritten human history.

In 1961, as the space race heated up, a small group of scientists at MIT began working on a revolutionary propulsion system. Their leader, Dr. Sarah Chen, was just 29 years old but already a pioneer in her field.

The concept was astonishingly simple yet brilliant. Instead of relying on chemical reactions, they would harness the power of quantum vacuum fluctuations. In layman's terms, they would sail on the fabric of spacetime itself.

The team made incredible progress. By 1963, they had built a working prototype that levitated silently in their laboratory. Dr. Chen's notes show she believed they could have a human-rated system ready by 1970.

But then came the political pressure. The military wanted weaponization. The budget was slashed. And in 1965, Dr. Chen disappeared from public records. Her final message to her team read: "Continue the work. The future depends on it."

We may never know what happened to Dr. Chen and her team. But their dream lives on in the pages of declassified documents and in the hearts of those who believe humanity's greatest achievements are still to come.

If you enjoyed this dive into lost futures, don't forget to like, comment, and subscribe. What forgotten project should we explore next?
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
✅ Mention: "Listen to our FULL PODCAST for more details!"
✅ Include 1 question to spark curiosity

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
✅ Mention connections to today's world
✅ Include at least one surprising fact that will shock listeners

EXAMPLE HOOK:
"Imagine a world where atomic explosions didn't just destroy — they propelled humanity to the stars. This was the vision behind Project Orion in 1960."

SCRIPT:
""".strip()

def generate_script(topic: str, mode: str = "shorts") -> str:
    """Ana fonksiyon: 3 katmanlı sistem"""
    generator = ScriptGenerator()
    return generator.generate_script(topic, mode)
