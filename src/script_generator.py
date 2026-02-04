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
                    script = self._generate_podcast_in_13_chapters(topic, func)
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

    def _create_clean_prompt(self, topic: str, mode: str, step: str = "", chapter_num: int = 1) -> str:
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
- Write 700-800 characters (micro storytelling)
- Start with a SHOCKING fact immediately
- Example: "In 1967, scientists secretly..." (NOT: "Welcome to...")
- Include 1-2 micro curiosity triggers
- Example: "But how did they hide it?" (NO podcast invitations!)
- NO podcast invitations, NO CTA, NO "like, comment, subscribe"
- Write micro-storytelling style, very concise
- Keep it under 800 characters total

Script:"""
        
        else:  # podcast - chapter generation
            if step == "outline":
                return f"""
{base_instruction}

Topic: {topic}

Requirements:
- Generate 13 chapter titles for a podcast about this topic
- Each title should be descriptive and engaging
- Focus on different aspects: origins, development, challenges, politics, legacy, etc.
- Format:
Chapter 1: [Title]
Chapter 2: [Title]
Chapter 3: [Title]
...
Chapter 13: [Title]

Chapter Titles:"""
            else:  # individual chapter
                return f"""
{base_instruction}

Topic: {topic}

Current Chapter: Chapter {chapter_num}

Requirements:
- Write EXACTLY 400 words for this chapter
- Focus on: {self._get_chapter_focus(chapter_num)}
- Include verified historical facts
- Use storytelling techniques
- Maintain consistent writing style
- NO "Chapter {chapter_num}:" or titles
- NO technical terms or headings
- Write conversationally and factually
- Count your words: exactly 400 words required

Chapter {chapter_num} Content:"""

    def _create_simple_prompt(self, topic: str, mode: str, step: str = "", chapter_num: int = 1) -> str:
        """AI'nın sapmaması için sade prompt."""
        return self._create_clean_prompt(topic, mode, step, chapter_num)

    def _get_chapter_focus(self, chapter_num: int) -> str:
        """Chapter numarasına göre içerik odak noktası."""
        focus_map = {
            1: "Origins and Initial Vision",
            2: "Early Development and Planning",
            3: "Technical Innovations and Breakthroughs",
            4: "Major Milestones and Achievements",
            5: "Political Climate and Government Support",
            6: "Funding and Budget Considerations",
            7: "Engineering Challenges and Solutions",
            8: "International Relations Impact",
            9: "Security Concerns and Classification",
            10: "Setbacks and Obstacles Encountered",
            11: "Alternative Approaches and Adaptations",
            12: "Legacy and Influence on Future Projects",
            13: "Modern Relevance and Final Reflections"
        }
        return focus_map.get(chapter_num, "General Content")

    def _generate_podcast_in_13_chapters(self, topic: str, generate_func: Callable) -> str:
        """Podcast metnini 13 chapter'da üretir (her chapter 400 words)."""
        full_script = ""
        
        # 1. Chapter başlıklarını oluştur
        logger.info("📚 Generating 13 chapter titles...")
        outline_prompt = self._create_simple_prompt(topic, "podcast", "outline")
        
        try:
            outline = generate_func(topic, "podcast", custom_prompt=outline_prompt, timeout=300)
            
            # Başlıkları parse et
            chapters = {}
            for i in range(1, 14):
                if f"Chapter {i}:" in outline:
                    start = outline.find(f"Chapter {i}:")
                    end = outline.find(f"Chapter {i+1}:", start) if i < 13 else len(outline)
                    chapters[i] = outline[start:end].strip()
            
            if not chapters:
                logger.warning("⚠️ Could not parse chapter titles, using default titles...")
                for i in range(1, 14):
                    chapters[i] = f"Chapter {i}: {self._get_chapter_focus(i)}"
            
        except Exception as e:
            logger.warning(f"Outline generation failed: {e}")
            # Varsayılan başlıklar
            chapters = {}
            for i in range(1, 14):
                chapters[i] = f"Chapter {i}: {self._get_chapter_focus(i)}"
        
        # 2. Her chapter'ı oluştur
        for chapter_num in range(1, 14):
            logger.info(f"📖 Chapter {chapter_num}/13 generating...")
            
            # Chapter içeriğini oluştur
            chapter_prompt = self._create_simple_prompt(topic, "podcast", "chapter", chapter_num)
            
            try:
                chapter_content = generate_func(topic, "podcast", custom_prompt=chapter_prompt, timeout=600)  # 10dk
                
                # Kelime sayısını kontrol et
                word_count = len(chapter_content.split())
                logger.info(f"Chapter {chapter_num} produced {word_count} words (target: 400)")
                
                if word_count < 300:
                    # 300 altıysa genişlet
                    logger.info(f"🔄 Extending Chapter {chapter_num} ({word_count}/400)")
                    
                    extend_prompt = f"""
Topic: {topic}

Previous content for Chapter {chapter_num}:
"{chapter_content}"

Requirements:
- Expand the previous content to reach at least 400 words
- Continue the storytelling naturally
- Include more verified historical facts
- Maintain the same writing style
- Do NOT repeat content
- Focus on: {self._get_chapter_focus(chapter_num)}
- Count your words: minimum 400 words required

Extended Chapter {chapter_num} Content:"""
                    
                    chapter_content = generate_func(topic, "podcast", custom_prompt=extend_prompt, timeout=600)
                    word_count = len(chapter_content.split())
                    logger.info(f"Extended Chapter {chapter_num} to {word_count} words")
                
                # Temizle ve ekle
                chapter_content = chapter_content.replace(f"Chapter {chapter_num}:", "").replace("Title:", "")
                chapter_content = chapter_content.replace("Opening shot", "").replace("Closing scene", "")
                
                full_script += f"\n\n{chapters[chapter_num]}\n{chapter_content}"
                
            except Exception as e:
                logger.warning(f"Chapter {chapter_num} failed: {e}")
                # Hata durumunda fallback içeriği
                full_script += f"\n\nChapter {chapter_num}: {self._get_chapter_focus(chapter_num)}\nContent could not be generated due to an error."
        
        # Final CTA ekle (ama sadece podcast için)
        full_script += "\n\nIf you enjoyed this dive into Cold War history, don't forget to like, comment your thoughts below, and subscribe for more fascinating stories!"
        
        # Karakter limiti kontrolü
        if len(full_script) > 60000:  # 60K karakter (13 × 400 × 13 ≈ 5200 words)
            logger.info("Maximum character limit reached, truncating...")
            full_script = full_script[:60000]
            last_period = full_script.rfind(".")
            if last_period != -1:
                full_script = full_script[:last_period + 1]
        
        return full_script.strip()

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
    
   
    if len(script) < 700:
        script = script.ljust(700)[:800]
    elif len(script) > 800:
        script = script[:800]
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
