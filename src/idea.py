# idea.py
import os

IDEA_FILE = r"C:\Users\gktg9\PycharmProjects\ouTube\idea.txt"
SIDEA_FILE = r"C:\Users\gktg9\PycharmProjects\ouTube\sidea.txt"

def load_ideas():
    if not os.path.exists(IDEA_FILE):
        raise FileNotFoundError(f"idea.txt bulunamadı: {IDEA_FILE}")
    with open(IDEA_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def get_next_idea():
    ideas = load_ideas()
    if not ideas:
        return "Boş fikir listesi", 0

    total = len(ideas)
    # Son indeksi oku
    current_index = 0
    if os.path.exists(SIDEA_FILE):
        try:
            with open(SIDEA_FILE, "r") as f:
                idx = int(f.read().strip()) - 1
                current_index = idx % total
        except:
            current_index = 0

    selected_idea = ideas[current_index]
    next_index = (current_index + 1) % total

    # Bir sonrakini kaydet
    with open(SIDEA_FILE, "w") as f:
        f.write(str(next_index + 1))

    return selected_idea, next_index