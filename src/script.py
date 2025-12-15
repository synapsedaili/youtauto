# src/script.py
import os
from huggingface_hub import InferenceClient

def generate_script(idea_text: str) -> str:
    """YouTube algoritması ve insan psikolojisine göre optimize edilmiş 60 saniyelik senaryo."""
    client = InferenceClient(
        "meta-llama/Llama-3.2-1B",
        token=os.environ.get("HF_TOKEN")
    )
    
    # 💥 PSİKOLOJİK OLARAK EN GÜÇLÜ PROMPT 💥
    prompt = f"""
You are Alex, the charismatic host of 'Synapse Daily' with 500K subscribers. 
Create a **60-second viral script** about: "{idea_text}"

🎬 PSYCHOLOGICAL BLUEPRINT (MUST FOLLOW):
1. OPENING (0-5 sec): 
   - Start with a SHOCKING statement/question using urgency words ("RIGHT NOW", "TODAY", "IMMEDIATELY")
   - Create a CURIOSITY GAP (don't reveal everything)
   - MAX 10 words

2. MIDDLE (5-45 sec) - EXACTLY 3 MICRO-POINTS:
   POINT 1 (Problem):
     - Name a SPECIFIC pain point your audience feels
     - Use concrete example: "When you open Instagram..."
   POINT 2 (Solution):
     - Give ONE actionable step with exact path: "Go to Settings > ..."
     - Include WHY it works
   POINT 3 (Result):
     - Show MEASURABLE benefit: "saves 2 hours/week", "reduces anxiety by 30%"
     - Use sensory words: "feel the relief", "see the difference"

3. CLOSING (45-60 sec):
   - "You just [achieved benefit]."
   - "If this helped you, SMASH that like button — it tells YouTube this knowledge matters."
   - Teaser: "Next video: [next shocking topic]"
   - Sign off: "I'm Alex from Synapse Daily. Stay curious."

⚡ RULES:
- TOTAL WORDS: 140-150 MAX (count carefully)
- NO jargon, NO fluff, NO "welcome to the channel"
- USE power words: "secret", "exposed", "hack", "instantly", "guaranteed"
- SENTENCE LENGTH: Max 8 words per sentence
- TONE: Urgent but trustworthy (like a friend revealing a secret)
- END EXACTLY at 60 seconds

📝 OUTPUT FORMAT (ONLY THE SCRIPT, NO EXTRA TEXT):
[OPENING LINE]

[POINT 1: Problem]

[POINT 2: Solution]

[POINT 3: Result]

[CLOSING + CTA + TEASER]
    """
    
    response = client.text_generation(
        prompt,
        max_new_tokens=300,
        temperature=0.75,  # Creativity control
        top_p=0.92,       # Focus on quality
        repetition_penalty=1.15
    )
    
    # Temizle: AI bazen extra text ekler
    script = response.strip()
    if "OUTPUT FORMAT" in script:
        script = script.split("OUTPUT FORMAT")[0].strip()
    if "```" in script:
        script = script.split("```")[1].strip()
        
    return script