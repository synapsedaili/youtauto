# src/fast_generator.py
import os
import tempfile
import shutil
from pathlib import Path
import numpy as np
import asyncio
import edge_tts
import multiprocessing
from PIL import Image, ImageDraw, ImageFont

# MoviePy importları
from moviepy.editor import ColorClip, CompositeVideoClip, AudioFileClip, ImageClip, concatenate_videoclips, \
    CompositeAudioClip
import moviepy.audio.fx.all as afx

# YouTube upload için gerekli
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import json
import pickle

# ======================
# SİSTEM VE FPS AYARLARI
# ======================
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

FPS = 24

# Görsel Listeleri - src/image klasöründen
def get_shorts_images():
    """src/image/ klasöründen 1s.jpg, 2s.jpg, ... tarzı görselleri al."""
    image_dir = Path("src/image")
    if image_dir.exists():
        images = []
        for i in range(1, 6):  # 1s.jpg'den 8s.jpg'ye kadar
            img_path = image_dir / f"{i}s.jpg"
            if img_path.exists():
                images.append(str(img_path))
        return images
    return []

def get_podcast_images():
    """src/image/ klasöründen 1.jpg, 2.jpg, ..., 12.jpg tarzı görselleri al."""
    image_dir = Path("src/image")
    if image_dir.exists():
        images = []
        for i in range(1, 13):  # 1.jpg'den 12.jpg'ye kadar
            img_path = image_dir / f"{i}.jpg"
            if img_path.exists():
                images.append(str(img_path))
        return images
    return []

SHORTS_IMAGES = get_shorts_images()
PODCAST_IMAGES = get_podcast_images()

# Varsayılan scriptler
TOPIC = "1970: Biosphere 2 First Funding Secured (USA)"

SHORTS_SCRIPT = """
$200 million for a fake planet! In 1961, it was just a poetic dream. 
But in 1970, the money turned dangerous. 
Texas oil billionaire Ed Bass signed the check. 
He didn't just buy a science project. 
He bought a backup Earth in Arizona. 
A private company owning the air we breathe? 
They called it Space Biospheres Ventures. 
While NASA built tin cans, they built Eden. 
But can you really trap nature in glass? 
Or was the desert already winning? 
Hear the full secret story in our podcast! 
Could you survive two years in a bottle? 
Is Earth our only home, or just the first? 
Like this video if you learned something new! 
Comment your thoughts below and subscribe for more fascinating stories!
""".strip()

