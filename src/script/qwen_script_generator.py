# src/script/qwen_script_generator.py
"""
Qwen Script Generator - UPDATED
=============================

Generates documentary scripts with:
- 3-part generation (3k + 3k + 2.5k = 8,500 characters)
- Introduction-Development-Conclusion structure
- Immediate TTS integration
- Dynamic prompt count based on audio duration
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from src.utils.config import Config
from src.utils.logging import get_logger, log_session_start, log_session_end
from src.controller.safety_checker import SafetyChecker
from src.controller.llama_controller import LlamaController

logger = get_logger()

class QwenScriptGenerator:
    def __init__(self):
        """Initialize Qwen script generator."""
        self.api_key = os.getenv('QWEN_API_KEY')
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.model = "qwen-max"
        self.safety_checker = SafetyChecker()
        self.llama_controller = LlamaController()
        
        # NEW: Script configuration
        self.config = {
            "target_characters": 8500,
            "part_1_chars": 3000,      # Introduction + Hook
            "part_2_chars": 3000,      # Development
            "part_3_chars": 2500,      # Conclusion + CTA
            "max_sentence_words": 8,   # Max 8 words per sentence
            "language": "en",          # English
            "opening_phrase": "Welcome to Synapse Daily",
            "closing_cta": "Like this video! Comment your thoughts below and subscribe for more fascinating stories!",
            "required_elements": {
                "shocking_hook": True,      # First 3 minutes
                "curiosity_questions": 3,   # Throughout script
                "real_facts_only": True,
                "emotional_triggers": True,
                "no_distortion": True
            }
        }
        
        logger.info("✅ QwenScriptGenerator initialized (UPDATED)")
    
    def generate_daily_script(self, topic: str) -> Dict:
        """
        Generate complete daily script with NEW structure.
        
        Args:
            topic (str): Daily topic
        
        Returns:
            Dict: Script data with paths, metadata, and audio info
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_session_start("Script Generation", session_id)
        
        logger.info(f"📝 Generating script for topic: {topic}")
        
        try:
            # 1. Generate 3-part script with Llama quality control
            script_data = self._generate_3part_script(topic)
            
            # 2. Validate with safety checker
            safety_results = self._validate_content(script_data)
            
            if not safety_results["is_safe"]:
                logger.warning("⚠️ Content failed safety check, requesting fixes...")
                script_data = self._request_qwen_fixes(topic, safety_results["issues"])
                safety_results = self._validate_content(script_data)
            
            # 3. Save script for TTS
            script_path = self._save_script(script_data["full_script"])
            
            # 4. Generate audio IMMEDIATELY
            audio_result = self._generate_audio_immediately(script_data["full_script"])
            
            # 5. Calculate prompt count based on audio duration
            prompt_count = self._calculate_prompt_count(audio_result["duration_seconds"])
            
            # 6. Generate visual prompts (dynamic count)
            prompts = self._generate_visual_prompts(script_data["full_script"], prompt_count)
            prompts_path = self._save_prompts(prompts)
            
            # 7. Generate metadata
            metadata = self._generate_metadata(topic, script_data, audio_result, safety_results)
            metadata_path = self._save_metadata(metadata)
            
            log_session_end(session_id, "complete", {
                "script_path": str(script_path),
                "audio_path": audio_result["audio_path"],
                "prompts_path": str(prompts_path),
                "total_characters": script_data["total_characters"],
                "audio_duration": audio_result["duration_seconds"],
                "prompt_count": prompt_count
            })
            
            logger.info(f"✅ Script generation complete!")
            logger.info(f"   Script: {script_path}")
            logger.info(f"   Audio: {audio_result['audio_path']} ({audio_result['duration_seconds']}s)")
            logger.info(f"   Prompts: {prompts_path} ({prompt_count} prompts)")
            logger.info(f"   Meta {metadata_path}")
            
            return {
                "script_path": str(script_path),
                "audio_path": audio_result["audio_path"],
                "prompts_path": str(prompts_path),
                "metadata_path": str(metadata_path),
                "total_characters": script_data["total_characters"],
                "audio_duration": audio_result["duration_seconds"],
                "prompt_count": prompt_count,
                "safety_passed": safety_results["is_safe"]
            }
            
        except Exception as e:
            logger.error(f"❌ Script generation failed: {str(e)}")
            log_session_end(session_id, "failed", {"error": str(e)})
            raise
    
    def _generate_3part_script(self, topic: str) -> Dict:
        """Generate script in 3 parts with Llama quality control."""
        
        parts = []
        total_chars = 0
        
        # PART 1: Introduction + Shocking Hook (3,000 chars)
        logger.info("📝 Generating Part 1: Introduction + Hook...")
        part1 = self._generate_script_part(
            topic,
            part_number=1,
            target_chars=self.config["part_1_chars"],
            section_type="introduction",
            requirements={
                "opening": self.config["opening_phrase"],
                "shocking_hook": True,
                "curiosity_question": 1
            }
        )
        parts.append(part1)
        total_chars += len(part1)
        logger.info(f"   Part 1: {len(part1)} characters")
        
        # Llama quality check before continuing
        quality_check = self.llama_controller.evaluate_script_part(part1, part_number=1)
        if not quality_check["approved"]:
            logger.warning(f"⚠️ Part 1 needs expansion: {quality_check['suggestions']}")
            part1 = self._expand_script_part(part1, quality_check["suggestions"])
            total_chars = total_chars - len(parts[0]) + len(part1)
            parts[0] = part1
        
        # PART 2: Development (3,000 chars)
        logger.info("📝 Generating Part 2: Development...")
        part2 = self._generate_script_part(
            topic,
            part_number=2,
            target_chars=self.config["part_2_chars"],
            section_type="development",
            requirements={
                "curiosity_questions": 2,
                "emotional_triggers": True,
                "real_facts": True
            }
        )
        parts.append(part2)
        total_chars += len(part2)
        logger.info(f"   Part 2: {len(part2)} characters")
        
        # Llama quality check
        quality_check = self.llama_controller.evaluate_script_part(part2, part_number=2)
        if not quality_check["approved"]:
            logger.warning(f"⚠️ Part 2 needs expansion: {quality_check['suggestions']}")
            part2 = self._expand_script_part(part2, quality_check["suggestions"])
            total_chars = total_chars - len(parts[1]) + len(part2)
            parts[1] = part2
        
        # PART 3: Conclusion + CTA (2,500 chars)
        logger.info("📝 Generating Part 3: Conclusion + CTA...")
        part3 = self._generate_script_part(
            topic,
            part_number=3,
            target_chars=self.config["part_3_chars"],
            section_type="conclusion",
            requirements={
                "closing_cta": self.config["closing_cta"],
                "curiosity_question": 1,
                "summary": True
            }
        )
        parts.append(part3)
        total_chars += len(part3)
        logger.info(f"   Part 3: {len(part3)} characters")
        
        # Combine parts
        full_script = "\n\n".join(parts)
        
        # Final character count adjustment
        if total_chars < self.config["target_characters"]:
            logger.info(f"📏 Script needs {self.config['target_characters'] - total_chars} more characters...")
            full_script = self._expand_to_target_length(full_script, self.config["target_characters"])
        elif total_chars > self.config["target_characters"] + 500:
            logger.info(f"✂️ Script exceeds target, trimming...")
            full_script = self._trim_to_target_length(full_script, self.config["target_characters"])
        
        # Final character count
        final_chars = len(full_script)
        logger.info(f"✅ Final script: {final_chars} characters (target: {self.config['target_characters']})")
        
        return {
            "full_script": full_script,
            "part_1": part1,
            "part_2": part2,
            "part_3": part3,
            "total_characters": final_chars,
            "parts": parts
        }
    
    def _generate_script_part(self, topic: str, part_number: int, target_chars: int, 
                             section_type: str, requirements: Dict) -> str:
        """Generate single part of script."""
        
        system_prompt = self._get_system_prompt_for_part(section_type, requirements)
        
        user_prompt = f"""
        Generate Part {part_number}/3 of a documentary script about: {topic}
        
        REQUIREMENTS:
        - Target: {target_chars} characters (including spaces)
        - Language: English
        - Max 8 words per sentence
        - No unnecessary repetition
        - High quality half-micro-storytelling
        - Based on REAL historical/scientific facts
        - Include specific details that trigger emotions and curiosity
        - NEVER make impossible claims or distort scientific facts
        
        STRUCTURE:
        {self._get_structure_requirements(section_type, requirements)}
        
        Generate ONLY the script content, no explanations.
        """
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.7,
                "result_format": "message"
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            content = result["output"]["choices"][0]["message"]["content"]
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"❌ Part {part_number} generation failed: {str(e)}")
            raise
    
    def _get_system_prompt_for_part(self, section_type: str, requirements: Dict) -> str:
        """Get system prompt based on section type."""
        
        base_prompt = """
        You are a professional documentary scriptwriter for YouTube channel "Synapse Daily".
        
        CRITICAL RULES:
        - Each sentence MUST be max 8 words
        - Count characters carefully (including spaces)
        - Write in English
        - Maintain meaning coherence throughout
        - No unnecessary repetition or nonsense
        - Use high quality half-micro-storytelling
        - Base content on REAL historical/scientific facts
        - Include specific details that trigger human emotions and curiosity
        - NEVER make impossible claims or distort scientific facts
        - Data security and historical accuracy are paramount
        """
        
        if section_type == "introduction":
            return f"""
            {base_prompt}
            
            SECTION: Introduction + Shocking Hook
            
            MUST INCLUDE:
            - Start with: "Welcome to Synapse Daily"
            - First 3 minutes MUST have SHOCKING HOOK (verified facts)
            - Include 1 curiosity-sparking question
            - Set up the mystery/story dramatically
            - Make viewers want to continue watching
            """
        
        elif section_type == "development":
            return f"""
            {base_prompt}
            
            SECTION: Development (Main Content)
            
            MUST INCLUDE:
            - 2-3 curiosity-sparking questions throughout
            - Include specific details that trigger emotions
            - Build tension and interest progressively
            - Maintain factual accuracy
            - Keep sentences engaging and dramatic
            """
        
        elif section_type == "conclusion":
            return f"""
            {base_prompt}
            
            SECTION: Conclusion + Call-to-Action
            
            MUST INCLUDE:
            - Summarize key points dramatically
            - Include 1 final curiosity question
            - End with CTA: "Like this video! Comment your thoughts below and subscribe for more fascinating stories!"
            - Leave viewers wanting more
            - Maintain emotional impact
            """
        
        return base_prompt
    
    def _get_structure_requirements(self, section_type: str, requirements: Dict) -> str:
        """Get structure requirements for section."""
        
        structures = {
            "introduction": """
            Structure:
            1. Opening phrase: "Welcome to Synapse Daily"
            2. Shocking hook (verified fact that grabs attention)
            3. Set up the mystery/story
            4. First curiosity question
            5. Transition to main content
            """,
            
            "development": """
            Structure:
            1. Continue the story dramatically
            2. Include 2 curiosity questions
            3. Add emotional triggers
            4. Maintain factual accuracy
            5. Build tension progressively
            """,
            
            "conclusion": """
            Structure:
            1. Summarize key points
            2. Final curiosity question
            3. Call-to-action (exact phrase)
            4. Emotional closing
            """
        }
        
        return structures.get(section_type, "")
    
    def _expand_script_part(self, part: str, suggestions: List[str]) -> str:
        """Expand script part based on Llama suggestions."""
        
        expand_prompt = f"""
        Expand this script section based on these suggestions:
        
        Original:
        {part[:2000]}
        
        Suggestions:
        {json.dumps(suggestions, indent=2)}
        
        Requirements:
        - Maintain 8 words max per sentence
        - Keep factual accuracy
        - Add emotional triggers
        - Maintain coherence with original
        """
        
        # Call Qwen for expansion
        # (Similar API call as _generate_script_part)
        # Return expanded content
        return part  # Placeholder
    
    def _expand_to_target_length(self, script: str, target: int) -> str:
        """Expand script to reach target character count."""
        
        current_chars = len(script)
        needed_chars = target - current_chars
        
        if needed_chars <= 0:
            return script
        
        expand_prompt = f"""
        Expand this script by approximately {needed_chars} characters:
        
        Current script:
        {script[:3000]}
        
        Requirements:
        - Maintain 8 words max per sentence
        - Add emotional details
        - Keep factual accuracy
        - Maintain coherence
        - English language
        """
        
        # Call Qwen for expansion
        # Return expanded script
        return script  # Placeholder
    
    def _trim_to_target_length(self, script: str, target: int) -> str:
        """Trim script to reach target character count."""
        
        # Intelligent trimming (remove redundancy, keep key content)
        # Return trimmed script
        return script[:target]  # Simplified
    
    def _generate_audio_immediately(self, script: str) -> Dict:
        """Generate audio from script immediately after script creation."""
        
        try:
            from src.tts import generate_voice_with_edge_tts
            import asyncio
            
            logger.info("🎙️ Generating audio immediately...")
            
            # Create audio directory
            audio_dir = Config.AUDIO_DIR
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate audio file
            timestamp = datetime.now().strftime("%Y%m%d")
            audio_path = audio_dir / f"{timestamp}_narration.mp3"
            
            # Run TTS
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
            
            # Calculate duration
            import mutagen
            audio = mutagen.File(str(audio_path))
            duration_seconds = int(audio.info.length) if audio else 0
            
            logger.info(f"✅ Audio generated: {audio_path} ({duration_seconds}s)")
            
            return {
                "audio_path": str(audio_path),
                "duration_seconds": duration_seconds
            }
            
        except Exception as e:
            logger.error(f"❌ Audio generation failed: {str(e)}")
            # Return fallback
            return {
                "audio_path": "",
                "duration_seconds": 600  # Default 10 minutes
            }
    
    def _calculate_prompt_count(self, audio_duration: int) -> int:
        """Calculate number of video prompts based on audio duration."""
        
        # Each video clip = 5 seconds
        clips_needed = audio_duration // 5
        
        # Add 10% buffer for transitions
        prompt_count = int(clips_needed * 1.1)
        
        # Ensure minimum 120 prompts for 10-minute video
        prompt_count = max(prompt_count, 120)
        
        logger.info(f"📊 Calculated {prompt_count} prompts for {audio_duration}s audio")
        
        return prompt_count
    
    def _generate_visual_prompts(self, script: str, prompt_count: int) -> List[Dict]:
        """Generate visual prompts based on script and count."""
        
        from src.script.prompt_engine import PromptEngine
        
        engine = PromptEngine()
        prompts = engine.generate_prompts_from_script(script, prompt_count)
        
        return prompts
    
    def _validate_content(self, script_ Dict) -> Dict:
        """Validate generated content with safety checker."""
        
        script = script_data.get("full_script", "")
        
        # Check script
        script_results = self.safety_checker.check_script(script)
        
        # Check character count
        char_count = len(script)
        char_valid = abs(char_count - self.config["target_characters"]) <= 500
        
        is_safe = script_results["valid"] and char_valid
        
        return {
            "is_safe": is_safe,
            "script_results": script_results,
            "character_count": char_count,
            "character_valid": char_valid
        }
    
    def _save_script(self, script: str) -> Path:
        """Save script for TTS generation."""
        scripts_dir = Config.SCRIPTS_DIR
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d")
        script_path = scripts_dir / f"{timestamp}_script.txt"
        
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        
        logger.info(f"📄 Script saved: {script_path}")
        return script_path
    
    def _save_prompts(self, prompts: List[Dict]) -> Path:
        """Save prompts for Kaggle video generation."""
        prompts_dir = Config.PROMPTS_DIR
        prompts_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d")
        prompts_path = prompts_dir / f"{timestamp}_prompts.json"
        
        with open(prompts_path, "w", encoding="utf-8") as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Prompts saved: {prompts_path}")
        return prompts_path
    
    def _save_metadata(self, meta Dict) -> Path:
        """Save generation metadata."""
        metadata_dir = Config.LOGS_DIR
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d")
        metadata_path = metadata_dir / f"{timestamp}_metadata.json"
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Metadata saved: {metadata_path}")
        return metadata_path
    
    def _generate_metadata(self, topic: str, script_ Dict, audio_result: Dict, 
                          safety_results: Dict) -> Dict:
        """Generate generation metadata."""
        return {
            "topic": topic,
            "generated_at": datetime.now().isoformat(),
            "model": self.model,
            "config": self.config,
            "statistics": {
                "total_characters": script_data["total_characters"],
                "target_characters": self.config["target_characters"],
                "audio_duration_seconds": audio_result["duration_seconds"],
                "prompt_count": self._calculate_prompt_count(audio_result["duration_seconds"])
            },
            "safety": {
                "passed": safety_results["is_safe"],
                "character_count_valid": safety_results.get("character_valid", False)
            },
            "files": {
                "script": f"{datetime.now().strftime('%Y%m%d')}_script.txt",
                "audio": audio_result["audio_path"].split("/")[-1],
                "prompts": f"{datetime.now().strftime('%Y%m%d')}_prompts.json"
            }
        }
    
    def get_todays_topic(self) -> str:
        """Get today's topic from sidea.txt or generate new one."""
        sidea_file = Config.SIDEA_FILE
        
        if sidea_file.exists():
            with open(sidea_file, "r") as f:
                index = int(f.read().strip())
            
            # Topic list
            topics = [
                "European Retro-Futurism in Urban Design (Netherlands) 1977",
                "Cold War Technology Archive Sealed by CIA (Global) 1980",
                "The Birth of Personal Computing (Silicon Valley) 1975",
                # Add more...
            ]
            
            topic = topics[index % len(topics)]
            
            # Update index
            with open(sidea_file, "w") as f:
                f.write(str(index + 1))
            
            return topic
        else:
            return "European Retro-Futurism in Urban Design (Netherlands) 1977"

def generate_daily_script(topic: str = None) -> Dict:
    """Main function to generate daily script."""
    generator = QwenScriptGenerator()
    
    if not topic:
        topic = generator.get_todays_topic()
    
    logger.info(f"🎯 Today's topic: {topic}")
    
    result = generator.generate_daily_script(topic)
    
    return result

if __name__ == "__main__":
    result = generate_daily_script()
    print(json.dumps(result, indent=2))
