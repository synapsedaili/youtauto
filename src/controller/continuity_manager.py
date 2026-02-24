# src/controller/continuity_manager.py
"""
Continuity Manager
================

Ensures visual consistency across all 120 video clips
"""

import json
from pathlib import Path
from typing import Dict, List
from src.utils.config import Config
from src.utils.logging import setup_logging

logger = setup_logging()

class ContinuityManager:
    def __init__(self):
        self.character_registry = {}  # Track all characters
        self.environment_registry = {}  # Track all environments
        self.object_registry = {}  # Track key objects
        self.style_registry = {}  # Track visual style
        
    def register_character(self, scene_num: int, description: str):
        """Register character appearance in a scene."""
        # Extract character features
        features = self._extract_character_features(description)
        
        if features['name'] not in self.character_registry:
            self.character_registry[features['name']] = {
                "first_appearance": scene_num,
                "descriptions": [features],
                "consistency_score": 1.0
            }
        else:
            # Check consistency with previous appearances
            prev_features = self.character_registry[features['name']]['descriptions'][-1]
            consistency = self._calculate_consistency(features, prev_features)
            self.character_registry[features['name']]['descriptions'].append(features)
            self.character_registry[features['name']]['consistency_score'] = consistency
        
        logger.debug(f"👤 Character registered: {features['name']} (Scene {scene_num})")
    
    def register_environment(self, scene_num: int, description: str):
        """Register environment in a scene."""
        features = self._extract_environment_features(description)
        
        if features['location'] not in self.environment_registry:
            self.environment_registry[features['location']] = {
                "first_appearance": scene_num,
                "descriptions": [features],
                "consistency_score": 1.0
            }
        else:
            prev_features = self.environment_registry[features['location']]['descriptions'][-1]
            consistency = self._calculate_consistency(features, prev_features)
            self.environment_registry[features['location']]['descriptions'].append(features)
            self.environment_registry[features['location']]['consistency_score'] = consistency
        
        logger.debug(f"🌍 Environment registered: {features['location']} (Scene {scene_num})")
    
    def generate_continuity_prompt(self, scene_num: int, base_prompt: str) -> str:
        """Add continuity constraints to prompt."""
        continuity_context = []
        
        # Add character consistency
        for char_name, char_data in self.character_registry.items():
            if char_data['descriptions']:
                latest_desc = char_data['descriptions'][-1]
                continuity_context.append(f"Character '{char_name}': {latest_desc['full_description']}")
        
        # Add environment consistency
        for loc_name, loc_data in self.environment_registry.items():
            if loc_data['descriptions']:
                latest_desc = loc_data['descriptions'][-1]
                continuity_context.append(f"Location '{loc_name}': {latest_desc['full_description']}")
        
        # Add style consistency
        if self.style_registry:
            style_desc = ", ".join(self.style_registry.get('keywords', []))
            continuity_context.append(f"Visual style: {style_desc}")
        
        # Append continuity context to prompt
        if continuity_context:
            enhanced_prompt = f"{base_prompt}\n\nCONTINUITY REQUIREMENTS:\n" + "\n".join(continuity_context)
        else:
            enhanced_prompt = base_prompt
        
        return enhanced_prompt
    
    def get_continuity_report(self) -> dict:
        """Generate full continuity report."""
        report = {
            "characters": {},
            "environments": {},
            "overall_consistency": 0.0
        }
        
        # Calculate character consistency
        for char_name, char_data in self.character_registry.items():
            report["characters"][char_name] = {
                "appearances": len(char_data['descriptions']),
                "consistency_score": char_data['consistency_score'],
                "first_scene": char_data['first_appearance']
            }
        
        # Calculate environment consistency
        for loc_name, loc_data in self.environment_registry.items():
            report["environments"][loc_name] = {
                "appearances": len(loc_data['descriptions']),
                "consistency_score": loc_data['consistency_score'],
                "first_scene": loc_data['first_appearance']
            }
        
        # Calculate overall consistency
        all_scores = [c['consistency_score'] for c in self.character_registry.values()]
        all_scores += [e['consistency_score'] for e in self.environment_registry.values()]
        report["overall_consistency"] = sum(all_scores) / len(all_scores) if all_scores else 1.0
        
        return report
    
    def _extract_character_features(self, description: str) -> dict:
        """Extract character features from description."""
        # Simplified extraction (use Llama for production)
        return {
            "name": "character_1",
            "age": "adult",
            "gender": "unspecified",
            "clothing": "period-appropriate",
            "full_description": description
        }
    
    def _extract_environment_features(self, description: str) -> dict:
        """Extract environment features from description."""
        return {
            "location": "generic",
            "time_period": "1970s",
            "lighting": "natural",
            "full_description": description
        }
    
    def _calculate_consistency(self, new_features: dict, prev_features: dict) -> float:
        """Calculate consistency score between two feature sets."""
        # Simplified consistency check
        score = 1.0
        
        # Check for major differences
        if new_features.get('age') != prev_features.get('age'):
            score -= 0.3
        if new_features.get('time_period') != prev_features.get('time_period'):
            score -= 0.3
        
        return max(0.0, score)

def main():
    """Test Continuity Manager."""
    manager = ContinuityManager()
    manager.register_character(1, "A man in 1970s suit")
    manager.register_character(10, "The same man in 1970s suit")
    report = manager.get_continuity_report()
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
