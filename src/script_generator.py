# src/script_generator.py
import os
import requests
import logging
from typing import Optional, Callable, Any, Tuple
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def clean_text(text: str) -> str:
    """Unicode karakterleri temizler."""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', text)
    return nfkd.encode('ascii', 'ignore').decode('ascii')

class AIScriptGenerator:
    def __init__(self) -> None:
        """Stabil sağlayıcı zinciri başlatır."""
        self.providers: list[Tuple[str, Callable]] = [
            ("qwen", self._generate_with_qwen),
            ("phi3", self._generate_with_phi3),
            ("llama3", self._generate_with_llama3),
            ("fallback", self._generate_fallback)
        ]
    
    def generate_script(self, topic: str, mode: str) -> str:
        """İstenen moda göre script üretir."""
        for name, func in self.providers:
            try:
                logger.info(f"🔄 Trying {name.upper()}...")
                if mode == "podcast":
                    script = self._generate_podcast_in_parts(topic, func)
                else:
                    script = func(topic, mode)
                
                if script and len(script) > 100:
                    logger.info(f"✅ {name.upper()} success!")
                    return clean_text(script)
            except Exception as e:
                logger.warning(f"⚠️ {name.upper()} failed: {str(e)}")
                continue
        
        logger.error("🔥 ALL PROVIDERS FAILED! Using final fallback.")
        return self._generate_final_fallback(topic, mode)

    def _create_clean_prompt(self, topic: str, mode: str, step: str = "") -> str:
        """AI'ı temiz yazmaya eğiten prompt."""
        
        base_instruction = """
You are Synapse Daily's trained content writer. You ONLY write clean, conversational text.
- NO titles, no chapter headings, no technical terms
- NO "Welcome to", "Title:", "Chapter:", "Opening shot", "Based on"
- NO AI instructions like "Shocking hook", "Curiosity questions", "CTA"
- Write as if speaking to the viewer directly
- Use verified historical facts
- Keep sentences under 8 words for clarity
"""

        if mode == "shorts":
            return f"""
{base_instruction}

Topic: {topic}

Requirements:
- Write 950-1250 characters
- Start with a SHOCKING fact immediately
- Example: "In 1967, scientists secretly..." (NOT: "Welcome to...")
- Include 2 curiosity questions in text
- Example: "But how did they hide it? What technologies were used?"
- Include "For the full story, listen to today's podcast!"
- End with: "Like, comment, subscribe for more Cold War mysteries!"
- Write conversationally, factually

Script:"""
        
        else:  # podcast
            if step == "part1":
                return f"""
{base_instruction}

Topic: {topic}

Requirements:
- Write Chapter 1-4 (1500-2000 words)
- Focus on: Origins, Vision, Early Development
- Start with: "Welcome to Synapse Daily..." (this is for you, not the viewer)
- Include verified historical facts
- Use storytelling: "Imagine being there in 1968..."
- Write naturally, factually

Chapter 1-4:"""
            elif step == "part2":
                return f"""
{base_instruction}

Topic: {topic}

Requirements:
- Write Chapter 5-8 (1500-2000 words)
- Focus on: Challenges, Politics, Funding
- Continue storytelling naturally
- Include verified historical facts
- Write factually, engagingly

Chapter 5-8:"""
            else:
                return f"""
{base_instruction}

Topic: {topic}

Requirements:
- Write Chapter 9-13 (2000-2500 words)
- Focus on: Legacy, Modern Relevance, Final Thoughts
- End with: "Like this video if you learned something new! Subscribe for more..."
- Conclude naturally and factually

Chapter 9-13:"""

    def _create_simple_prompt(self, topic: str, mode: str, step: str = "") -> str:
        """AI'nın sapmaması için sade prompt."""
        return self._create_clean_prompt(topic, mode, step)

    def _generate_podcast_in_parts(self, topic: str, generate_func: Callable) -> str:
    """Podcast metnini 3 parçada üretir (kelime sayısı kontrolüyle)."""
    full_script = ""
    
    # Bölüm planı: (step, hedef_kelime_sayısı)
    chapter_plan = [
        ("part1", 4500),  # Chapter 1-4
        ("part2", 4500),  # Chapter 5-8  
        ("part3", 6000)   # Chapter 9-13
    ]
    
    for i, (step, target_words) in enumerate(chapter_plan):
        logger.info(f"Part {i+1}/3 generating... (hedef: ~{target_words} kelime)")
        
        attempts = 0
        max_attempts = 3  # En fazla 3 deneme
        
        while attempts < max_attempts:
            attempts += 1
            prompt = self._create_simple_prompt(topic, "podcast", step)
            
            try:
                chunk = generate_func(topic, "podcast", custom_prompt=prompt, timeout=600)
                
                if not chunk or len(chunk.strip()) < 50:
                    logger.warning(f"Part {i+1} is too short, retrying... ({attempts}/{max_attempts})")
                    continue
                
                # Kelime sayısını kontrol et
                word_count = len(chunk.split())
                logger.info(f"Part {i+1} produced {word_count} words (target: {target_words})")
                
                if word_count >= target_words:
                    # Hedefe ulaştı, bir sonraki bölüme geç
                    logger.info(f"✅ Part {i+1} target reached ({word_count}/{target_words})")
                    
                    # AI'nın teknik terimlerini temizle
                    chunk = chunk.replace("Title:", "").replace("Chapter:", "")
                    chunk = chunk.replace("Opening shot", "").replace("Closing scene", "")
                    
                    full_script += chunk + "\n\n"
                    break
                else:
                    # Hedefe ulaşmadı, AI'a "bu metni genişlet" diyerek tekrar dene
                    extend_prompt = f"""
Topic: {topic}

Previous content:
"{chunk}"

Requirements:
- Expand the previous content to reach at least {target_words} words
- Continue the storytelling naturally
- Include more verified historical facts
- Maintain the same writing style
- Do NOT repeat content
- Focus on: {self._get_chapter_focus(step)}

Expanded content:"""
                    
                    logger.info(f"🔄 Extending Part {i+1} ({word_count}/{target_words})")
                    chunk = generate_func(topic, "podcast", custom_prompt=extend_prompt, timeout=600)
                    
                    word_count = len(chunk.split())
                    logger.info(f"Extended Part {i+1} to {word_count} words")
                    
                    if word_count >= target_words:
                        chunk = chunk.replace("Title:", "").replace("Chapter:", "")
                        chunk = chunk.replace("Opening shot", "").replace("Closing scene", "")
                        
                        full_script += chunk + "\n\n"
                        break
                    else:
                        logger.warning(f"Part {i+1} still insufficient ({word_count}/{target_words}), retrying... ({attempts}/{max_attempts})")
                        continue
                        
            except Exception as e:
                logger.warning(f"Part {i+1} attempt {attempts} failed: {e}")
                if attempts >= max_attempts:
                    logger.warning(f"Part {i+1} failed after {max_attempts} attempts, skipping...")
                    continue
        
        # Karakter limiti kontrolü
        if len(full_script) > 45000:
            logger.info("Maximum character limit reached, stopping generation.")
            break
    
    # Son temizlik
    if len(full_script) > 45000:
        full_script = full_script[:45000]
        last_period = full_script.rfind(".")
        if last_period != -1:
            full_script = full_script[:last_period + 1]
    
    return full_script.strip()

