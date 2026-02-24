# src/script/prompt_engine.py
"""
Prompt Engine
============

Generates visual prompts from script with continuity tracking
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict
from src.utils.config import Config
from src.utils.logging import get_logger

logger = get_logger()

class PromptEngine:
    def __init__(self):
        """Initialize prompt engine with continuity tracking."""
        self.character_registry = {}
        self.environment_registry = {}
        self.style_keywords = [
            "cinematic", "documentary", "realistic", "vintage", "1970s",
            "professional photography", "museum exhibit quality"
        ]
        
        logger.info("✅ PromptEngine initialized")
    
    def extract_scenes_from_script(self, script: str) -> List[Dict]:
        """
        Extract scene information from script.
        
        Args:
            script (str): Full script text
        
        Returns:
            List[Dict]: List of scene dictionaries
        """
        scenes = []
        
        # Split by chapters
        chapters = re.split(r'Chapter\s*\d+:', script, flags=re.IGNORECASE)
        
        for i, chapter in enumerate(chapters[1:], 1):  # Skip first empty split
            chapter_lines = chapter.strip().split('\n')
            chapter_title = chapter_lines[0].strip() if chapter_lines else f"Chapter {i}"
            
            # Extract key visual elements from chapter
            visual_elements = self._extract_visual_elements(chapter)
            
            scenes.append({
                "chapter": i,
                "title": chapter_title,
                "content": chapter,
                "visual_elements": visual_elements
            })
        
        logger.info(f"📋 Extracted {len(scenes)} scenes from script")
        return scenes
    
    def _extract_visual_elements(self, text: str) -> Dict:
        """Extract visual elements from text."""
        elements = {
            "characters": [],
            "locations": [],
            "objects": [],
            "time_period": "1970s",
            "mood": "documentary"
        }
        
        # Simple keyword extraction (use Llama for production)
        character_keywords = ["man", "woman", "person", "architect", "designer", "official"]
        location_keywords = ["city", "building", "street", "Amsterdam", "Netherlands", "urban"]
        object_keywords = ["car", "train", "architecture", "design", "plan"]
        
        text_lower = text.lower()
        
        for keyword in character_keywords:
            if keyword in text_lower:
                elements["characters"].append(keyword)
        
        for keyword in location_keywords:
            if keyword in text_lower:
                elements["locations"].append(keyword)
        
        for keyword in object_keywords:
            if keyword in text_lower:
                elements["objects"].append(keyword)
        
        return elements
    
    def generate_prompts(self, scenes: List[Dict], target_count: int = 120) -> List[Dict]:
        """
        Generate visual prompts from scenes.
        
        Args:
            scenes (List[Dict]): List of scene dictionaries
            target_count (int): Target number of prompts
        
        Returns:
            List[Dict]: List of prompt dictionaries
        """
        prompts = []
        
        # Calculate prompts per scene
        prompts_per_scene = max(1, target_count // len(scenes))
        
        for scene in scenes:
            # Generate prompts for this scene
            scene_prompts = self._generate_scene_prompts(
                scene,
                prompts_per_scene
            )
            prompts.extend(scene_prompts)
        
        # Ensure we have exactly target_count prompts
        while len(prompts) < target_count:
            # Add overview prompts
            overview_prompt = self._create_overview_prompt(scenes)
            prompts.append(overview_prompt)
        
        # Trim to target count
        prompts = prompts[:target_count]
        
        # Add sequential IDs
        for i, prompt in enumerate(prompts):
            prompt["id"] = f"vid_{i:03d}"
            prompt["scene_number"] = i + 1
        
        logger.info(f"🎨 Generated {len(prompts)} visual prompts")
        return prompts
    
    def _generate_scene_prompts(self, scene: Dict, count: int) -> List[Dict]:
        """Generate multiple prompts for a single scene."""
        prompts = []
        
        chapter = scene["chapter"]
        title = scene["title"]
        elements = scene["visual_elements"]
        
        # Create variation prompts
        for i in range(count):
            # Build prompt with continuity
            prompt_text = self._build_prompt_with_continuity(
                title, elements, variation=i
            )
            
            prompts.append({
                "chapter": chapter,
                "prompt": prompt_text,
                "duration": 5,
                "style": "cinematic documentary"
            })
        
        return prompts
    
    def _build_prompt_with_continuity(self, title: str, elements: Dict, variation: int = 0) -> str:
        """Build prompt with continuity constraints."""
        # Base prompt
        base = f"A cinematic, documentary-style image representing '{title}'."
        
        # Add character consistency
        if elements["characters"]:
            char_desc = ", ".join(elements["characters"][:2])
            base += f" Featuring {char_desc} in 1970s attire."
        
        # Add environment consistency
        if elements["locations"]:
            loc_desc = ", ".join(elements["locations"][:2])
            base += f" Set in {loc_desc}."
        
        # Add style keywords
        style = ", ".join(self.style_keywords[:4])
        base += f" {style}."
        
        # Add variation
        variations = [
            "Wide establishing shot.",
            "Medium shot with natural lighting.",
            "Close-up on key details.",
            "Panoramic view.",
            "Archival footage style."
        ]
        base += f" {variations[variation % len(variations)]}"
        
        # Safety filter
        base = self._sanitize_prompt(base)
        
        return base
    
    def _create_overview_prompt(self, scenes: List[Dict]) -> Dict:
        """Create overview prompt for transition scenes."""
        return {
            "chapter": 0,
            "prompt": "Professional overview image showing multiple related elements. Documentary style, historical archive quality, cinematic lighting. 1970s European urban design theme.",
            "duration": 5,
            "style": "cinematic documentary"
        }
    
    def _sanitize_prompt(self, prompt: str) -> str:
        """Remove potentially problematic words."""
        unsafe_words = [
            "violence", "blood", "weapon", "gun", "knife", "attack", "fight",
            "nude", "sex", "explicit", "adult", "horror", "scary", "terror",
            "kill", "murder", "death", "corpse", "zombie", "ghost", "demon",
            "nuclear", "bomb", "explosion", "war", "battle", "combat"
        ]
        
        sanitized = prompt.lower()
        for word in unsafe_words:
            sanitized = sanitized.replace(word, "scene")
        
        # Capitalize first letter
        if sanitized:
            sanitized = sanitized[0].upper() + sanitized[1:]
        
        return sanitized
    
    def save_prompts(self, prompts: List[Dict], output_path: str = None):
        """Save prompts to JSON file."""
        if not output_path:
            output_path = Config.PROMPTS_DIR / f"{self._get_date()}_prompts.json"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Prompts saved: {output_path}")
        return output_path
    
    def _get_date(self) -> str:
        """Get current date string."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d")
    
    def validate_prompts(self, prompts: List[Dict]) -> Dict:
        """Validate prompts for safety and quality."""
        issues = []
        
        # Check count
        if len(prompts) < 120:
            issues.append(f"Only {len(prompts)} prompts, need 120")
        
        # Check for unsafe content
        unsafe_words = ["violence", "blood", "weapon", "explicit", "adult"]
        
        for i, prompt in enumerate(prompts):
            prompt_text = prompt.get("prompt", "").lower()
            for word in unsafe_words:
                if word in prompt_text:
                    issues.append(f"Prompt {i}: Contains '{word}'")
        
        # Check prompt length
        for i, prompt in enumerate(prompts):
            prompt_text = prompt.get("prompt", "")
            if len(prompt_text) < 20:
                issues.append(f"Prompt {i}: Too short ({len(prompt_text)} chars)")
            elif len(prompt_text) > 500:
                issues.append(f"Prompt {i}: Too long ({len(prompt_text)} chars)")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "total_prompts": len(prompts)
        }

