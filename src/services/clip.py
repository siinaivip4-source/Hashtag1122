import torch
import threading
import time
from PIL import Image
from io import BytesIO
from transformers import CLIPModel, CLIPProcessor
from typing import Dict, Any

from src.core.logger import get_logger
from src.core.config import config

logger = get_logger(__name__)

STYLES = [
    "2D", "3D", "Cute", "Animeart", "Realism",
    "Aesthetic", "Cool", "Fantasy", "Comic", "Horror",
    "Cyberpunk", "Lofi", "Minimalism", "Digitalart", "Cinematic",
    "Pixelart", "Scifi", "Vangoghart"
]

COLORS = [
    "Black", "White", "Blackandwhite", "Red", "Yellow",
    "Blue", "Green", "Pink", "Orange", "Pastel",
    "Hologram", "Vintage", "Colorful", "Neutral", "Light",
    "Dark", "Warm", "Cold", "Neon", "Gradient",
    "Purple", "Brown", "Grey"
]

TAGS_OBJECT = ["None",
    "sport", "football", "messi", "lamineyamal", "ronaldo", "mbappe", "flamengo", "sepalmeiras", "sccorinthianspaulista", "juventus", "realmadrid", "dortmund", "chelsea", "intermiami", "neymar", "manchesterunited", "manchestercity", "bayernmunich", "barcelona", "liverpool", "sonheungmin", "atleticomadrid", "arsenal", "cricket", "dhoni", "basketball", "phoenixsuns", "milwaukeebucks", "michaeljordan", "stephencurry", "goldenstatewarriors", "superbowl",
    "animal", "lion", "wolf", "leopard", "phoenix", "pet", "dog", "cow", "butterfly", "dragon", "cat", "rabbit", "panda", "bear", "hamster", "fish", "bird", "eagle", "tiger", "unicorn", "duck", "peacock", "capybara", "elephant", "pig", "fox", "monkey", "penguins", "squirrel", "horse", "sheep", "camel",
    "universe", "planet", "astronaut", "galaxy", "spaceship", "aurora",
    "game", "gamepad", "pubg", "minecraft", "mario", "leagueoflegends", "jinx", "valorant", "mortalkombat", "grandtheftauto", "freefire", "callofduty", "genshinimpact", "halo", "hololive", "hollowknight", "mobilelegends", "arenaofvalor", "naraka",
    "film", "dc", "batman", "theflash", "superman", "joker", "marvel", "spiderman", "wolverine", "deadpool", "thanos", "blackpanther", "captainmarvel", "ghostrider", "scarletwitch", "thor", "ironman", "venom", "captainamerica", "hulk", "gameofthrones", "wukong", "it", "pennywise", "frankenstein", "zombie", "ghostface", "fridaythe13th", "jasonvoorhees", "theaddamsfamily", "scream", "michaelmyers", "chucky", "dracula", "oppenheimer", "dune", "beetlejuice", "theironclaw", "gundam", "kpopdemonhunter", "lokahchapter1chandra", "strangerthings", "predator", "nowyouseeme", "theboys", "avatar", "godzilla", "kingkong",
    "cartoon", "theamazingworldofgumball", "gumballwatterson", "darwinwatterson", "familyguy", "petergriffin", "stewiegriffin", "briangriffin", "glennquagmire", "clevelandbrown", "joeswanson", "thesimpsons", "bartsimpson", "natra", "aobing", "disney", "insideout", "coco", "zootopia", "baymax", "spongebob", "peanuts", "bighero6", "tomandjerry", "ben10", "bugsbunny", "stitch", "sonic", "minions", "paddington", "nightmarebeforechristmas", "jackskellington", "howtotrainyourdragon", "kungfupanda", "pocoyo", "metroman", "avatarthelastairbender", "walle", "iceage", "regularshow", "couragethecowardlydog", "adventuretime", "finn", "jake", "marceline", "princessbubblegum", "iceking", "bmo", "gunter", "rickandmorty", "webarebears", "toystory",
    "anime", "dragonball", "goku", "vegeta", "frieza", "gohan", "piccolo", "trunks", "majinbuu", "onepiece", "luffy", "sanji", "chopper", "ace", "zoro", "animeboy", "animegirl", "jujutsukaisen", "yujiitadori", "ryomensukuna", "megumifushiguro", "tojifushiguro", "getosuguru", "satorugojo", "narutoshippuden", "sasuke", "uzumakinaruto", "sharingan", "itachi", "kakashi", "hinata", "jiraiya", "sakura", "garaa", "madara", "crayonshinchan", "shinchan", "sanrio", "hellokitty", "kuromi", "demonslayer", "tanjirokamado", "nezukokamado", "shinobu", "rengoku", "akaza", "zenitsuagatsuma", "inosukehashibira", "dandadan", "kentakakura", "tsubasajinnouchi", "blackclover", "pokemon", "charmande", "pikachu", "cubone", "bulbasaur", "gengar", "squirtle", "psyduck", "sailormoon", "thegodofhighschool", "jinmori", "sakamotodays", "haikyu", "shoyohinata", "tobiokageyama", "swordartonline", "asuna", "alice", "ghibli", "totoro", "spiritedaway", "ponyo", "bluelock", "kurokonobasket", "darlinginthefranxx", "zerotwo", "myheroacademia", "izuku", "himikotoga", "chainsawman", "denji", "slamdunk", "conan", "doraemon", "sololeveling", "sungjinwoo", "bleach", "ichigokurosaki", "toshirohitsugaya", "shihouinyoruichi", "aizensosuke", "ranma", "worldtrigger", "frieren", "spyxfamily", "loidforger", "anyaforger", "yorforger", "rezero", "ram", "rem", "subaru", "attackontitan", "leviackerman", "erenyeager", "oshinoko", "fullmetalalchemist", "mobpsycho100", "overlord", "fate", "saber", "hunterxhunter",
    "humans", "kpop", "bigbang", "bts", "blackpink", "celeb", "taylorswift", "pesopluma", "kingvon", "juicewrld", "travisscott", "warrior", "knight", "samurai", "cowboy", "king", "ninja",
    "nature", "mountain", "beach", "flowers", "sunflower", "peony", "rose", "cherryblossom", "lotus", "waterfall", "ocean", "sky", "disaster", "storm", "landscape", "tree", "leaf", "rain", "moon", "stone", "winter", "snowman", "desert", "summer", "forest",
    "vehicle", "car", "audi", "porsche", "lamborghini", "ferrari", "mclaren", "bmw", "mercedes", "toyota", "ship", "train", "boat", "motorbike", "formula1racing",
    "abstract", "pattern", "geometric", "iphonewallpaper", "firework", "brokenscreen", "smoke",
    "love", "heart", "couple",
    "fnb", "food", "fruit", "drink",
    "religion", "god", "cross", "flag", "vietnam", "brazil", "hindugods", "mexico", "zodiac",
    "holiday", "christmas", "santaclaus", "christmastree", "thanksgiving", "newyear", "valentine", "ramadan", "diwali",
    "quote", "sadquote", "funnyquote", "lovequote", "lifequote", "motivatequote",
    "scenery", "city", "village", "architecture", "home", "wonders", "road",
    "season", "spring", "autumn",
    "meme", "middlefinger", "67",
    "warning", "warningsign", "warningtext",
    "manhua", "tianguancifu",
    "donghua", "xianni",
    "manga", "vagabond",
    "other", "ghost", "sillyface", "glitter", "logo", "emoji", "bt21", "fire", "labubu", "flashlight", "money", "dollars", "yinyang", "doublewallpaper", "crybaby", "twinkletwinkle"
]

