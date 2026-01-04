# src/tts.py
import asyncio
import edge_tts

async def generate_voice_with_edge_tts(text: str, output_path: str):
    """Edge TTS ile ses üretir."""
    communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
    await communicate.save(output_path)