PODCAST_SCRIPT = """
Synapse Daily: The $200 Million Gamble (1970)

Chapter 1: The Bridge Across the Decade
"Welcome to Synapse Daily."

In our last story, we explored 1961. We met John Allen, the wandering poet. We saw his sketches of a "second womb." It was a beautiful, radical, and quiet dream. But visions don't build airlocks. Poetry doesn't pay for five hundred tons of steel. To move from a notebook to the desert, Allen needed a miracle. He needed the year 1970.

The world in 1970 was a different beast. The idealism of the sixties was bruising. The Vietnam War was a dark shadow. But the Space Race had left a residue. It left a belief that technology could solve everything. People weren't just looking at the moon anymore. They were looking at the survival of the species.

This is the bridge. 1970 is the year the "Plan B" became a business. It was the moment the "Synergists" stopped being a troupe of dreamers and started being a board of directors. If 1961 was the soul, 1970 was the cold, hard cash. This year represents the largest private investment in ecological history. We are talking about money that could move mountains. And that is exactly what they planned to do.

Chapter 2: The Pitch – When Oil Met Soil (Expanded)
How do you sell a fake planet to a man who already owns the world? This wasn't just a meeting. It was a heist of the imagination. In late 1970, John Allen walked into a room with a burden. He had the maps of a new world, but his pockets were empty. On the other side of the mahogany table sat Ed Bass. He was the crown prince of a Texas oil dynasty. He had billions in the bank but a void in his soul.

The air in the room was thick. You could smell the expensive tobacco and the scent of old money. Allen didn’t start with spreadsheets. He didn't talk about profit margins. He leaned in and whispered about the "End of the World." He told Bass that the Earth was a fading star. He called our planet "Biosphere 1"—a bank account being drained by a greedy civilization.

"What if," Allen asked, "you could own the prototype for the future?"

He used his Harvard MBA precision to slice through Bass’s boredom. He spoke of "Ecological Capital." He described a cathedral of glass in the desert where life would be eternal. Bass was captivated. He wasn't just looking at an investment; he was looking at a survival pod for the elite. This was the ultimate psychological gamble. Allen was a poet playing a businessman. Bass was a billionaire playing a god.

When the pen hit the paper in 1970, the world shifted. It wasn't just a check for millions. It was a contract between the old energy of the earth—oil—and the new dream of life—soil. The "Plan B" now had a bankroll that could rival small nations. This was the moment the dream got teeth. This was the birth of a partnership that would either save humanity or burn $200 million in the Arizona sun.

Chapter 3: Space Biospheres Ventures – The Secret Engine
With the money secured in 1970, the project needed a name. They didn't call it a "Commune." They didn't call it a "Garden." They called it Space Biospheres Ventures (SBV). This was a calculated move.

The 1970s were the dawn of the "Venture Capital" era. By framing the project as a "Venture," Allen and Bass bypassed government red tape. They didn't want NASA’s slow bureaucracy. They didn't want university ethics committees. They wanted speed. They wanted total control.

SBV operated like a modern tech startup. They bought land. They hired engineers. They began to patent their designs. In 1970, they realized that "Life Support" was a commodity. If you could build a system that recycled water and air, you owned the most valuable patent in the universe. This chapter of the story is about the corporate architecture. It’s about the lawyers, the NDAs, and the high-walled secrecy that started long before the glass was ever poured. They weren't just scientists; they were ecological tycoons.

Chapter 4: Choosing the Wasteland – The Oracle Decision
Money was in the bank. The company was formed. Now, they needed a site. It couldn't just be anywhere. It needed to be a place with intense, consistent sunlight. It needed to be a place isolated from the "noise" of the world.

In late 1970, the search led them to Oracle, Arizona. Located at the base of the Santa Catalina Mountains, it was perfect. The air was clear. The elevation was right. But more importantly, it was a "Blank Canvas."

The logistics of 1970 were the real challenge. How do you transport millions of gallons of saltwater to the middle of a desert? How do you bring tropical trees through mountain passes? The 1970 funding wasn't just for the building. It was for the infrastructure. They had to build roads where there were none. They had to negotiate water rights in a state where water is gold.

This was the "Groundbreaking" phase. They were looking at a patch of dirt and seeing a rainforest. They were looking at a desert and seeing an ocean. The local ranchers thought they were crazy. The world didn't yet know their names. But in Oracle, the first surveyors were already marking the lines. The dream of 1961 was finally hitting the Arizona soil.

Chapter 5: The Biological Audit – Sourcing a Planet
With the millions of Ed Bass now sitting in the bank, the "Shopping List" began. But you can't just go to a store and buy an ecosystem. In 1970, the team started what they called the "Biological Audit." This was a massive undertaking.

They needed thousands of species. They needed insects that wouldn't eat the glass seals. They needed plants that would cooperate. They sent teams to the furthest corners of the globe. From the deep Amazon to the marshes of Florida. Every single creature had to be vetted.

This was a logistical nightmare. Imagine 1970s paperwork for importing rare soil microbes. They had to ensure that no "pests" entered. If one wrong species got in, the whole system would fail. The funding allowed for private expeditions. They were like Victorian explorers with modern bank accounts. They weren't just collecting plants; they were collecting the "Operating System" of Earth. Every seed was a line of code. Every animal was a hardware component. The desert of Oracle was about to become the most crowded place on Earth.

Chapter 6: The Technosphere – The Invisible God (Expanded)
Think about the pressure. Not just the social pressure, but the literal, physical weight of the air. Below the lush ferns and the simulated ocean of Biosphere 2 lay a terrifying secret: The Technosphere. This was a 500-ton stainless steel monster. It was a massive, seamless pan designed to separate the "fake" world from the "real" one.

The 1970 funding was poured into this steel belly. Why? Because nature is leaky. The Arizona soil is breathing. It has its own gases, its own moisture, its own rules. To prove the experiment worked, Allen needed total control. Every square inch of that steel was welded by hand. Thousands of miles of seams. One tiny crack, one microscopic hole, and the data was ruined. The dream would bleed into the desert.

But the real horror was the heat. Imagine the Arizona sun beating down on three acres of glass. Inside, the air expands. It pushes against the walls with the force of a thousand hammers. Without a release, the entire glass cathedral would explode into a million shards.

This led to the creation of the "Lungs." These were two gargantuan, circular concrete bunkers. Inside, a 20-ton rubber membrane hung from the ceiling. As the sun rose, the building would "exhale," and these massive rubber plates would rise into the air. At night, as the desert cooled, the building would "inhale," and the lungs would sink. It was a rhythmic, mechanical heartbeat. In 1970, they were spending millions on a machine that lived and breathed. They were playing a dangerous game with thermodynamics. If the lungs failed, the world died. It was that simple. They were living inside a ticking biological clock.

Chapter 7: The Synergist Elite – The Management of Dreams
How did a group of "Theater People" manage a $200 million project? This is the strangest part of the 1970 story. John Allen didn't hire corporate managers. He used his "Synergists."

These were people who had lived together for years. They shared a secret language. They shared a radical vision. To the outside world, they looked like a cult. To Ed Bass, they were a lean, efficient machine. They worked eighteen hours a day. They didn't care about titles. They cared about the "Goal."

But this created a wall of secrecy. They didn't trust mainstream science. They didn't trust the government. This "Us vs. Them" mentality was funded by Bass’s fortune. It allowed them to work in total darkness. No peer reviews. No public oversight. In 1970, this was their greatest strength. Later, it would become their greatest weakness. But for now, the Synergist Elite was the most powerful group in the desert.

Chapter 8: The Mars Blueprint – A Cold War Target
Why 1970? We have to look at the stars. The Apollo program was the pride of America. But NASA was building "Tin Cans." They were building ships to visit the moon, not to live there.

Biosphere 2 was the "Private Sector Space Race." John Allen knew that if you want to go to Mars, you can't take enough oxygen with you. You have to grow it. You have to recycle it. The 1970 funding was a bet on the future of space travel.

They weren't just building a garden; they were building a "Mars Prototype." Every airlock was a test for a future colony. While the Soviets were experimenting with BIOS-3 in Siberia, the Americans were building the "Venture" model. The goal was to sell this technology to the highest bidder. Whether it was NASA or a future space corporation. In 1970, the "Plan B" wasn't just for Earth. It was for the entire solar system. They were the first to treat space survival as a business.

Chapter 9: The Wall of Skepticism – Academic War (Expanded)
As the steel skeletons rose from the Oracle dust, a different kind of storm was brewing. It wasn't made of sand, but of pure, intellectual hatred. The 1970 funding had allowed the Synergists to bypass the gatekeepers of science. And the gatekeepers were furious.

In the ivory towers of Harvard and Yale, professors looked at the news reports and felt a cold rage. To them, John Allen wasn't a scientist. He was a "New Age Prophet." They called Biosphere 2 a "Scientific Circus." They whispered words like "Cult" and "Pseudoscience" in the halls of power.

The war was about philosophy. The establishment believed in "Reductionism"—the idea that you study one leaf, one bug, or one chemical at a time. But Allen and his team were "Holists." They believed you couldn't understand the leaf without the soil, the wind, and the human standing next to it.

"You can't do science with $200 million of private oil money!" the critics screamed.

The media began to hunt for blood. They looked for cracks in the glass and cracks in the team’s sanity. But the 1970 investment gave the Synergists a shield of gold. They didn't need the scientists' approval. They didn't need government grants. This created a dangerous "Us vs. Them" mentality.

The team in the desert retreated further into their glass world. They became more secretive, more defensive. Every criticism from the outside was seen as an attack on the future of humanity. The 1970 funding hadn't just built a laboratory; it had built a fortress. An island of "Theatrical Science" surrounded by an ocean of academic hostility. The tension was no longer just about the oxygen inside. It was about who had the right to define reality itself. The battle lines were drawn in the sand, and neither side was willing to blink.
Chapter 10: The Economic Weight – A $200 Million Gamble
Let’s talk about the number. Two hundred million dollars. In 1970, that wasn't just money. It was a statement. To put it in perspective, NASA's entire budget was being slashed. The Vietnam War was draining the treasury. Yet, in the middle of a desert, a private individual was building a world.

This investment changed the town of Oracle forever. It brought in engineers from all over the globe. It created a local economy based on the impossible. But it also created a heavy burden. When you spend that much money, you cannot afford to fail.

The pressure from Ed Bass was silent but immense. Every dollar had to be accounted for in the "Biological Audit." This led to a culture of perfectionism. They weren't just building a lab. They were building an asset. In 1970, "Ecology" became "Big Business." This was the first time nature was given a price tag on such a massive scale. They were buying air. They were buying water. They were buying the future.

Chapter 11: The Culture of the Glass – A Secret Society
With the 1970 funding came a wall of silence. Because it was private money, there was no "Freedom of Information Act." The Synergists lived by their own rules. They created a culture that was part-monastery, part-startup.

This chapter of the story is about the "Inner Circle." John Allen managed the vision. Ed Bass managed the gold. Together, they created a world that didn't need the outside. This isolation started long before the airlock hissed shut in 1991.

In 1970, they began to filter who could join the mission. You didn't just need a PhD. You needed "The Spirit." You had to believe in the "Plan B" with every fiber of your being. This led to accusations of being a cult. But to them, it was just "Synergy." They were the only ones who truly understood the fragility of Biosphere 1. The money gave them the luxury of ignoring the critics. It gave them the power to create their own reality.

Chapter 12: From Draft to Hardware – The 1970 Shift
This is the bridge to the future. If you look at the 1961 drafts, they were beautiful and flowing. They looked like art. But by the end of 1970, the drawings changed. They became blueprints. They became technical manuals.

The funding allowed for the "Test Module." Before they built the big dome, they built a smaller one. A proof of concept. This was where the real science happened. They learned how to seal a room perfectly. They learned how a single human could survive with just a few plants.

The 1970 investment turned a "Poet's Dream" into "Hardware." They were ordering steel by the ton. They were shipping glass by the thousands. The desert was no longer silent. It was a construction site for a new civilization. This was the moment of no return. The money was spent. The ground was broken. The "Plan B" was no longer a theory; it was a physical structure rising against the Arizona sky.

Chapter 13: The Finale – Why 1970 Still Matters
As we conclude this journey on Synapse Daily, we have to ask: Was 1970 the year we almost saved the world? Or was it the year we realized we couldn't?

The 1970 funding of Biosphere 2 is a mirror for our own time. Today, billionaires are looking at Mars. They are looking at bunkers. They are still trying to buy a "Plan B." But the lesson of 1970 is profound. Even with $200 million, even with the smartest minds and the best steel, nature cannot be fully owned.

Biosphere 2 stands today as a monument to that 1970 ambition. It reminds us that our primary home—Biosphere 1—is irreplaceable. The "First Funding" was an act of hope. It was a brave, crazy, and expensive attempt to understand the miracle of life.

John Allen’s vision and Ed Bass’s checkbook created a legend. They proved that we have the courage to try, even if we don't have all the answers. We are still living in the shadow of that 1970 gamble. Because every breath we take is a reminder that there is no price tag on a planet that breathes.

"Thank you for joining us on Synapse Daily. You are the reason we tell these stories. If you felt the weight of history today, share this mission. Until next time, take care of our only home."
""".strip()


