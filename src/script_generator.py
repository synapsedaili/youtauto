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
ALL information must be FACTUALLY ACCURATE and VERIFIABLE.
- NEVER invent facts, statistics, quotes, or historical events
- If unsure, say "Historical records show..." or "According to verified sources..."
- Base everything on real historical/scientific evidence
- Include verification notes like "(CIA Archives, 1963)"
- Maintain narrative coherence and avoid repetition
- NEVER include technical production notes like: "opening sound effects", "3 seconds", "voiceover", "background music begins", "fade in", "cut to"
- DO include historical terms even if they contain these words (e.g., "background radiation", "sound barrier", "voiceover artist")
- AVOID these forbidden phrases: "fact with", "curious question #1", "curious question #2", "shocking fact", "dramatic tone", "incredible story"
- Start with NATURAL engaging statements, not forced hooks
"""
if mode == "shorts":
    return f"""{base_rules}
Write ONLY the script content about: "{topic}"

CRITICAL RULES:
- TOTAL CHARACTERS: 950-1050 (NOT 1200!) 👈 SINIRI İNDİR
- Start with a NATURAL engaging historical statement
- Include exactly 2 NATURAL curiosity questions
- Mid-video: "For the full story, listen to today's podcast!"
- End with: "Like, comment, and subscribe for more Cold War mysteries!"
- NEVER use numbered lists or technical markers
- Use conversational tone, avoid complex sentences
- ENSURE the script fits within 67 seconds when spoken at natural pace

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
    
   
        chapter_ranges = [
            ("1-3", 5000),   # Eski: 8000 → Yeni: 5000
            ("4-6", 5000),   # Eski: 8000 → Yeni: 5000  
            ("7-9", 5000),   # Eski: 8000 → Yeni: 5000
            ("10-13", 8000)  # Eski: 12000 → Yeni: 8000
        ]
        
        full_script = ""
        context = ""
        retry_count = 0
        MAX_RETRIES = 2
        
        while retry_count <= MAX_RETRIES:
            full_script = ""
            context = ""
            
            for i, (chapters, max_chars) in enumerate(chapter_ranges):
                logger.info(f"챕터 {chapters} üretiliyor... (hedef: ~{max_chars} karakter)")
                
                prompt = self._create_podcast_chunk_prompt(topic, chapters, context, max_chars)
                
                try:
                    chunk = generate_func(topic, "podcast", custom_prompt=prompt, timeout=1200)
                    if not chunk or len(chunk.strip()) < max_chars * 0.4:  # %40'tan azsa başarısız say
                        logger.warning(f"Chapter {chapters} çok kısa ({len(chunk)} karakter). Tekrar deneniyor...")
                        continue
                        
                    if len(chunk) > max_chars:
                        chunk = self._smart_truncate(chunk, max_chars)
                    
                    full_script += chunk + "\n\n"
                    context = full_script[-800:]
                    
                except Exception as e:
                    logger.warning(f"Chapter {chapters} üretim hatası: {e}. Tekrar deneniyor...")
                    continue
            
            total_chars = len(full_script.strip())
            logger.info(f"✅ QWEN success! Toplam karakter: {total_chars}")
            
            # 👉 KRİTİK: MINIMUM 16.000 KARAKTER OLARAK DEĞİŞTİRİLDİ
            if total_chars >= 16000:
                logger.info(f"✅ METİN KALİTE KONTROLÜNDEN GEÇTİ! ({total_chars} karakter)")
                return full_script.strip()
            else:
                retry_count += 1
                logger.warning(f"❌ METİN ÇOK KISA! ({total_chars} karakter). {retry_count}/{MAX_RETRIES} tekrar denemesi yapılıyor...")
                if retry_count > MAX_RETRIES:
                    logger.error("🔥 TÜM TEKRARLAR BAŞARISIZ OLDU! Fallback metni kullanılacak.")
                    return self._generate_enhanced_fallback(topic, "podcast")
        
        return full_script.strip()

    def _create_podcast_chunk_prompt(self, topic: str, chapter_range: str, context: str, max_chars: int) -> str:
        """13 bölümlük podcast için DETAYLI ve PROFESYONEL prompt."""
        base_rules = """
You are Dr. Sarah Mitchell, a PhD historian specializing in Cold War technology at Harvard University.
Your mission: Create the MOST DETAILED, ACCURATE, and ENGAGING podcast script on this topic.

🎯 ABSOLUTE RULES:
- EVERY claim MUST be verified with specific sources like "(CIA Document X-1966, page 42)", "(National Archives Record Group 330)"
- Include EXACT dates, names, locations, technical specifications (e.g., "Mach 3.2", "12-foot diameter")
- NEVER invent facts - if unsure, say "Historical records are unclear on this point"
- Use rich descriptive language but maintain academic rigor
- Include primary source quotes where possible (e.g., "As Dr. Edward Teller stated in 1964: 'This changes everything...'")

📚 REQUIRED SOURCES TO REFERENCE:
- Declassified CIA/FBI/KGB documents
- Congressional hearing transcripts
- Technical reports from Lawrence Livermore National Laboratory
- Personal memoirs of key engineers/scientists
- Patent filings and engineering blueprints

🎭 NARRATIVE STYLE:
- Start each chapter with a vivid scene-setting moment
- Use storytelling techniques but NEVER sacrifice accuracy
- Address the listener as "you" to create connection
- Include emotional human elements (e.g., "For the engineers working overnight, this wasn't just a job...")
"""
        
        chapter_descriptions = {
            "1-3": """Chapter 1: Origins and Vision
[Detailed account of who conceived Project Pluto, when, where, and the geopolitical context. Include exact meeting dates, names of key scientists, initial funding amounts, and strategic objectives.]

Chapter 2: Key Figures and Organizations
[Profiles of 3-5 critical individuals: full names, credentials, roles. Organizations involved: Department of Defense, DARPA, Lawrence Livermore Lab. Include personal anecdotes and career trajectories.]

Chapter 3: Initial Technical Concepts
[Engineering details: nuclear ramjet mechanics, material science challenges, radiation shielding concepts. Reference specific patent numbers and technical papers.]""",
            
            "4-6": """Chapter 4: Engineering Challenges
[Deep dive into specific engineering hurdles: heat dissipation at Mach 3+, materials that could withstand 2500°F, vibration issues. Include failed prototypes and their test results.]

Chapter 5: Political Support and Opposition
[Congressional debates, key senators/representatives, budget battles, internal Pentagon politics. Reference exact hearing dates and vote counts. Quote from declassified memos.]

Chapter 6: International Reactions
[KGB intelligence reports on Project Pluto, Soviet counter-projects, NATO allies' responses. Include diplomatic cables and intelligence intercepts.]""",
            
            "7-9": """Chapter 7: Budget Battles and Funding
[Year-by-year funding breakdowns, cost overruns, Congressional appropriation votes. Include specific dollar amounts and inflation-adjusted equivalents.]

Chapter 8: Technological Breakthroughs
[Major innovations: new alloys, radiation-hardened electronics, navigation systems for Mach 3 flight. Reference technical reports with exact document numbers.]

Chapter 9: Public Perception and Media Coverage
[Major newspaper articles, TV coverage, public opinion polls from 1964-1968. Include quotes from New York Times, Washington Post, Time Magazine.]""",
            
            "10-13": """Chapter 10: Implementation Attempts
[Test flight preparations, launch facility construction (exact locations), safety protocols. Include dates, personnel involved, technical specifications of test vehicles.]

Chapter 11: Reasons for Cancellation
[Exact cancellation date, key decision-makers, final cost analysis, strategic reassessment. Reference the specific memo or meeting where the decision was made.]

Chapter 12: Immediate Aftermath
[What happened to the team members, facilities, technology. Careers after cancellation. Include specific names and their post-Project Pluto paths.]

Chapter 13: Long-term Legacy and Modern Relevance
[How Project Pluto's technology influenced modern weapons systems, space exploration, nuclear propulsion. Current classified programs that use this legacy. Expert quotes from modern engineers.]"""
        }
        
        # 🎯 DİNAMİK HESAPLAMA: Karakter başına kelime oranı
        words_per_char = 0.18  # Ortalama İngilizce metin oranı
        estimated_words = int(max_chars * words_per_char)
        
        if context:
            return f"""{base_rules}

🎯 CURRENT ASSIGNMENT:
Continue EXACTLY chapters {chapter_range} about: "{topic}"

📊 SPECIFICATIONS:
- Total characters: ~{max_chars} (approximately {estimated_words} words)
- Character count includes spaces and punctuation
- MUST include specific source references like "(NARA RG 330, Box 17, File Pluto-1966)"
- DO NOT summarize previous chapters - continue ONLY from {chapter_range}
- STOP exactly at the end of Chapter {chapter_range.split('-')[1]}

📋 EXACT OUTPUT STRUCTURE:
{chapter_descriptions[chapter_range]}

💡 CONTINUATION CONTEXT (for seamless transition only):
"{context[-300:]}"...

🎯 YOUR MISSION CONTINUES NOW. Maintain academic rigor while keeping the narrative engaging.
"""
        else:
            return f"""{base_rules}

🎯 CURRENT ASSIGNMENT:
Write EXACTLY chapters {chapter_range} about: "{topic}"

📊 SPECIFICATIONS:
- Total characters: ~{max_chars} (approximately {estimated_words} words)
- Character count includes spaces and punctuation
- MUST include specific source references like "(NARA RG 330, Box 17, File Pluto-1966)"
- DO NOT summarize previous chapters - focus ONLY on {chapter_range}
- STOP exactly at the end of Chapter {chapter_range.split('-')[1]}

📋 EXACT OUTPUT STRUCTURE:
{chapter_descriptions[chapter_range]}

🎯 YOUR MISSION STARTS NOW. Create the most historically accurate and engaging narrative possible.
"""

    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Metni doğal noktalardan (cümle sonları) keser."""
        if len(text) <= max_length:
            return text
        
        # Önce son cümleyi tamamlamayı dene
        truncated = text[:max_length]
        last_period = truncated.rfind(".")
        last_question = truncated.rfind("?")
        last_exclamation = truncated.rfind("!")
        
        # En yakın doğal bitiş noktasını bul
        cut_points = [p for p in [last_period, last_question, last_exclamation] if p != -1]
        if cut_points:
            cut_point = max(cut_points) + 1
            return text[:cut_point]
        
        # Doğal bitiş yoksa kelime sınırından kes
        last_space = truncated.rfind(" ")
        if last_space != -1:
            return text[:last_space]
        
        # Hiçbiri yoksa zorla kes
        return truncated
    
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
    
    # Karakter sınırı kontrolü (1200 karakter)
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
        str: 20.000+ karaktere yaklaşan podcast scripti
    """
    generator = AIScriptGenerator()
    return generator.generate_script(topic, "podcast").strip()

