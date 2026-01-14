# src/script_generator.py
import os
import re
import requests
import logging
from typing import Optional, Callable, Any, Tuple
from src.config import Config
from src.utils import setup_logging

# Logger ayarları
logger = setup_logging()

def clean_text(text: str) -> str:
    """
    Metinden Unicode karakterleri temizler ve ASCII formatına dönüştürür.
    
    Args:
        text (str): Temizlenecek metin
    
    Returns:
        str: Temizlenmiş metin
    """
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', text)
    return nfkd.encode('ascii', 'ignore').decode('ascii')


class AIScriptGenerator:
    """
    AI destekli script üretici sınıfı.
    
    Özellikler:
    - 3 katmanlı sağlayıcı sistemi (Qwen → Phi3 → Llama3.2)
    - Podcast için 13 bölümlü üretim (4 istekte)
    - Shorts'ta teknik talimatları engelleme
    - Dinamik bağlam yönetimi
    - Zaman aşımı koruma
    """
    
    def __init__(self) -> None:
        """Sağlayıcı listesini başlatır."""
        self.providers: list[Tuple[str, Callable]] = [
            ("qwen", self._generate_with_qwen),
            ("phi3", self._generate_with_phi3),
            ("ollama", self._generate_with_ollama_fallback)
        ]
    
    def generate_script(self, topic: str, mode: str) -> str:
        """
        İstenen moda göre script üretir.
        
        Args:
            topic (str): Konu başlığı (Format: "YIL: Konu Açıklaması")
            mode (str): "shorts" veya "podcast"
        
        Returns:
            str: Üretilen script metni
        """
        for name, func in self.providers:
            try:
                logger.info(f"🔄 Trying {name.upper()}...")
                if mode == "podcast":
                    script = self._generate_podcast_in_chunks(topic, func)
                else:
                    script = func(topic, mode)
                
                # Kalite kontrolü
                if script and len(script) > 100:
                    logger.info(f"✅ {name.upper()} success!")
                    return clean_text(script)
            except Exception as e:
                logger.warning(f"⚠️ {name.upper()} failed: {str(e)}")
                continue
        
        logger.error("🔥 ALL PROVIDERS FAILED! Using enhanced fallback.")
        return self._generate_enhanced_fallback(topic, mode)

    def _create_prompt(self, topic: str, mode: str, context: str = "") -> str:
        """
        AI modeli için optimize edilmiş prompt oluşturur.
        
        Args:
            topic (str): Konu başlığı
            mode (str): "shorts" veya "podcast"
            context (str): Önceki içerik (sadece podcast için)
        
        Returns:
            str: Oluşturulan prompt
        """
        base_rules = """
You are a professional Cold War historian creating engaging YouTube content.
All information must be FACTUALLY ACCURATE and VERIFIABLE.
- NEVER invent facts, statistics, quotes, or historical events
- If unsure, say "Historical records show..." or "According to verified sources..."
- Base everything on real historical/scientific evidence
- Include verification notes like "(CIA Archives, 1963)"
- Maintain narrative coherence and avoid repetition
- NEVER include technical production notes like: "opening sound effects", "3 seconds", "voiceover", "background music begins", "fade in", "cut to"
- DO include historical terms even if they contain these words (e.g., "background radiation", "sound barrier", "voiceover artist")
"""
        if mode == "shorts":
            return f"""{base_rules}
Write ONLY the script content about: "{topic}"

CRITICAL RULES:
- Start with a shocking historical fact (first 3 seconds)
- Include exactly 2 curiosity questions
- Mention "For the full story, listen to today's podcast!"
- End with "Like, comment, and subscribe for more Cold War mysteries!"
- Total characters: 1000-1200
- Use conversational tone, avoid complex sentences
- NEVER mention production techniques or sound effects

SCRIPT:"""
        else:
            if context:
                return f"""{base_rules}
Continue the podcast script naturally from the previous section.

Previous context (do not repeat):
"{context}"

Now continue the story about: "{topic}"

- Keep storytelling style
- Add new verified facts
- Do NOT summarize or conclude yet
- Stop mid-sentence if approaching limit
- NEVER mention production techniques like "cut to", "fade in", "sound effects"
- If discussing audio technology, say "audio equipment of the era" instead of "sound effects"
- If discussing narration, say "historical narration" instead of "voiceover"

CONTINUATION:"""
            else:
                return f"""{base_rules}
Write the BEGINNING of a detailed YouTube podcast script about: "{topic}"

Structure EXACTLY as follows:
Chapter 1: Origins and Vision
[Engaging narrative about the initial concept, key figures, and historical context. Include verified sources and archival references.]

CRITICAL RULES:
- NEVER mention production techniques or sound effects
- Include specific dates, names, and document references
- Maintain historical accuracy above storytelling flair
- Address the viewer directly with "you" to create connection
- Total characters: approximately 2000

BEGINNING:"""

    def _generate_podcast_in_chunks(self, topic: str, generate_func: Callable) -> str:
        """
        Podcast metnini 13 bölüme ayırarak 4 istekte üretir.
        
        Args:
            topic (str): Konu başlığı
            generate_func (Callable): Kullanılacak sağlayıcı fonksiyonu
        
        Returns:
            str: Tam podcast metni
        """
        chapter_ranges = [
            ("1-3", 2000),
            ("4-6", 2000), 
            ("7-9", 2000),
            ("10-13", 3000)
        ]
        
        full_script = ""
        context = ""
        
        for i, (chapters, max_chars) in enumerate(chapter_ranges):
            logger.info(f"챕터 {chapters} üretiliyor... (hedef: ~{max_chars} karakter)")
            
            prompt = self._create_podcast_chunk_prompt(topic, chapters, context, max_chars)
            
            try:
                chunk = generate_func(topic, "podcast", custom_prompt=prompt, timeout=900)
                if not chunk or len(chunk.strip()) < 100:
                    logger.warning(f"Chunk {i+1} başarısız veya çok kısa")
                    continue
                    
                # Karakter sınırını uygula
                if len(chunk) > max_chars:
                    chunk = chunk[:max_chars]
                    last_period = chunk.rfind(".")
                    if last_period != -1:
                        chunk = chunk[:last_period + 1]
                
                full_script += chunk + "\n\n"
                context = full_script[-600:]  # Son 600 karakter bağlam olarak
                
            except Exception as e:
                logger.warning(f"Chapter {chapters} üretim hatası: {e}")
                continue
        
        return full_script.strip()

    def _create_podcast_chunk_prompt(self, topic: str, chapter_range: str, context: str, max_chars: int) -> str:
        """13 bölümlük podcast için özel chunk prompt oluşturur."""
        base_rules = """
You are a professional Cold War historian creating a detailed YouTube podcast script.
All information must be FACTUALLY ACCURATE and VERIFIABLE.
- NEVER invent facts, statistics, quotes, or historical events
- If unsure, say "Historical records show..." or "According to verified sources..."
- Base everything on real historical/scientific evidence
- Include verification notes like "(CIA Archives, 1963)"
- Maintain narrative coherence and avoid repetition
- NEVER mention production techniques like "cut to", "fade in", "sound effects"
- If discussing audio technology, say "audio equipment of the era" instead of "sound effects"
- If discussing narration, say "historical narration" instead of "voiceover"
"""
        
        chapter_descriptions = {
            "1-3": "Chapter 1: Origins and Vision\nChapter 2: Key Figures and Organizations\nChapter 3: Initial Technical Concepts",
            "4-6": "Chapter 4: Engineering Challenges\nChapter 5: Political Support and Opposition\nChapter 6: International Reactions",
            "7-9": "Chapter 7: Budget Battles and Funding\nChapter 8: Technological Breakthroughs\nChapter 9: Public Perception and Media Coverage",
            "10-13": "Chapter 10: Implementation Attempts\nChapter 11: Reasons for Cancellation\nChapter 12: Immediate Aftermath\nChapter 13: Long-term Legacy and Modern Relevance"
        }
        
        if context:
            return f"""{base_rules}
Continue the podcast script naturally from the previous section.

Previous context (do not repeat):
"{context}"

Now write ONLY chapters {chapter_range} about: "{topic}"

Structure EXACTLY as:
{chapter_descriptions[chapter_range]}

- Use engaging storytelling but maintain historical accuracy
- Include specific dates, names, and document references
- Total characters: approximately {max_chars}
- DO NOT include any technical markers or summaries
- STOP at the end of Chapter {chapter_range.split('-')[1]}

CONTINUATION:"""
        else:
            return f"""{base_rules}
Write the BEGINNING of a detailed YouTube podcast script about: "{topic}"

Structure EXACTLY as:
{chapter_descriptions[chapter_range]}

- Use engaging storytelling but maintain historical accuracy  
- Include specific dates, names, and document references
- Total characters: approximately {max_chars}
- DO NOT include any technical markers or summaries
- STOP at the end of Chapter {chapter_range.split('-')[1]}

BEGINNING:"""

    def _generate_with_qwen(self, topic: str, mode: str, custom_prompt: Optional[str] = None, timeout: int = 120) -> str:
        """Qwen2 modeli ile metin üretir."""
        return self._generate_with_ollama_model(topic, mode, "qwen2", custom_prompt, timeout)
    
    def _generate_with_phi3(self, topic: str, mode: str, custom_prompt: Optional[str] = None, timeout: int = 120) -> str:
        """Phi3 modeli ile metin üretir."""
        return self._generate_with_ollama_model(topic, mode, "phi3", custom_prompt, timeout)
    
    def _generate_with_ollama_fallback(self, topic: str, mode: str, custom_prompt: Optional[str] = None, timeout: int = 120) -> str:
        """Llama3.2 fallback modeli ile metin üretir."""
        return self._generate_with_ollama_model(topic, mode, "llama3.2", custom_prompt, timeout)

    def _generate_with_ollama_model(self, topic: str, mode: str, model_name: str, custom_prompt: Optional[str] = None, timeout: int = 120) -> str:
        """
        Ollama API üzerinden metin üretir.
        
        Args:
            topic (str): Konu başlığı
            mode (str): "shorts" veya "podcast"
            model_name (str): Ollama model adı
            custom_prompt (Optional[str]): Özel prompt
            timeout (int): İstek zaman aşımı (saniye)
        
        Returns:
            str: Üretilen metin
        
        Raises:
            Exception: API isteği başarısız olursa
        """
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": custom_prompt or self._create_prompt(topic, mode),
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
            
            # Boş sonuç kontrolü
            if not result or len(result) < 50:
                raise ValueError("Model returned empty or very short response")
                
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error with model {model_name}: {str(e)}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"Response parsing error: {str(e)}")
            raise

    def _generate_enhanced_fallback(self, topic: str, mode: str) -> str:
        """
        Tüm sağlayıcılar başarısız olduğunda kaliteli fallback script üretir.
        
        Args:
            topic (str): Konu başlığı
            mode (str): "shorts" veya "podcast"
        
        Returns:
            str: Fallback script
        """
        year = topic.split(":")[0].strip() if ":" in topic else "1960s"
        title = topic.split(":", 1)[1].strip() if ":" in topic else topic
        
        if mode == "shorts":
            return f"""
In {year}, engineers dreamed of building {title}. This wasn't science fiction—it was real Cold War ambition.

How did they plan to construct it? What made it revolutionary?

For the full story, listen to today's podcast!

Like, comment, and subscribe for more Cold War mysteries!
""".strip()
        else:
            return f"""
Chapter 1: The Vision of {year}
In {year}, amid the height of the Cold War, scientists proposed a radical idea: {title}. Historical records from the National Archives reveal this was more than a concept—it was a detailed blueprint backed by serious funding and political will.

Chapter 2: Technical Innovation and Challenges
The design pushed 1960s technology to its limits. Engineers at major laboratories developed novel solutions for radiation shielding, life support, and modular construction. Declassified technical reports show how they solved problems we still face today.

Chapter 3: Political Will and Budget Constraints
Despite technical feasibility, changing political landscapes and budget priorities threatened the project. Congressional hearings from {int(year) + 2} reveal intense debates about cost versus strategic advantage. International tensions further complicated implementation.

Chapter 4: Lasting Legacy in Modern Engineering
Though never fully realized as originally envisioned, the project's DNA lives on. Modern space habitats, urban planning principles, and even AI-driven resource management systems owe direct debt to these pioneering concepts. The lessons learned continue to shape our approach to ambitious engineering challenges.

If you enjoyed this journey into Cold War innovation, don't forget to like this video, share your thoughts in the comments below, and subscribe for more deep dives into the untold stories that shaped our world.
""".strip()


def generate_shorts_script(topic: str) -> str:
    """
    Shorts için optimize edilmiş script üretir.
    
    Args:
        topic (str): Konu başlığı
    
    Returns:
        str: 1200 karaktere optimize edilmiş shorts scripti
    """
    generator = AIScriptGenerator()
    script = generator.generate_script(topic, "shorts")
    
    # Karakter sınırı kontrolü
    if len(script) > 1200:
        script = script[:1200]
        last_period = script.rfind(".")
        if last_period != -1:
            script = script[:last_period + 1]
        else:
            last_space = script.rfind(" ")
            if last_space != -1:
                script = script[:last_space]
    
    return script.strip()


def generate_podcast_script(topic: str) -> str:
    """
    Podcast için optimize edilmiş script üretir.
    
    Args:
        topic (str): Konu başlığı
    
    Returns:
        str: 9,000 karaktere yaklaşan podcast scripti
    """
    generator = AIScriptGenerator()
    return generator.generate_script(topic, "podcast").strip()
