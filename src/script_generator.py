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
        # Podcast için 15 dk'lık anlamlı metin (~13.500 karakter)
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

---

PROJECT DETAILS: Project Orion was first proposed in 1958 by physicist Stanislaw Ulam. The idea was to use nuclear pulse propulsion - essentially dropping atomic bombs behind a spacecraft and using the explosion to push it forward.

THE TEAM: Led by Ted Taylor and Freeman Dyson, the team at General Atomics believed they could build a 4000-ton spacecraft capable of reaching Mars in 100 days.

THE SHIP: The spacecraft would be equipped with a massive pusher plate, a 100-ton shock absorber system, and a crew of 50 people. It was designed to be launched from a salt flat in Nevada.

THE TESTS: Chemical Explosive Propulsion (CEP) tests were conducted in 1959. These tests proved that the concept worked on a small scale.

THE RISKS: The project faced enormous risks. Nuclear fallout, crew safety, and the possibility of accidents were major concerns.

THE COST: Estimated at $20 billion in today's money, the project was considered affordable compared to the Apollo program.

THE LEGACY: Although cancelled, Project Orion influenced future space travel concepts and remains a symbol of Cold War ambition.

---

COLD WAR CONTEXT: During the 1950s and 1960s, the United States and Soviet Union were locked in a race to explore space. Project Orion represented a bold attempt to leap ahead of the competition.

THE RACE: The Soviet Union's launch of Sputnik in 1957 accelerated the space race. Project Orion was seen as a way to reach Mars before the Soviets.

THE VISION: Scientists imagined a future where nuclear-powered ships could travel to the outer planets and beyond. The goal was to establish human colonies on Mars and other worlds.

THE FEAR: The Partial Test Ban Treaty of 1963 reflected growing concerns about nuclear weapons. The treaty banned nuclear tests in the atmosphere, underwater, and in outer space.

THE DECISION: The Kennedy administration ultimately chose to focus on the Apollo program, which aimed to land humans on the Moon by the end of the decade.

---

TECHNICAL SPECIFICATIONS: The Orion spacecraft was designed to be 135 feet in diameter and 180 feet tall. It would carry 2000 one-megaton nuclear bombs.

THE ENGINE: Each bomb would be dropped from the spacecraft and explode about 100 feet behind it. The explosion would hit the pusher plate and propel the ship forward.

THE SPEED: The spacecraft could theoretically reach speeds of 30,000 miles per hour, allowing it to reach Mars in just 100 days.

THE SAFETY: The crew would be protected by a massive shock absorber system that would cushion them from the explosions.

THE FUEL: The spacecraft would carry enough fuel for a round trip to Mars, with additional fuel for exploration of the outer planets.

THE CREW: The crew would consist of 50 people, including scientists, engineers, and support staff.

---

ALTERNATIVES: Other nuclear propulsion projects included NERVA and Project Daedalus. These projects aimed to develop nuclear thermal and nuclear pulse propulsion systems.

NERVA: The Nuclear Engine for Rocket Vehicle Application was a nuclear thermal rocket program that ran from 1955 to 1972.

DAEDELUS: Project Daedalus was a study conducted by the British Interplanetary Society in the 1970s to design an interstellar spacecraft.

COMPARISON: Unlike Orion, which used nuclear pulse propulsion, NERVA used nuclear thermal propulsion. This involved heating a gas with a nuclear reactor and expelling it through a nozzle.

LIMITATIONS: Both projects faced similar challenges, including political opposition, safety concerns, and high costs.

---

MODERN REVIVAL: In recent years, there has been renewed interest in nuclear propulsion for space travel. Projects like Project Dragon and Breakthrough Starshot aim to develop new technologies for interstellar travel.

PROJECT DRAGON: A modern version of Orion, Project Dragon aims to use nuclear pulse propulsion to reach Mars in just 45 days.

BREAKTHROUGH STARSHOT: This project aims to send a fleet of tiny spacecraft to the nearest star system using light sails.

FUTURE PROSPECTS: Advances in materials science and nuclear technology may make nuclear propulsion feasible in the future.

ETHICS: The use of nuclear weapons for propulsion raises ethical questions about the militarization of space.

CONCLUSION: Project Orion remains a symbol of human ambition and the power of bold thinking. While it was never built, its legacy lives on in the dreams of future space explorers.

Join us next time for more Cold War mysteries. Don't forget to like, comment, and subscribe for more lost futures!
        """.strip()

    # Karakter limitine göre kırp
    if mode == "shorts":
        script = script[:Config.SHORTS_CHAR_LIMIT]
    else:
        script = script[:Config.PODCAST_CHAR_LIMIT]

    logger.info(f"✅ {mode.upper()} metni hazır! ({len(script)} karakter)")
    return script