TAGS_MOOD = ["Happy", "Sad", "Lonely", "Chill", "Funny", "None"]
TAGS_GENDER = ["Boy", "Girl", "Man", "Woman", "Couple", "None"]

STYLE_PROMPT_MAP = {
    "2D": "flat 2d vector art, simple lines, cartoon illustration, no realistic shading, bold silhouettes, clean outlines, minimalist vector, paper-cut aesthetic, solid color fills",
    "3D": "3d computer graphics, blender render, c4d, unreal engine, volumetric lighting, plastic material, octane render, ray tracing, soft shadows, claymorphism, high-gloss finish",
    "Realism": "real life photography, 4k photo, raw camera image, hyperrealistic skin texture, dslr, shutter speed, aperture f/1.8, natural lighting, intricate pores, lifelike detail",
    "Animeart": "anime style, japanese manga, cel shading, 2d character design, waifu, makoto shinkai vibe, vibrant eyes, expressive lineart, ghibli atmosphere, sharp highlights",
    "Cinematic": "cinematic movie scene, dramatic lighting, film grain, wide shot, movie poster style, anamorphic lens flare, epic composition, color graded, IMAX quality, suspenseful mood",
    "Digitalart": "digital painting, wacom tablet drawing, highly detailed concept art, artstation style, speedpaint, soft brushwork, deviantart trending, fantasy landscape, layered texture",
    "Pixelart": "pixel art, 8-bit, 16-bit, dot matrix, blocky edges, retro game, gameboy aesthetic, dithering, limited palette, sprite sheet, isometric pixel",
    "Vangoghart": "vincent van gogh style, oil painting, thick brush strokes, impressionism, starry night, impasto technique, swirling sky, vivid emotional colors, post-impressionist, canvas texture",
    "Cyberpunk": "cyberpunk city, neon lights, high tech low life, futuristic sci-fi, cyborg, night city rain, synthetic neon, mechanical limbs, flying cars, rainy pavement reflections",
    "Lofi": "lofi hip hop style, chill vibes, retro anime aesthetic, study girl, soft lighting, grainy texture, purple haze, cozy bedroom, nostalgic mood, lo-fi filter",
    "Vintage": "vintage retro style, sepia tone, old photograph, film grain, noise, 1980s, vhs glitch, polaroid frame, faded colors, retro fashion, analog feel",
    "Horror": "horror theme, scary, creepy, dark nightmare, monster, gore, blood, eerie fog, eldritch terror, unsettling shadows, gothic macabre, sinister grin",
    "Minimalism": "minimalism, simple clean lines, minimal art, negative space, simple background, zen-like simplicity, geometric harmony, essential shapes, breathing room, monochromatic",
    "Cute": "cute kawaii, chibi style, adorable character, soft shapes, pastel vibe, sanrio aesthetic, big sparkly eyes, squishy appearance, wholesome mood, tiny limbs",
    "Cool": "cool stylish fashion, streetwear, edgy vibe, magazine cover, posing, urban chic, hypebeast style, confident gaze, high fashion editorial, vogue aesthetic",
    "Aesthetic": "aesthetic artistic composition, beautiful lighting, dreamy atmosphere, tumblr style, ethereal glow, vaporwave elements, soft focus, poetic visuals, curated mood",
    "Fantasy": "fantasy art, magic, dungeons and dragons, medieval armor, sword, wizard, mythical creatures, mystical aura, ancient ruins, epic quest, enchanted forest",
    "Comic": "comic book style, bold outlines, pop art, marvel dc style, halftone dots, action lines, speech bubbles, vibrant ink, ink wash, retro superhero",
    "Scifi": "sci-fi, science fiction, outer space, spaceship, alien, futuristic technology, interstellar travel, high-tech laboratory, planetary rings, mecha design, starlight"
}