# ======================
# SHORTS İÇİN ÇOKLU GÖRSEL VE KEN BURNS
# ======================
def create_shorts_bg(image_list, total_duration, width, height):
    clips = []
    duration_per_img = 6.0
    elapsed = 0.0

    for i, img_path in enumerate(image_list):
        if elapsed >= total_duration: break

        current_clip_dur = (total_duration - elapsed) if i == len(image_list) - 1 else min(duration_per_img,
                                                                                           total_duration - elapsed)

        if Path(img_path).exists():
            clip = ImageClip(img_path).resize(height=height)
            if clip.w < width: clip = clip.resize(width=width)

            clip = (clip.set_duration(current_clip_dur)
                    .resize(lambda t: 1 + 0.1 * (t / current_clip_dur))
                    .set_position('center'))
            clips.append(clip)
            elapsed += current_clip_dur
        else:
            clips.append(ColorClip((width, height), (50, 50, 50)).set_duration(current_clip_dur))
            elapsed += current_clip_dur

    return concatenate_videoclips(clips).set_duration(total_duration)


# ======================
# PODCAST İÇİN ÇOKLU GÖRSEL FONKSİYONU
# ======================
def create_podcast_bg(image_list, total_duration, width, height):
    clips = []
    # Mevcut olan görselleri filtrele
    valid_images = [img for img in image_list if Path(img).exists()]

    if not valid_images:
        return ColorClip((width, height), (30, 30, 30)).set_duration(total_duration)

    elapsed_time = 0.0
    for i, img_path in enumerate(valid_images):
        if elapsed_time >= total_duration:
            break

        # Eğer son görseldeysek, kalan tüm süreyi ona ver
        if i == len(valid_images) - 1:
            current_duration = total_duration - elapsed_time
        else:
            # Diğer her görsel tam 120 saniye (2 dk) kalsın
            # Ama video süresinden fazlasını almasın
            current_duration = min(100.0, total_duration - elapsed_time)

        if current_duration <= 0:
            break

        clip = ImageClip(img_path).resize(width=width)
        if clip.h < height:
            clip = clip.resize(height=height)

        # Süreyi set ediyoruz ve zoom efektini bu süreye göre ayarlıyoruz
        clip = (clip.set_duration(current_duration)
                .resize(lambda t, dur=current_duration: 1 + 0.05 * (t / dur))
                .set_position('center'))

        clips.append(clip)
        elapsed_time += current_duration

    return concatenate_videoclips(clips).set_duration(total_duration)


