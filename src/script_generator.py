# src/script_generator.py
import os
from huggingface_hub import InferenceClient
from src.config import Config

def get_shorts_prompt(topic: str) -> str:
    return f"""
You are the narrator of 'Synapse Daily' – a channel about Cold War tech and lost futures.
Write a 1000-character YouTube Shorts script about: {topic}

RULES:
- Start with a HOOK that grabs attention in 5 seconds.
- Include 1 PERSONAL TOUCH: "I couldn't believe this existed!"
- End with: "Don't forget to like, comment, and subscribe for more lost futures!"
- Tone: Thoughtful, nostalgic, curious — but FAST-PACED.
- TOTAL CHARACTERS: MAX 1000 (strict!).
- NO markdown, NO explanations — just the script.

Script:
""".strip()

def get_podcast_prompt(topic: str) -> str:
    return f"""
You are the narrator of 'Synapse Daily', exploring Cold War oddities and unbuilt utopias.
Write a 15,000-character podcast script about: {topic}

STRUCTURE:
1. HOOK (0:00-0:15): Start with a vivid question or image.
2. STORYTELLING: Frame facts around a PERSON, DECISION, or CONFLICT.
3. TENSION: Ask "Why?" and "What happened next?"
4. VISUAL CUES: Insert [GÖRSEL: description] for key moments.
5. PERSONAL VOICE: Use 2-3 subjective phrases.
6. RHYTHM: Short sentences, use transitions like "But here's the twist..."
7. CALL TO ACTION (LAST 15 SECONDS): 
   "If you enjoyed this dive into lost futures, don't forget to like, comment your thoughts below, and subscribe for more Cold War mysteries."

RULES:
- TOTAL CHARACTERS: EXACTLY 15,000
- Language: Fluent English
- NO markdown — just pure script.
- END WITH CTA.

Script:
""".strip()

def generate_script(topic: str, mode: str = "shorts") -> str:
    if mode == "shorts":
        prompt = get_shorts_prompt(topic)
        max_chars = 1000
    else:
        prompt = get_podcast_prompt(topic)
        max_chars = 15000

    client = InferenceClient(
        "meta-llama/Llama-3.2-1B",
        token=os.environ.get("HF_TOKEN")
    )

    response = client.text_generation(
        prompt,
        max_new_tokens=4000 if mode == "podcast" else 300,
        temperature=0.75,
        top_p=0.9,
        repetition_penalty=1.15
    )

    script = response.strip()[:max_chars]
    
    # CTA eksikse ekle
    if "like, comment, and subscribe" not in script.lower():
        cta = " Don't forget to like, comment, and subscribe for more lost futures!"
        if len(script) + len(cta) <= max_chars:
            script += cta
    
    return script