COLOR_PROMPT_MAP = {
    "Black": "black clothing, black outfit, black object, black fashion, matte black material, deep obsidian, midnight void, jet black silk, charcoal shadows, ink-washed darkness",
    "White": "white clothing, white outfit, white object, bright white surface, ivory elegance, snow-capped purity, pearl sheen, alabaster texture, bleached linen",
    "Blackandwhite": "black and white photography, monochrome, greyscale image, high contrast noir, silver screen nostalgia, charcoal sketch, dramatic chiaroscuro, ink on parchment",
    "Red": "clearly red colored object, vivid red fabric, bold red paint, pure red rose, firetruck red, red traffic light, solid red flag, red lipstick, cardinal red dominant color, undeniably red, tomato red, pure scarlet red hue",
    "Yellow": "bright yellow clothing, yellow object, sunflower color, golden yellow, canary brilliance, honey gold, lemon zest, amber glow, saffron silk",
    "Blue": "blue clothing, blue sky, blue ocean, blue object, cyan, sapphire depth, cobalt sky, navy professional, azure mist, electric blue spark",
    "Green": "green clothing, green plants, nature, forest, green object, emerald lush, mossy earth, jade stone, lime vibrancy, sage leaves",
    "Pink": "pink clothing, pink flower, magenta, hot pink object, rose petal, blush satin, coral tint, bubblegum pop, dusty mauve",
    "Orange": "orange clothing, orange fruit, sunset color, pumpkin orange, apricot warmth, copper metallic, terracotta clay, tiger lily, marmalade glow",
    "Pastel": "soft pastel colors, pale pink blue yellow, baby colors, mint cream, lavender haze, peach fuzz, macaron palette, misty sky blue",
    "Hologram": "holographic texture, iridescent rainbow reflection, metallic silver rainbow, opalescent shimmer, liquid mercury rainbow, glitch aesthetic, soap bubble film, pearlescent foil",
    "Vintage": "sepia tone, old photograph style, retro brown filter, faded polaroid, grainy film stock, daguerreotype finish, antique parchment, tea-stained edges",
    "Colorful": "rainbow colors, many different vibrant colors, confetti, festival, kaleidoscope burst, psychedelic swirl, mardi gras palette, stained glass, technicolor dream",
    "Neutral": "beige clothing, cream color, skin tone, earth tones, sand color, oatmeal linen, taupe elegance, mushroom grey, sandstone, light khaki",
    "Light": "bright image, high key lighting, sunny day, white background, overexposed ethereal, backlit glow, ethereal morning haze, soft focus brightness, studio ring light",
    "Dark": "low key lighting, night scene, shadows, silhouette, dark room, moody vignette, cinematic shadows, heavy noir atmosphere, dim candlelit, obscured silhouette",
    "Warm": "warm lighting, orange tone, golden hour, cozy atmosphere, candlelight flicker, campfire radiance, sepia sunset, toasted almond, brassy undertones",
    "Cold": "cold lighting, blue tone, winter atmosphere, ice, frosty glaze, steel blue chill, arctic pale, moonlight silver, fluorescent clinical",
    "Neon": "glowing neon signs, cyberpunk lights, laser beam, vaporwave magenta, toxic lime glow, night city pulse, ultraviolet streak, radioactive cyan",
    "Gradient": "smooth color gradient background, blurred transition, ombre transition, dusk to dawn bleed, silk-smooth blending, watercolor wash, horizon blur",
    "Purple": "purple clothing, violet, lavender object, grape color, royal amethyst, plum velvet, orchid bloom, dark violet mystery, lilac breeze",
    "Brown": "brown clothing, wooden texture, chocolate color, soil, mahogany wood, espresso crema, rustic leather, cinnamon spice, weathered bronze",
    "Grey": "grey clothing, concrete wall, silver metal, grey object, ash color, slate stone, gunmetal industrial, misty fog, pewter shine, heathered wool"
}


