# src/script_generator.py
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def generate_script(topic: str, mode: str = "shorts") -> str:
    """
    Sabit metin üretici.
    mode: 'shorts' veya 'podcast'
    """
    if mode == "shorts":
        # Shorts için 1 dk'lık anlamlı metin
        script = f"""
What if you could travel back to 1960 and witness Project Orion - the nuclear-powered spaceship that could have changed space travel forever?

In the Cold War era, scientists imagined a world where atomic bombs could propel spacecraft to distant stars. Project Orion was born from this dream.

The concept was revolutionary: drop nuclear bombs behind a massive spacecraft, and use the explosion to push it forward. It wasn't science fiction - it was real physics, real engineering.

But why was it cancelled? What were the risks? And could we build it today?

Join us next time for more Cold War mysteries. Don't forget to like, comment, and subscribe for more lost futures!
        """.strip()
    else:
        # Podcast için 15 dk'lık anlamlı metin
        script = f"""
Welcome to Synapse Daily. Today we dive deep into Project Orion - the nuclear-powered spaceship that almost was.

HOOK: Imagine a world where atomic explosions didn't just destroy - they propelled humanity to the stars. This was the vision behind Project Orion in 1960.

STORYTELLING: Meet Dr. Freeman Dyson, the brilliant physicist who believed we could reach Mars by 1965 using nuclear pulse propulsion. His team at General Atomics worked tirelessly to make this dream a reality.

The concept was simple yet audacious. A massive spacecraft would drop nuclear bombs behind it. Each explosion would hit a pusher plate, propelling the ship forward. The crew would experience a gentle push - like being on an elevator.

TENSION: But the project faced enormous challenges. The Partial Test Ban Treaty of 1963 made nuclear tests in space illegal. Political pressure mounted. The Apollo program took priority.

PERSONAL VOICE: What strikes me most about Orion is how it represents a time when humanity dared to dream big. Today we're limited by safety, cost, and bureaucracy. But in the 1960s, nothing seemed impossible.

The technology was proven on paper. Tests with chemical explosives showed the concept worked. But politics killed the dream.

RHYTHM: Now, the real story begins. What if Orion had succeeded? We could have had lunar bases by 1970, Mars colonies by 1980. The entire space race would have unfolded differently.

CONCLUSION: If you enjoyed this dive into lost futures, don't forget to like, comment your thoughts below, and subscribe for more Cold War mysteries. What forgotten project should we explore next?
        """.strip()

    # Karakter limitine göre kırp
    if mode == "shorts":
        script = script[:Config.SHORTS_CHAR_LIMIT]
    else:
        script = script[:Config.PODCAST_CHAR_LIMIT]

    logger.info(f"✅ {mode.upper()} metni hazır! ({len(script)} karakter)")
    return script
