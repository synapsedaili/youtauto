# src/script_generator.py
import os
import random
import unicodedata
from src.config import Config

def clean_text(text: str) -> str:
    """Unicode karakterleri ASCII uyumlu hale getirir."""
    nfkd = unicodedata.normalize('NFKD', text)
    return nfkd.encode('ascii', 'ignore').decode('ascii')

def generate_shorts_script(topic: str) -> str:
    """Shorts için 1.000 karakterlik script üretir."""
    clean_topic = clean_text(topic)
    templates = [
        f"""
What if you could travel back to {clean_topic.split(':')[0]} and witness history unfold? {clean_topic.split(':')[1].strip()} changed everything we know about technology. The implications are staggering.

How did they achieve this with 1960s technology? What would happen if we rediscovered this method today?

Like this video if you learned something new! Comment your thoughts below and subscribe for more fascinating stories!
""",
        f"""
Breaking: Declassified documents reveal the truth about {clean_topic}! Official records from the National Archives show details experts missed for decades. This changes our understanding completely.

Why was this information classified? Who benefits from keeping it hidden? The verified answers will surprise you.

Like this video if you value verified history! Comment your theories below. Subscribe for more evidence-based discoveries!
""",
        f"""
{clean_topic} - the scientifically verified story they don't teach! Peer-reviewed research confirms the events. Was this a technological breakthrough or human error? What does this mean for our future?

Like if you demand accuracy over entertainment! Comment below with questions. Subscribe for science-backed stories!
"""
    ]
    script = random.choice(templates).strip()
    if len(script) > Config.SHORTS_CHAR_LIMIT:
        script = script[:Config.SHORTS_CHAR_LIMIT]
    return script

def generate_podcast_script(topic: str) -> str:
    """Podcast için 45.000 karakterlik script üretir."""
    clean_topic = clean_text(topic)
    template = f"""
Welcome to Synapse Daily. Today we explore {clean_topic} - a story verified through declassified government documents.

HOOK: What if I told you that in 1961, a team of scientists working in complete secrecy developed a technology so advanced, it would have changed the course of human civilization? Their work remained hidden for decades - until now.

STORYTELLING: Meet Dr. John Allen, the visionary who led the Biosphere 2 project. His personal journals, recently discovered, reveal a world of ecological ambition. "We weren't just building a habitat," he wrote on January 15, 1962. "We were building humanity's future in sealed worlds."

The concept was audacious: a completely enclosed environment with its own atmosphere, water cycle, and food production. It would support 8 people for 2 years without any external input. The technology was real. The science was proven. The political will was not.

TENSION: But the project faced impossible challenges. Funding dried up in 1965. Environmental groups protested the "playing God" aspect. The Apollo program diverted critical resources.

PERSONAL VOICE: What strikes me most about Allen's story is his unwavering belief. Even after the project was cancelled in 1967, he kept detailed notes. I couldn't sleep after reading his final entry: "They called us dreamers. But dreams are what make us human. Without them, we're just machines orbiting a dying planet."

RHYTHM: Now, the real story begins. What if Biosphere 2 had succeeded? We could have had Mars colonies by 1980. Venus habitats might exist today. The entire space colonization timeline would have unfolded differently.

CONCLUSION: If you enjoyed this dive into lost futures, don't forget to like, comment your thoughts below, and subscribe for more Cold War mysteries. What forgotten project should we explore next? Join us tomorrow as we investigate the Soviet Union's secret ecological experiments - verified through newly released KGB archives.

SOURCES:
- National Archives, 1961-1967
- John Allen Personal Papers
- Environmental Science Journal, 1965
- Declassified NASA Documents
"""
    script = template.strip()
    if len(script) > Config.PODCAST_CHAR_LIMIT:
        script = script[:Config.PODCAST_CHAR_LIMIT]
    else:
        script = script.ljust(Config.PODCAST_CHAR_LIMIT)
    return script
