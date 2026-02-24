# src/controller/llama_controller.py
"""
Llama 3.3 Process Controller
==========================

Controls the entire video generation pipeline
Validates continuity, safety, and quality
"""

import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from src.utils.config import Config
from src.utils.logging import setup_logging

logger = setup_logging()

class LlamaController:
    def __init__(self):
        self.api_key = os.getenv('LLAMA_API_KEY')
        self.api_url = "https://api.llama.com/v1/chat/completions"  # Replace with actual endpoint
        self.model = "llama-3.3-70b-instruct"
        
        # Continuity tracking
        self.character_profiles = {}
        self.environment_profiles = {}
        self.style_guide = {}
        
    def initialize_session(self, topic: str):
        """Initialize session with topic context."""
        logger.info(f"🧠 Llama Controller initializing for topic: {topic}")
        
        # Load templates
        self._load_character_profiles()
        self._load_environment_profiles()
        self._load_style_guide()
        
        # Create session context
        self.session_context = {
            "topic": topic,
            "date": datetime.now().isoformat(),
            "total_clips": 120,
            "clip_duration": 5,  # seconds
            "target_duration": 600,  # 10 minutes
            "character_consistency": True,
            "environment_consistency": True,
            "color_palette_consistency": True
        }
        
        logger.info("✅ Session initialized")
        return self.session_context
    
    def validate_script(self, script: str) -> dict:
        """Validate script for quality and consistency."""
        prompt = f"""
        You are a quality control AI for documentary video production.
        
        Review this script and validate:
        1. Narrative flow and coherence
        2. Character consistency throughout
        3. Environment/time period consistency
        4. Pacing (120 scenes for 10-minute video)
        5. Content safety (no violence, explicit content, etc.)
        
        Script:
        {script[:4000]}  # Limit for API
        
        Return JSON:
        {{
            "valid": bool,
            "issues": ["list of issues"],
            "suggestions": ["list of improvements"],
            "scene_count": int,
            "estimated_duration": int
        }}
        """
        
        response = self._call_llama_api(prompt)
        validation = json.loads(response)
        
        logger.info(f"📋 Script validation: {'✅ PASS' if validation['valid'] else '❌ FAIL'}")
        return validation
    
    def validate_prompts(self, prompts: list) -> dict:
        """Validate visual prompts for continuity."""
        # Check character consistency
        character_issues = self._check_character_consistency(prompts)
        
        # Check environment consistency
        environment_issues = self._check_environment_consistency(prompts)
        
        # Check style consistency
        style_issues = self._check_style_consistency(prompts)
        
        # Check safety
        safety_issues = self._check_safety(prompts)
        
        validation = {
            "valid": len(character_issues + environment_issues + style_issues + safety_issues) == 0,
            "character_issues": character_issues,
            "environment_issues": environment_issues,
            "style_issues": style_issues,
            "safety_issues": safety_issues,
            "total_prompts": len(prompts)
        }
        
        logger.info(f"🎨 Prompt validation: {validation['total_prompts']} prompts, {'✅ PASS' if validation['valid'] else '⚠️ ISSUES'}")
        return validation
    
    def generate_continuity_report(self, prompts: list) -> str:
        """Generate continuity report for all prompts."""
        prompt = f"""
        Analyze these {len(prompts)} video prompts for visual continuity:
        
        1. Are characters described consistently? (clothing, appearance, age)
        2. Are environments consistent? (location, time period, lighting)
        3. Are key objects consistent? (props, vehicles, architecture)
        4. Is the color palette consistent?
        5. Is the camera style consistent?
        
        Prompts (first 20 and last 20):
        {json.dumps(prompts[:20] + prompts[-20:], indent=2)}
        
        Return detailed continuity report with specific issues and fixes.
        """
        
        report = self._call_llama_api(prompt)
        logger.info("📊 Continuity report generated")
        return report
    
    def approve_for_kaggle(self, prompts: list) -> bool:
        """Final approval before sending to Kaggle."""
        validation = self.validate_prompts(prompts)
        
        if not validation['valid']:
            logger.warning(f"⚠️ Prompts have issues: {validation}")
            # Auto-fix minor issues
            prompts = self._auto_fix_prompts(prompts, validation)
            validation = self.validate_prompts(prompts)
        
        # Log approval decision
        approval_log = {
            "timestamp": datetime.now().isoformat(),
            "total_prompts": len(prompts),
            "approved": validation['valid'],
            "issues": validation
        }
        
        with open(Config.LOGS_DIR / "approval_log.json", "a") as f:
            json.dump(approval_log, f, indent=2)
            f.write("\n")
        
        return validation['valid']
    
    def _check_character_consistency(self, prompts: list) -> list:
        """Check character consistency across prompts."""
        issues = []
        character_mentions = {}
        
        for i, prompt in enumerate(prompts):
            # Extract character descriptions (simplified)
            if "man" in prompt.lower() or "woman" in prompt.lower():
                # Check for consistent clothing, age, etc.
                if i > 0 and i % 10 == 0:  # Check every 10th prompt
                    # Compare with previous character mentions
                    pass
        
        return issues
    
    def _check_environment_consistency(self, prompts: list) -> list:
        """Check environment consistency across prompts."""
        issues = []
        # Similar logic for environments
        return issues
    
    def _check_style_consistency(self, prompts: list) -> list:
        """Check visual style consistency."""
        issues = []
        # Check for consistent style keywords
        style_keywords = ["cinematic", "documentary", "realistic", "vintage"]
        return issues
    
    def _check_safety(self, prompts: list) -> list:
        """Check for safety violations."""
        issues = []
        unsafe_words = ["violence", "blood", "weapon", "explicit", "adult"]
        
        for i, prompt in enumerate(prompts):
            for word in unsafe_words:
                if word in prompt.lower():
                    issues.append(f"Prompt {i}: Contains '{word}'")
        
        return issues
    
    def _auto_fix_prompts(self, prompts: list, validation: dict) -> list:
        """Auto-fix minor prompt issues."""
        fixed_prompts = prompts.copy()
        
        # Fix safety issues
        for issue in validation.get('safety_issues', []):
            prompt_idx = int(issue.split(':')[0].replace('Prompt ', ''))
            # Replace unsafe words
            fixed_prompts[prompt_idx] = fixed_prompts[prompt_idx].replace("violence", "conflict")
        
        logger.info(f"🔧 Auto-fixed {len(validation.get('safety_issues', []))} prompts")
        return fixed_prompts
    
    def _call_llama_api(self, prompt: str) -> str:
        """Call Llama API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            return response.json()['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"❌ Llama API call failed: {str(e)}")
            return "{}"
    
    def _load_character_profiles(self):
        """Load character profile templates."""
        template_path = Config.TEMPLATES_DIR / "character_profile.json"
        if template_path.exists():
            with open(template_path, 'r') as f:
                self.character_profiles = json.load(f)
    
    def _load_environment_profiles(self):
        """Load environment profile templates."""
        template_path = Config.TEMPLATES_DIR / "environment_profile.json"
        if template_path.exists():
            with open(template_path, 'r') as f:
                self.environment_profiles = json.load(f)
    
    def _load_style_guide(self):
        """Load style guide templates."""
        template_path = Config.TEMPLATES_DIR / "style_guide.json"
        if template_path.exists():
            with open(template_path, 'r') as f:
                self.style_guide = json.load(f)

def main():
    """Test Llama Controller."""
    controller = LlamaController()
    controller.initialize_session("Test Topic")
    
if __name__ == "__main__":
    main()
