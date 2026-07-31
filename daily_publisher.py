import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Outfit Ideas That Feel Effortlessly You",
        "Aesthetic Moments to Brighten Your Day",
        "Beauty and Confidence — A Daily Ritual",
        "Elegant Looks for Every Mood",
        "How to Build an Aesthetic Wardrobe",
        "Everyday Beauty Tips You'll Love",
        "The Creative Side of Personal Style",
        "Style Inspiration for Your Week",
        "Self-Expression Through What You Wear",
        "Simple Ways to Elevate Your Everyday",
        "Confidence, Creativity and Class",
        "Your Aesthetic: Own It Fully",
        "Beauty in the Little Details",
        "Fashion for Real Life, Every Day",
        "New Looks, New Stories, Regular Updates",
    ]

    fallback_descriptions = [
        "Your outfit is your introduction — make it speak elegance, confidence, and creativity. Personal style isn't about trends; it's about pieces that feel authentically you. Start with what you love and build from there. Drop a 💫 if you're styling today! #fashion #outfitideas #personalstyle #elegance #confidence #miyoraaikari",
        "Aesthetics are everywhere when you look for them — soft light, curated corners, thoughtful details. We share those everyday moments that feel a little more beautiful. Life is art when you notice it. Save this for a little inspiration. 🌸 #aesthetics #lifestyle #dailyinspiration #beautifulmoments #curatedlife #miyoraaikari",
        "Beauty is a form of self-respect — the skincare, the outfit, the little rituals that make you feel like you. When you show up for yourself, it radiates outward. Start with one small ritual today. Like if you're investing in yourself! 💖 #beauty #selfcare #confidence #rituals #selflove #miyoraaikari",
        "Elegance is the art of making the ordinary feel special. A well-tied scarf, a favorite perfume, a polished pair of shoes — details create the impression. Cultivate grace in your choices. Double tap if you love the details! 🕊️ #elegance #style #details #sophistication #fashion #miyoraaikari",
        "An aesthetic wardrobe is built piece by piece — quality basics, one signature color, and items that spark joy. It's not about volume; it's about intention. Here's how to curate your own. Save this as your style guide! 👗 #capsulewardrobe #aestheticclothes #styleguide #fashiontips #curatedstyle #miyoraaikari",
        "Everyday beauty doesn't require perfection — just consistency. A simple routine, enough sleep, and a little kindness toward yourself go a long way. Glow from the inside out. Comment one beauty habit you swear by! ✨ #beautytips #dailyroutine #skincare #glow #healthyskin #miyoraaikari",
        "Creativity is the soul of personal style. Mixing textures, playing with color, and trying unexpected combinations keeps fashion exciting. There are no mistakes — only discoveries. What's your boldest style choice? Drop it below! 🎨 #creativity #fashion #selfexpression #styleinspo #boldchoices #miyoraaikari",
        "Style should fit your real life — comfy, functional, and beautiful. Whether it's coffee runs or evening plans, dress for the day you actually have. Fashion that works is fashion you'll love. Double tap if you dress for real life! ☕ #everydaystyle #reallifefashion #comfortablechic #outfitideas #lifestyle #miyoraaikari",
        "Confidence is the most attractive quality — and it's cultivated, not born. Dressing well, standing tall, and speaking kindly to yourself all build it. You are worthy of taking up space. Drop a 👑 if you're owning your confidence! #confidence #selfworth #empowerment #selflove #style #miyoraaikari",
        "Beauty lives in the little details — a perfectly matched lip, a favorite ring, the way light hits your hair. Notice them, celebrate them. You are made of beautiful details. Save this for a self-love reminder. 💕 #beautyindetails #selflove #glowup #confidence #lifestyle #miyoraaikari",
        "Self-expression is your superpower. Your clothes, your home, your feed — all of it is a canvas for who you are. Create without apology. The world needs your unique voice. Share this with a creative friend! 🖌️ #selfexpression #creativity #personalstyle #artoflife #uniqueness #miyoraaikari",
        "A fresh look for every season keeps life exciting. As the weather changes, so does the style — lighter fabrics, warmer tones, new combinations. Here's what we're loving right now. What are you wearing this season? Comment below! 🍂 #seasonalstyle #fashionupdate #outfitinspo #trending #styleguide #miyoraaikari",
        "New posts and stories regularly — that's our promise. A little inspiration, a little beauty, a little style, delivered to your feed. Thanks for being part of this aesthetic journey. Double tap to say hi! 👋 #dailycontent #fashionblog #lifestylecreator #beautydiary #community #miyoraaikari",
        "Inspiration is a habit you can build — a look you save, a quote you keep, a color palette that lifts you. Curate what feeds your creativity and watch it transform your style. Save this for your inspiration board! 📌 #inspiration #moodboard #creativity #styleideas #aestheticliving #miyoraaikari",
        "At the end of the day, fashion is about feeling like the best version of you. Wear the outfit that makes you smile, take the photo, live the moment. You deserve to feel beautiful. Good night, and see you in the next post. 🌙 #elegance #confidence #selflove #lifestyle #fashionjourney #miyoraaikari",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "aesthetic and curated — speak like a thoughtful style and beauty creator",
        "elegant and graceful — inspire refined, polished everyday looks",
        "creative and expressive — celebrate self-expression and personal style",
        "warm and encouraging — speak like a friend sharing beauty tips",
        "fresh and inspiring — offer daily doses of beauty and motivation",
        "confident and empowering — help viewers feel beautiful and worthy",
        "gentle and reflective — emphasise beauty in the little details",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Miyora Aikari'. "
        f"The page covers fashion, lifestyle, and beauty - sharing outfits, aesthetics, and everyday moments. It's inspired by elegance, confidence, and creativity, with new posts and stories regularly. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if this inspired you! Comment your favorite look below! Share this with someone who loves aesthetics! Follow Miyora Aikari for daily fashion and beauty inspiration!"
        f"Include relevant hashtags in ALL LOWERCASE such as #fashion #lifestyle #beauty #outfitideas #aesthetics #elegance #confidence #creativity #style #dailyinspiration #selfexpression #beautytips #fashioninspo #miyoraaikari. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["fashion", "lifestyle", "beauty", "outfitideas", "aesthetics", "elegance", "confidence", "creativity", "style", "dailyinspiration", "selfexpression", "beautytips", "fashioninspo", "miyoraaikari"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