# ======================
# METİN RESMİ OLUŞTURUCU
# ======================
def create_text_image(text, width, height, is_shorts):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fontsize = 70 if is_shorts else 50
    try:
        font = ImageFont.truetype("arial.ttf", fontsize)
    except:
        font = ImageFont.load_default()

    if is_shorts:
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test = current_line + " " + word if current_line else word
            if draw.textbbox((0, 0), test, font=font)[2] < width * 0.8:
                current_line = test
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

        full_text = "\n".join(lines)
        bbox = draw.multiline_textbbox((0, 0), full_text, font=font, align="center")
        x = (width - (bbox[2] - bbox[0])) // 2
        y = (height - (bbox[3] - bbox[1])) // 2
        draw.multiline_text((x, y), full_text, font=font, fill="white", stroke_width=4, stroke_fill="black",
                            align="center")
    else:
        lines = []
        words = text.split()
        current_line = ""
        for word in words:
            if draw.textbbox((0, 0), current_line + " " + word, font=font)[2] <= width - 200:
                current_line += (" " + word if current_line else word)
            else:
                lines.append(current_line);
                current_line = word
        lines.append(current_line)
        y_offset = 180
        for line in lines:
            draw.text((180, y_offset), line, font=font, fill="white", stroke_width=2, stroke_fill="black")
            y_offset += fontsize + 15
    return img