def generate_visual_prompts(script_path: str = None, target_count: int = 120):
    """
    Main function to generate visual prompts.
    
    Args:
        script_path (str, optional): Path to script file
        target_count (int): Target number of prompts
    """
    try:
        # Load script
        if not script_path:
            script_path = Config.SCRIPTS_DIR / f"{PromptEngine()._get_date()}_script.txt"
        
        logger.info(f"📖 Loading script: {script_path}")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            script = f.read()
        
        # Initialize engine
        engine = PromptEngine()
        
        # Extract scenes
        scenes = engine.extract_scenes_from_script(script)
        
        # Generate prompts
        prompts = engine.generate_prompts(scenes, target_count)
        
        # Validate
        validation = engine.validate_prompts(prompts)
        
        if not validation["valid"]:
            logger.warning(f"⚠️ Prompt validation issues: {validation['issues']}")
        
        # Save prompts
        output_path = engine.save_prompts(prompts)
        
        logger.info(f"✅ Generated {len(prompts)} prompts successfully")
        
        return {
            "prompts_path": str(output_path),
            "total_prompts": len(prompts),
            "validation": validation
        }
        
    except Exception as e:
        logger.error(f"❌ Prompt generation failed: {str(e)}")
        raise

if __name__ == "__main__":
    result = generate_visual_prompts()
    print(json.dumps(result, indent=2))
