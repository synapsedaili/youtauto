# src/script_generator.py
import os
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
    - Podcast için 4 bölümlü üretim
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
You are a professional Cold War historian and YouTube content creator. All information must be FACTUALLY ACCURATE and VERIFIABLE.
- NEVER invent facts, statistics, quotes, or historical events
- If unsure, say "Historical records show..." or "According to verified sources..."
- Base everything on real historical/scientific evidence
- Include verification notes like "(CIA Archives, 1963)"
- Maintain narrative coherence and avoid repetition
- Use engaging storytelling techniques but never sacrifice accuracy
- Address the viewer directly with "you" to create connection
"""
        if mode == "shorts":
            return f"""{base_rules}
Write a 900-character YouTube Shorts script about: "{topic}"
- Start with SHOCKING HOOK (first 3 seconds)
- Include 2 curiosity questions
- Mid-video: "For the full story, listen to today's podcast!"
- End with CTA: "Like, comment, and subscribe for more Cold War mysteries!"
- Total characters: ~1100
- Use conversational tone, avoid complex sentences
SCRIPT:"""
        else:
            if context:
                return f"""{base_rules}
Continue the following podcast script naturally. Maintain Chapter structure and factual accuracy.

Previous context (do not repeat):
"{context[-500:]}"...

Now continue the story about: "{topic}"

- Keep storytelling style
- Add new verified facts
- Do NOT summarize or conclude yet
- Stop mid-sentence if approaching limit
- Maintain historical accuracy above all

CONTINUATION:"""
            else:
                return f"""{base_rules}
Write a 7,000-word YouTube podcast script about: "{topic}"

Structure your response EXACTLY as follows:

Chapter 1: The Vision (Origins and Ambition)
[Engaging narrative about the initial concept, key figures, and historical context. Include verified sources and archival references.]

Chapter 2: The Execution (Engineering and Implementation)
[Technical details, challenges overcome, innovative solutions. Reference specific documents, blueprints, or technical reports.]

Chapter 3: The Political Arena (Budget Battles and Geopolitical Context)
[Political challenges, funding issues, international relations impact. Use declassified documents as evidence.]

Chapter 4: The Legacy (Modern Relevance and Lessons Learned)
[How this historical project influences today's technology and policy. Draw meaningful connections to present day.]

Final CTA:
Like this video if you learned something new! Comment your thoughts below and subscribe for more fascinating stories!

CRITICAL RULES:
- DO NOT include any technical markers like [HOOK], [VOICE ON], or brackets
- ONLY return pure narrative text with chapter headings
- Maintain historical accuracy above storytelling flair
- Include specific dates, names, and document references
- Avoid speculation - only state verified facts
SCRIPT:"""

    def _generate_podcast_in_chunks(self, topic: str, generate_func: Callable) -> str:
        """
        Podcast metnini 4 parçada üretir ve birleştirir.
        
        Args:
            topic (str): Konu başlığı
            generate_func (Callable): Kullanılacak sağlayıcı fonksiyonu
        
        Returns:
            str: Tam podcast metni
        """
        full_script = ""
        context = ""
        
        for i in range(4):  # 4 BÖLÜM
            logger.info(f"챕터 {i+1}/4 üretiliyor...")
            prompt = self._create_prompt(topic, "podcast", context)
            
            try:
                chunk = generate_func(topic, "podcast", custom_prompt=prompt, timeout=900)
                if not chunk or not chunk.strip():
                    logger.warning(f"Chunk {i+1} is empty. Breaking generation.")
                    break
                
                if full_script:
                    full_script += " " + chunk
                else:
                    full_script = chunk.strip()
                
                # Bağlamı güncelle (son 500 karakter)
                context = full_script[-500:] if len(full_script) > 500 else full_script
                
                # Kelime sınırı kontrolü
                if len(full_script) > 42000:
                    logger.info("챕터 limitine ulaşıldı, üretim durduruluyor.")
                    break
                    
            except Exception as e:
                logger.warning(f"Chunk {i+1} başarısız: {e}")
                break
        
        # Son cümleyi tamamlama
        if len(full_script) > 45000:
            full_script = full_script[:45000]
            last_period = full_script.rfind(".")
            if last_period != -1:
                full_script = full_script[:last_period + 1]
            else:
                last_space = full_script.rfind(" ")
                if last_space != -1:
                    full_script = full_script[:last_space]
        
        return full_script.strip()

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
{title} in {year} was a revolutionary concept that changed everything.

{title} wasn't just a dream—it was a detailed plan backed by top scientists.

For the full story, listen to today's podcast!

Like, comment, and subscribe for more Cold War mysteries!
""".strip()
        else:
            return f"""
Chapter 1: The Vision of {year}
In {year}, amid the height of the Space Race, engineers proposed a radical idea: {title}. Historical records from the National Archives reveal this was more than a concept—it was a detailed blueprint backed by serious funding and political will.

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
        str: 900 karaktere optimize edilmiş shorts scripti
    """
    generator = AIScriptGenerator()
    script = generator.generate_script(topic, "shorts")
    
    # Karakter sınırı kontrolü
    if len(script) > 900:
        script = script[:900]
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
        str: 7,000 kelimeye yaklaşan podcast scripti
    """
    generator = AIScriptGenerator()
    return generator.generate_script(topic, "podcast").strip()