# ======================
# YOUTUBE UPLOAD İŞLEMLERİ
# ======================
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    """YouTube API authenticated service döndürür."""
    credentials = None
    
    # token.pickle dosyası varsa yükle
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    
    # credentials geçerli değilse yeniden authenticate et
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        
        # Yeni credentials'ı kaydet
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
    
    return build('youtube', 'v3', credentials=credentials)


def upload_to_youtube(video_path, title, description, privacy_status="private"):
    """YouTube'a video upload eder."""
    youtube = get_authenticated_service()
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['Cold War', 'History', 'Documentary', 'Soviet'],
            'categoryId': '27'  # Education
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=1024*1024, resumable=True)
    
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"📦 Upload progress: {int(status.progress() * 100)}%")
    
    print(f"✅ Video uploaded successfully! Video ID: {response['id']}")
    return response['id']


# ======================
# ANA VİDEO ÜRETİMİ + UPLOAD
# ======================
def create_and_upload_video(script, title, description, is_shorts=True):
    print(f"🎥 {('Shorts' if is_shorts else 'Podcast')} üretimi başladı...")
    
    # Geçici dosya oluştur
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
        temp_path = temp_video.name
    
    temp_dir = Path(tempfile.mkdtemp())
    temp_audio = temp_dir / "audio.mp3"

    asyncio.run(edge_tts.Communicate(script, "en-US-GuyNeural").save(str(temp_audio)))
    voice_audio = AudioFileClip(str(temp_audio))
    duration = voice_audio.duration

    # --- ARKA PLAN SESİ ---
    ambient_path = "data/1.mp3"  # Arka plan sesi
    if os.path.exists(ambient_path):
        try:
            ambient_audio = AudioFileClip(ambient_path)
            ambient_audio = afx.audio_loop(ambient_audio, duration=duration)
            ambient_audio = ambient_audio.volumex(0.15)
            final_audio = CompositeAudioClip([voice_audio, ambient_audio])
            print("✅ Arka plan sesi (data/1.mp3) başarıyla eklendi.")
        except Exception as e:
            print(f"⚠️ Arka plan sesi eklenirken hata: {e}")
            final_audio = voice_audio
    else:
        print("⚠️ data/1.mp3 bulunamadı, sadece konuşma sesi kullanılıyor.")
        final_audio = voice_audio

    width, height = (1080, 1920) if is_shorts else (1920, 1080)

    if is_shorts:
        background = create_shorts_bg(SHORTS_IMAGES, duration, width, height)
    else:
        background = create_podcast_bg(PODCAST_IMAGES, duration, width, height)

    overlay = ColorClip((width, height), (0, 0, 0)).set_duration(duration).set_opacity(0.4)

    words = script.split()
    chunk_size = 4 if is_shorts else 50
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

    text_clips = []
    start_time = 0.0
    speed = (duration / len(words)) * chunk_size

    for chunk in chunks:
        if start_time >= duration: break
        c_dur = min(speed, duration - start_time)
        text_img = create_text_image(chunk, width, height, is_shorts)
        img_p = temp_dir / f"t_{start_time}.png"
        text_img.save(str(img_p))
        text_clips.append(ImageClip(str(img_p)).set_duration(c_dur).set_start(start_time).set_position('center'))
        start_time += c_dur

    final = CompositeVideoClip([background, overlay] + text_clips).set_audio(final_audio).set_duration(duration)

    final.write_videofile(
        temp_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=multiprocessing.cpu_count(),
        preset="ultrafast",
        logger=None
    )
    
    print(f"✅ Video üretildi: {temp_path}")
    
    # YouTube upload
    print("📤 YouTube'a upload ediliyor...")
    video_id = upload_to_youtube(temp_path, title, description, "private")
    
    # Geçici dosyaları temizle
    os.unlink(temp_path)
    shutil.rmtree(temp_dir)
    
    print(f"🎉 {('Shorts' if is_shorts else 'Podcast')} tamamlandı! Video ID: {video_id}")
    return video_id


if __name__ == "__main__":
    print("🚀 Fast Video Generator Başlatılıyor...")
    print(f"📊 Shorts görselleri: {len(SHORTS_IMAGES)} adet")
    print(f"📊 Podcast görselleri: {len(PODCAST_IMAGES)} adet")
    
    # Shorts upload
    create_and_upload_video(
        SHORTS_SCRIPT,
        "Soviet Alfa-Class Submarine Design (1961) - Shorts",
        "1961: Soviet Alfa-Class Submarine Design Initiated - Cold War Mystery",
        is_shorts=True
    )
    
    # Podcast upload
    create_and_upload_video(
        PODCAST_SCRIPT,
        "Soviet Alfa-Class Submarine Design (1961) - Documentary",
        "Detailed documentary about the 1961 Soviet Alfa-Class Submarine Design - Cold War Engineering",
        is_shorts=False
    )
    
    print("🎉 Tüm işlemler tamamlandı!")
