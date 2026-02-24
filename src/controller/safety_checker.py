# src/controller/safety_checker.py
"""
Safety Checker
============

Validates scripts and prompts for safety, quality, and compliance
Integrated with Llama 3.3 for AI-powered content review
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
from src.utils.config import Config
from src.utils.logging import get_logger

logger = get_logger()

class SafetyChecker:
    def __init__(self):
        """Initialize safety checker with violation categories."""
        self.llama_api_key = os.getenv('LLAMA_API_KEY')
        self.llama_api_url = "https://api.llama.com/v1/chat/completions"
        
        # Safety violation categories
        self.violation_categories = {
            "violence": [
                "violence", "blood", "gore", "murder", "kill", "death", "corpse",
                "weapon", "gun", "knife", "sword", "bomb", "explosion", "attack",
                "fight", "battle", "war", "combat", "shooting", "stabbing"
            ],
            "adult_content": [
                "nude", "naked", "sex", "sexual", "explicit", "adult", "porn",
                "erotic", "intimate", "breast", "genital", "orgy", "fetish"
            ],
            "horror": [
                "horror", "scary", "terror", "frightening", "terrifying", "nightmare",
                "zombie", "ghost", "demon", "monster", "haunted", "possessed",
                "creepy", "disturbing", "gruesome", "macabre"
            ],
            "illegal_activities": [
                "drug", "cocaine", "heroin", "meth", "marijuana", "illegal",
                "theft", "robbery", "hacking", "fraud", "smuggling", "trafficking"
            ],
            "hate_speech": [
                "racist", "discrimination", "hate", "supremacy", "extremist",
                "terrorist", "radical", "bigot", "prejudice"
            ],
            "self_harm": [
                "suicide", "self-harm", "cutting", "overdose", "anorexia",
                "bulimia", "depression", "hopeless"
            ]
        }
        
        # Required content elements for documentary quality
        self.required_elements = {
            "educational_value": True,
            "historical_accuracy": True,
            "cultural_sensitivity": True,
            "age_appropriate": "general"  # general, teen, mature
        }
        
        logger.info("✅ SafetyChecker initialized")
    
    def check_script(self, script: str) -> Dict:
        """
        Comprehensive script safety check.
        
        Args:
            script (str): Full script text
        
        Returns:
            Dict: Validation results with issues and suggestions
        """
        logger.info("🔍 Checking script for safety violations...")
        
        results = {
            "valid": True,
            "violations": [],
            "warnings": [],
            "suggestions": [],
            "scores": {}
        }
        
        # 1. Keyword-based violation check
        keyword_violations = self._check_keywords(script)
        if keyword_violations:
            results["violations"].extend(keyword_violations)
            results["valid"] = False
        
        # 2. AI-powered content analysis (Llama)
        ai_analysis = self._llama_content_analysis(script)
        if ai_analysis["flagged"]:
            results["violations"].extend(ai_analysis["issues"])
            results["valid"] = False
        
        # 3. Quality checks
        quality_results = self._check_quality(script)
        results["warnings"].extend(quality_results["warnings"])
        results["suggestions"].extend(quality_results["suggestions"])
        results["scores"] = quality_results["scores"]
        
        # 4. Chapter structure validation
        structure_results = self._check_chapter_structure(script)
        results["warnings"].extend(structure_results["warnings"])
        
        # Log results
        if results["valid"]:
            logger.info(f"✅ Script passed safety check (Score: {results['scores'].get('overall', 0)}/100)")
        else:
            logger.warning(f"❌ Script failed safety check: {len(results['violations'])} violations")
        
        return results
    
    def check_prompts(self, prompts: List[Dict]) -> Dict:
        """
        Check visual prompts for safety and continuity.
        
        Args:
            prompts (List[Dict]): List of prompt dictionaries
        
        Returns:
            Dict: Validation results
        """
        logger.info(f"🔍 Checking {len(prompts)} prompts for safety...")
        
        results = {
            "valid": True,
            "violations": [],
            "warnings": [],
            "flagged_prompts": [],
            "continuity_issues": []
        }
        
        # Check each prompt
        for i, prompt_data in enumerate(prompts):
            prompt_text = prompt_data.get("prompt", "")
            
            # Keyword check
            violations = self._check_keywords(prompt_text)
            if violations:
                results["violations"].extend(violations)
                results["flagged_prompts"].append({
                    "index": i,
                    "prompt": prompt_text[:100],
                    "violations": [v["category"] for v in violations]
                })
                results["valid"] = False
        
        # Continuity check
        continuity_issues = self._check_continuity(prompts)
        if continuity_issues:
            results["continuity_issues"] = continuity_issues
            results["warnings"].extend([f"Continuity: {issue}" for issue in continuity_issues])
        
        # Quality check
        quality_issues = self._check_prompt_quality(prompts)
        results["warnings"].extend(quality_issues)
        
        # Log results
        if results["valid"]:
            logger.info(f"✅ All {len(prompts)} prompts passed safety check")
        else:
            logger.warning(f"❌ {len(results['flagged_prompts'])} prompts flagged for violations")
        
        return results
    
    def auto_fix_script(self, script: str, violations: List[Dict]) -> str:
        """
        Auto-fix safety violations in script.
        
        Args:
            script (str): Original script
            violations (List[Dict]): List of violations to fix
        
        Returns:
            str: Fixed script
        """
        logger.info(f"🔧 Auto-fixing {len(violations)} violations...")
        
        fixed_script = script
        
        for violation in violations:
            category = violation.get("category", "")
            word = violation.get("word", "")
            
            # Replace with safe alternatives
            replacements = {
                "violence": "conflict",
                "blood": "liquid",
                "weapon": "object",
                "kill": "defeat",
                "death": "passing",
                "bomb": "device",
                "explosion": "burst",
                "attack": "approach",
                "fight": "struggle",
                "war": "conflict",
                "gun": "device",
                "knife": "tool"
            }
            
            if word.lower() in replacements:
                fixed_script = fixed_script.replace(word, replacements[word.lower()])
                logger.debug(f"   Replaced '{word}' → '{replacements[word.lower()]}'")
        
        logger.info(f"✅ Script auto-fixed")
        return fixed_script
    
    def auto_fix_prompts(self, prompts: List[Dict], violations: List[Dict]) -> List[Dict]:
        """
        Auto-fix safety violations in prompts.
        
        Args:
            prompts (List[Dict]): Original prompts
            violations (List[Dict]): Violations to fix
        
        Returns:
            List[Dict]: Fixed prompts
        """
        logger.info(f"🔧 Auto-fixing prompt violations...")
        
        fixed_prompts = prompts.copy()
        
        replacements = {
            "violence": "dramatic scene",
            "blood": "red liquid",
            "weapon": "object",
            "gun": "device",
            "knife": "tool",
            "bomb": "device",
            "explosion": "bright flash",
            "attack": "approach",
            "fight": "confrontation",
            "war": "conflict era",
            "kill": "defeat",
            "death": "passing",
            "scary": "atmospheric",
            "horror": "mysterious",
            "terror": "tension"
        }
        
        for i, prompt_data in enumerate(fixed_prompts):
            prompt_text = prompt_data.get("prompt", "")
            
            for unsafe_word, safe_replacement in replacements.items():
                if unsafe_word in prompt_text.lower():
                    # Case-insensitive replacement
                    pattern = re.compile(re.escape(unsafe_word), re.IGNORECASE)
                    prompt_text = pattern.sub(safe_replacement, prompt_text)
                    fixed_prompts[i]["prompt"] = prompt_text
        
        logger.info(f"✅ Prompts auto-fixed")
        return fixed_prompts
    
    def _check_keywords(self, text: str) -> List[Dict]:
        """Check text for unsafe keywords."""
        violations = []
        text_lower = text.lower()
        
        for category, keywords in self.violation_categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    violations.append({
                        "category": category,
                        "word": keyword,
                        "severity": "high" if category in ["violence", "adult_content"] else "medium"
                    })
        
        return violations
    
    def _llama_content_analysis(self, script: str) -> Dict:
        """Use Llama 3.3 for AI-powered content analysis."""
        try:
            import requests
            
            prompt = f"""
            You are a content safety reviewer for YouTube documentaries.
            
            Analyze this script for:
            1. Violence or harmful content
            2. Adult or explicit themes
            3. Horror or disturbing imagery
            4. Illegal activities
            5. Hate speech or discrimination
            6. Self-harm references
            
            Return JSON:
            {{
                "flagged": bool,
                "issues": ["list of specific issues"],
                "risk_level": "low|medium|high",
                "suitable_for_youtube": bool
            }}
            
            Script (first 3000 chars):
            {script[:3000]}
            """
            
            headers = {
                "Authorization": f"Bearer {self.llama_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "llama-3.3-70b-instruct",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            response = requests.post(self.llama_api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON from response
            analysis = json.loads(content.strip())
            
            logger.debug(f"🤖 Llama analysis: flagged={analysis.get('flagged', False)}")
            return analysis
            
        except Exception as e:
            logger.warning(f"⚠️ Llama analysis failed: {str(e)}")
            return {"flagged": False, "issues": [], "risk_level": "low", "suitable_for_youtube": True}
    
    def _check_quality(self, script: str) -> Dict:
        """Check script quality metrics."""
        results = {
            "warnings": [],
            "suggestions": [],
            "scores": {}
        }
        
        # Word count
        word_count = len(script.split())
        if word_count < 3000:
            results["warnings"].append(f"Script too short: {word_count} words (recommended: 3000+)")
        elif word_count > 5000:
            results["warnings"].append(f"Script too long: {word_count} words (recommended: 3000-5000)")
        
        # Chapter count
        chapter_count = len(re.findall(r'Chapter\s*\d+:', script, re.IGNORECASE))
        if chapter_count < 13:
            results["warnings"].append(f"Only {chapter_count} chapters (recommended: 13)")
        
        # Calculate scores
        results["scores"] = {
            "length": min(100, (word_count / 3000) * 100),
            "structure": min(100, (chapter_count / 13) * 100),
            "overall": min(100, ((word_count / 3000) * 50 + (chapter_count / 13) * 50))
        }
        
        return results
    
    def _check_chapter_structure(self, script: str) -> Dict:
        """Check chapter structure and flow."""
        results = {"warnings": []}
        
        chapters = re.split(r'Chapter\s*\d+:', script, flags=re.IGNORECASE)
        
        for i, chapter in enumerate(chapters[1:], 1):
            chapter_words = len(chapter.strip().split())
            if chapter_words < 200:
                results["warnings"].append(f"Chapter {i} too short: {chapter_words} words")
            elif chapter_words > 400:
                results["warnings"].append(f"Chapter {i} too long: {chapter_words} words")
        
        return results
    
    def _check_continuity(self, prompts: List[Dict]) -> List[str]:
        """Check for continuity issues between prompts."""
        issues = []
        
        # Track recurring elements
        characters = {}
        locations = {}
        time_periods = {}
        
        for i, prompt_data in enumerate(prompts):
            prompt = prompt_data.get("prompt", "").lower()
            
            # Simple continuity checks (use Llama for production)
            if "1970s" in prompt:
                time_periods[i] = "1970s"
            elif "1980s" in prompt:
                time_periods[i] = "1980s"
            
            # Check for major inconsistencies
            if len(time_periods) > 1:
                unique_periods = set(time_periods.values())
                if len(unique_periods) > 2:
                    issues.append(f"Multiple time periods detected: {unique_periods}")
        
        return issues[:5]  # Limit to 5 issues
    
    def _check_prompt_quality(self, prompts: List[Dict]) -> List[str]:
        """Check prompt quality metrics."""
        issues = []
        
        for i, prompt_data in enumerate(prompts):
            prompt = prompt_data.get("prompt", "")
            
            if len(prompt) < 20:
                issues.append(f"Prompt {i}: Too short ({len(prompt)} chars)")
            elif len(prompt) > 500:
                issues.append(f"Prompt {i}: Too long ({len(prompt)} chars)")
            
            # Check for visual descriptiveness
            visual_keywords = ["image", "scene", "view", "shot", "camera", "lighting", "color"]
            has_visual = any(kw in prompt.lower() for kw in visual_keywords)
            
            if not has_visual:
                issues.append(f"Prompt {i}: Lacks visual description keywords")
        
        return issues[:10]  # Limit to 10 issues
    
    def generate_safety_report(self, script_results: Dict, prompt_results: Dict) -> str:
        """Generate comprehensive safety report."""
        report = []
        report.append("=" * 60)
        report.append("🛡️  SAFETY CHECK REPORT")
        report.append("=" * 60)
        
        # Script results
        report.append("\n📄 SCRIPT ANALYSIS:")
        report.append(f"   Valid: {'✅ YES' if script_results['valid'] else '❌ NO'}")
        report.append(f"   Violations: {len(script_results['violations'])}")
        report.append(f"   Warnings: {len(script_results['warnings'])}")
        if script_results['scores']:
            report.append(f"   Overall Score: {script_results['scores'].get('overall', 0):.1f}/100")
        
        # Prompt results
        report.append("\n🎨 PROMPT ANALYSIS:")
        report.append(f"   Valid: {'✅ YES' if prompt_results['valid'] else '❌ NO'}")
        report.append(f"   Flagged Prompts: {len(prompt_results['flagged_prompts'])}")
        report.append(f"   Continuity Issues: {len(prompt_results['continuity_issues'])}")
        
        # Violations detail
        if script_results['violations'] or prompt_results['violations']:
            report.append("\n⚠️  VIOLATIONS:")
            for v in script_results['violations'][:5]:
                report.append(f"   - {v['category']}: '{v['word']}'")
            for v in prompt_results['violations'][:5]:
                report.append(f"   - {v['category']}: '{v['word']}'")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)

def check_content_safety(script: str, prompts: List[Dict]) -> Tuple[bool, Dict]:
    """
    Convenience function for full content safety check.
    
    Args:
        script (str): Script text
        prompts (List[Dict]): List of prompts
    
    Returns:
        Tuple[bool, Dict]: (is_safe, results_dict)
    """
    checker = SafetyChecker()
    
    # Check script
    script_results = checker.check_script(script)
    
    # Check prompts
    prompt_results = checker.check_prompts(prompts)
    
    # Generate report
    report = checker.generate_safety_report(script_results, prompt_results)
    logger.info(report)
    
    # Auto-fix if needed
    if not script_results['valid']:
        script = checker.auto_fix_script(script, script_results['violations'])
    
    if not prompt_results['valid']:
        prompts = checker.auto_fix_prompts(prompts, prompt_results['violations'])
    
    is_safe = script_results['valid'] and prompt_results['valid']
    
    return is_safe, {
        "script": script_results,
        "prompts": prompt_results,
        "fixed_script": script,
        "fixed_prompts": prompts
    }

if __name__ == "__main__":
    # Test safety checker
    test_script = "Chapter 1: The Beginning\nThis is a test script about historical events..."
    test_prompts = [
        {"id": "vid_001", "prompt": "A cinematic scene from the 1970s showing urban architecture"},
        {"id": "vid_002", "prompt": "Documentary style image of city planning meeting"}
    ]
    
    is_safe, results = check_content_safety(test_script, test_prompts)
    print(f"Safe: {is_safe}")
    print(json.dumps(results, indent=2))
