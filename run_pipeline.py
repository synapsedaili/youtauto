# run_pipeline.py
"""
Synapse Daily Pipeline Runner
=============================

Bu dosya geçici olarak duraklatılmıştır.
Sadece src/fast_generator.py çalışsın diye.
"""

def run_shorts_pipeline():
    """Geçici olarak duraklatıldı."""
    print("⏸️ Shorts pipeline geçici olarak duraklatıldı.")
    print("🎬 Sadece fast_generator.py çalışsın diye.")

def run_podcast_pipeline():
    """Geçici olarak duraklatıldı."""
    print("⏸️ Podcast pipeline geçici olarak duraklatıldı.")
    print("🎬 Sadece fast_generator.py çalışsın diye.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and "--mode" in sys.argv:
        mode = sys.argv[sys.argv.index("--mode") + 1]
        if mode == "shorts":
            run_shorts_pipeline()
        elif mode == "podcast":
            run_podcast_pipeline()
    else:
        print("⏸️ run_pipeline.py geçici olarak duraklatıldı.")
        print("🎬 Sadece src/fast_generator.py çalışsın diye.")
        print("🔧 Test yapmak için: python src/fast_generator.py")
