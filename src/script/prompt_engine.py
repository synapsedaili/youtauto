# src/script/prompt_engine.py 
"""
Prompt Engine - UPDATED
=====================

Now supports dynamic prompt count based on audio duration
"""

def generate_prompts_from_script(self, script: str, prompt_count: int) -> List[Dict]:
    """
    Generate visual prompts from script with dynamic count.
    
    Args:
        script (str): Full script text
        prompt_count (int): Number of prompts needed (based on audio duration)
    
    Returns:
        List[Dict]: List of prompt dictionaries
    """
    scenes = self.extract_scenes_from_script(script)
    prompts = self.generate_prompts(scenes, prompt_count)
    
    return prompts