# src/script_generator.py dosyasının TAM SONUNA EKLE

def generate_shorts_script(topic: str) -> str:
    """
    Shorts için optimize edilmiş script üretir.
    
    Args:
        topic (str): Konu başlığı
    
    Returns:
        str: 950-1050 karaktere optimize edilmiş shorts scripti
    """
    generator = AIScriptGenerator()
    script = generator.generate_script(topic, "shorts")
    
    # 1050 KARAKTER SINIRI 
    if len(script) > 1050:
        script = script[:1050]
        
        last_period = script.rfind(".")
        last_question = script.rfind("?")
        last_exclamation = script.rfind("!")
        
        # En son durak işaretini bul
        cut_points = [p for p in [last_period, last_question, last_exclamation] if p != -1]
        if cut_points:
            cut_point = max(cut_points) + 1
            script = script[:cut_point]
        else:
            # Durak işareti yoksa kelime sınırından kes
            last_space = script.rfind(" ")
            if last_space != -1:
                script = script[:last_space]
    
    # 👉En az 800 karakter olsun
    if len(script) < 800:
        logger.warning(f"⚠️ Shorts script çok kısa ({len(script)} karakter). Fallback ekleniyor.")
        fallback = (
            "\n\nFor the full story, listen to today's podcast! "
            "Like, comment, and subscribe for more Cold War mysteries!"
        )
        script = script + fallback
    
    return script.strip()
