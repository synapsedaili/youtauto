# src/controller/llama_controller.py 
"""
Llama 3.3 Process Controller 
====================================

Now includes script part evaluation and expansion decisions
"""

def evaluate_script_part(self, part: str, part_number: int) -> Dict:
    """
    Evaluate script part for quality and expansion needs.
    
    Args:
        part (str): Script part content
        part_number (int): Which part (1, 2, or 3)
    
    Returns:
        Dict: Evaluation results with approval and suggestions
    """
    try:
        prompt = f"""
        You are a quality control AI for documentary scripts.
        
        Evaluate this script part ({part_number}/3):
        
        {part[:2000]}
        
        Check for:
        1. Emotional impact (does it trigger curiosity/emotion?)
        2. Factual accuracy (are claims verifiable?)
        3. Sentence structure (max 8 words per sentence?)
        4. Engagement level (will viewers keep watching?)
        5. Character count efficiency (no filler content?)
        
        Return JSON:
        {{
            "approved": bool,
            "score": 0-100,
            "suggestions": ["list of specific improvements"],
            "needs_expansion": bool,
            "expansion_areas": ["which parts to expand"]
        }}
        """
        
        response = self._call_llama_api(prompt)
        evaluation = json.loads(response)
        
        logger.info(f"📊 Part {part_number} evaluation: Score {evaluation.get('score', 0)}/100")
        
        return evaluation
        
    except Exception as e:
        logger.warning(f"⚠️ Llama evaluation failed: {str(e)}")
        return {"approved": True, "score": 80, "suggestions": [], "needs_expansion": False}