class ClipService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.loaded_models: Dict[str, Dict[str, Any]] = {}
        self.model_map = {
            "clip-openai": "openai/clip-vit-base-patch32",
            "clip-openclip-laion": "laion/CLIP-ViT-B-32-laion2B-s34B-b79K",
            "clip-openclip-vit-h14": "laion/CLIP-ViT-H-14-laion2B-s32B-b79K",
        }
        self._load_lock = threading.Lock()
        self._inference_locks: Dict[str, threading.Lock] = {}
        self._request_count = 0

    def _get_inference_lock(self, model_key: str) -> threading.Lock:
        if model_key not in self._inference_locks:
            self._inference_locks[model_key] = threading.Lock()
        return self._inference_locks[model_key]

    def load(self, model_key: str = "clip-openai") -> None:
        if model_key in self.loaded_models:
            return
            
        logger.info(f"Thread {threading.get_ident()} waiting to load model '{model_key}'...")
        with self._load_lock:
            if model_key in self.loaded_models:
                return
                
            repo_id = self.model_map.get(model_key, "openai/clip-vit-base-patch32")
            logger.info(f"Loading CLIP model '{model_key}' ({repo_id}) to {self.device}...")
            
            model = CLIPModel.from_pretrained(repo_id).to(self.device)
            processor = CLIPProcessor.from_pretrained(repo_id)
            
            s_prompts = [STYLE_PROMPT_MAP.get(s, f"a {s} style artwork") for s in STYLES]
            c_prompts = [COLOR_PROMPT_MAP.get(c, f"dominant color is {c}") for c in COLORS]
            obj_prompts = [f"#{tag}" for tag in TAGS_OBJECT]
            mood_prompts = [f"feeling {tag.lower()}" for tag in TAGS_MOOD]
            gender_prompts = [f"a photo of a {tag.lower()}" for tag in TAGS_GENDER]
            
            with torch.no_grad():
                s_inputs = processor(text=s_prompts, return_tensors="pt", padding=True).to(self.device)
                c_inputs = processor(text=c_prompts, return_tensors="pt", padding=True).to(self.device)
                obj_inputs = processor(text=obj_prompts, return_tensors="pt", padding=True).to(self.device)
                mood_inputs = processor(text=mood_prompts, return_tensors="pt", padding=True).to(self.device)
                gender_inputs = processor(text=gender_prompts, return_tensors="pt", padding=True).to(self.device)

                s_feat = model.get_text_features(**s_inputs)
                c_feat = model.get_text_features(**c_inputs)
                obj_feat = model.get_text_features(**obj_inputs)
                mood_feat = model.get_text_features(**mood_inputs)
                gender_feat = model.get_text_features(**gender_inputs)

                s_feat /= s_feat.norm(dim=-1, keepdim=True)
                c_feat /= c_feat.norm(dim=-1, keepdim=True)
                obj_feat /= obj_feat.norm(dim=-1, keepdim=True)
                mood_feat /= mood_feat.norm(dim=-1, keepdim=True)
                gender_feat /= gender_feat.norm(dim=-1, keepdim=True)
            
            self.loaded_models[model_key] = {
                "model": model,
                "processor": processor,
                "s_feat": s_feat,
                "c_feat": c_feat,
                "obj_feat": obj_feat,
                "mood_feat": mood_feat,
                "gender_feat": gender_feat
            }
            logger.info(f"CLIP model '{model_key}' ready.")

    def predict(self, image_bytes: bytes, model_key: str = "clip-openai") -> tuple[str, str, list[str]]:
        self._request_count += 1
        rid = self._request_count
        start_time = time.time()
        
        logger.info(f"[REQ-{rid}] Pipeline start for {len(image_bytes)} bytes")
        self.load(model_key)
        
        m_data = self.loaded_models.get(model_key)
        if not m_data:
            raise Exception(f"Model {model_key} failed to load.")

        model = m_data["model"]
        processor = m_data["processor"]
        
        image = Image.open(BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        logger.info(f"[REQ-{rid}] Waiting for model lock...")
        lock_start = time.time()
        lock = self._get_inference_lock(model_key)
        acquired = lock.acquire(timeout=config.lock_timeout)
        if not acquired:
            logger.error(f"[REQ-{rid}] Lock timeout ({config.lock_timeout}s).")
            raise Exception(f"Server Busy: AI model lock timeout")
            
        try:
            wait_time = time.time() - lock_start
            logger.info(f"[REQ-{rid}] Lock acquired (waited {wait_time:.3f}s). Processing...")
            
            with torch.no_grad():
                inputs = processor(images=image, return_tensors="pt").to(self.device)
                img_feat = model.get_image_features(**inputs)
                img_feat /= img_feat.norm(dim=-1, keepdim=True)
                
            s_probs = (100.0 * img_feat @ m_data["s_feat"].T).softmax(dim=-1)
            c_probs = (100.0 * img_feat @ m_data["c_feat"].T).softmax(dim=-1)
            obj_probs = (100.0 * img_feat @ m_data["obj_feat"].T).softmax(dim=-1)
            mood_probs = (100.0 * img_feat @ m_data["mood_feat"].T).softmax(dim=-1)
            gender_probs = (100.0 * img_feat @ m_data["gender_feat"].T).softmax(dim=-1)
            
            s_idx = s_probs.argmax().item()
            mood_idx = mood_probs.argmax().item()
            gender_idx = gender_probs.argmax().item()

            # Lấy top-2 objects có xác suất cao nhất
            obj_scores = obj_probs[0]
            obj_top2 = obj_scores.topk(2).indices.tolist()
            obj1 = TAGS_OBJECT[obj_top2[0]]
            obj2 = TAGS_OBJECT[obj_top2[1]]

            hashtags = [
                obj1,
                obj2,
                TAGS_MOOD[mood_idx],
                TAGS_GENDER[gender_idx]
            ]

            # ── Color: chỉ nhận màu khi model đủ tự tin (vượt threshold)
            # Threshold 0.10 = cần ít nhất 2.3x tự tin hơn chọn ngẫu nhiên (1/23 ≈04.35%)
            COLOR_THRESHOLD = 0.10
            c_vals = c_probs[0]
            c_max_score = c_vals.max().item()
            c_idx = c_vals.argmax().item()
            final_color = COLORS[c_idx] if c_max_score >= COLOR_THRESHOLD else "None"
            logger.info(f"[REQ-{rid}] Color: {COLORS[c_idx]} score={c_max_score:.4f} "
                        f"({'accepted' if c_max_score >= COLOR_THRESHOLD else 'REJECTED -> None'})")

            image.close()
            return STYLES[s_idx], final_color, hashtags
        finally:
            lock.release()
            logger.info(f"[REQ-{rid}] Released lock. Total: {time.time() - start_time:.3f}s")

clip_service = ClipService()