def _get_chapter_focus(self, step: str) -> str:
    """Bölüm hedefine göre içerik odak noktası."""
    focus_map = {
        "part1": "Origins, Vision, Early Development",
        "part2": "Challenges, Politics, Funding",
        "part3": "Legacy, Modern Relevance, Final Thoughts"
    }
    return focus_map.get(step, "General Content")

    def _generate_with_qwen(self, topic: str, mode: str, custom_prompt: Optional[str] = None, timeout: int = 120) -> str:
        return self._generate_with_ollama_model(topic, mode, "qwen2", custom_prompt, timeout)
    
    def _generate_with_phi3(self, topic: str, mode: str, custom_prompt: Optional[str] = None, timeout: int = 120) -> str:
        return self._generate_with_ollama_model(topic, mode, "phi3", custom_prompt, timeout)
    
    def _generate_with_llama3(self, topic: str, mode: str, custom_prompt: Optional[str] = None, timeout: int = 120) -> str:
        return self._generate_with_ollama_model(topic, mode, "llama3.2", custom_prompt, timeout)

    def _generate_with_ollama_model(self, topic: str, mode: str, model_name: str, custom_prompt: Optional[str] = None, timeout: int = 120) -> str:
        url = "http://localhost:11434/api/generate"
        prompt = custom_prompt or self._create_simple_prompt(topic, mode)
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 8192
            }
        }
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            result = response.json()["response"].strip()
            
            # AI'nın sapma yapmasını engelle
            if not result or len(result) < 50:
                raise ValueError("Empty response")
            
            # Prompt terimlerini temizle
            result = result.replace("Opening a shot", "").replace("Based on the", "")
            result = result.replace("As an AI", "").replace("I can't", "")
            result = result.replace("Title:", "").replace("Chapter:", "")
            
            return result
        except Exception as e:
            logger.error(f"Model {model_name} error: {str(e)}")
            raise

    def _generate_fallback(self, topic: str, mode: str, custom_prompt: Optional[str] = None, timeout: int = 120) -> str:
        """Farklı modelle tekrar dener."""
        backup_models = ["llama3.2", "phi3", "mistral"]
        prompt = custom_prompt or self._create_simple_prompt(topic, mode)
        
        for model in backup_models:
            try:
                logger.info(f"Trying backup model: {model}")
                url = "http://localhost:11434/api/generate"
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.6}
                }
                response = requests.post(url, json=payload, timeout=timeout)
                response.raise_for_status()
                result = response.json()["response"].strip()
                
                if result and len(result) > 50:
                    return result
            except:
                continue
        
        raise Exception("All backup models failed")

    def _generate_final_fallback(self, topic: str, mode: str) -> str:
        """Son çare: statik kaliteli içerik."""
        year = topic.split(":")[0].strip() if ":" in topic else "1960s"
        title = topic.split(":", 1)[1].strip() if ":" in topic else topic
        
        if mode == "shorts":
            return f"""
In {year}, engineers dreamed of {title}. This wasn't science fiction—it was Cold War reality.

How did they plan it? What made it revolutionary?

For the full story, listen to today's podcast!

Like, comment, and subscribe for more Cold War mysteries!
""".strip()
        else:
            return f"""
Welcome to Synapse Daily. Today we explore {year}: {title}—a story verified through declassified documents.

Chapter 1: The Vision
In {year}, amid global tensions, a team of scientists developed a revolutionary concept. Historical records show this was more than ambition—it was detailed planning.

Chapter 2: The Execution  
The project faced impossible challenges. Funding dried up. Political pressure mounted. Yet, they persisted with meticulous documentation.

Chapter 3: The Legacy
What strikes me most is their unwavering belief. Even after cancellation, they kept detailed notes. Their vision lives on today.

If you enjoyed this dive into lost futures, don't forget to like, comment your thoughts below, and subscribe for more Cold War mysteries.
""".strip()

def generate_shorts_script(topic: str) -> str:
    generator = AIScriptGenerator()
    script = generator.generate_script(topic, "shorts")
    
    # Karakter limiti 950-1250 arası
    if len(script) < 950:
        script = script.ljust(950)[:1250]
    elif len(script) > 1250:
        script = script[:1250]
        last_period = script.rfind(".")
        if last_period != -1:
            script = script[:last_period + 1]
        else:
            last_space = script.rfind(" ")
            if last_space != -1:
                script = script[:last_space]
    
    return script.strip()

def generate_podcast_script(topic: str) -> str:
    generator = AIScriptGenerator()
    return generator.generate_script(topic, "podcast")
