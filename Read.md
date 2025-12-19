# 🧠 Synapse Daily — Cold War Tech & Lost Futures

> **"Günlük Soğuk Savaş teknolojileri ve unutulmuş ütopik mimariler üzerine AI üretilmiş içerik"**

Bu proje, **1960–1980 yılları arasındaki Soğuk Savaş teknolojileri**, **gerçekleşmemiş şehir projeleri** ve **sibernetik deneyler** hakkında **girişten uzak, derinlemesine** içerik üretir.

---

## 🎥 İçerik Stratejisi

- **Günlük 2 video**: 
  - 📱 **Shorts**: 1 dakikalık, dikkat çekici bilgiler
  - 🎙️ **Podcast**: 15 dakikalık, hikayeli analizler
- **Tema**: 
  - Unbuilt Cities (Arcosanti, Habitat 67)
  - Cold War Tech Oddities (Project Orion, Nükleer Trenler)
  - Cybernetic Utopias (Chile Cybersyn, SSCC)

---

## ⚙️ Teknik Özellikler

- **Tamamen otomatik**: GitHub Actions ile her gün **16:00 TR saati** çalışır
- **Sıfır maliyet**: 
  - Metin üretimi: Hugging Face Inference API (ücretsiz tier)
  - Seslendirme: **Coqui TTS** (offline, ücretsiz)
  - Video: MoviePy + FFmpeg
  - Yükleme: YouTube Data API
- **Depolama**: Geçici dosyalar her pipeline sonrası **otomatik silinir**

---

## 🚀 Kurulum (Yerel Test)

```bash
# 1. Ortamı kur
git clone https://github.com/<kullanıcı>/synapse-daily.git
cd synapse-daily
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. API anahtarlarını ayarla
echo "HF_TOKEN=senin_hf_token" > .env
echo "ELEVENLABS_API_KEY=senin_elevenlabs_key" >> .env  # Opsiyonel

# 4. Shorts üret
python src/create_shorts.py

# 5. Podcast üret
python src/create_podcast.py