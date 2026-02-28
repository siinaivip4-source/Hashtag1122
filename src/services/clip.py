import torch
from PIL import Image
from io import BytesIO
from transformers import CLIPModel, CLIPProcessor

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

HASHTAGS = [
    "photography", "photo", "portrait", "landscape", "camera",
    "lifestyle", "daily", "vibes", "mood", "instagood",
    "fashion", "style", "ootd", "model", "beauty",
    "art", "digitalart", "illustration", "drawing", "creative",
    "travel", "adventure", "explore", "nature", "outdoor",
    "food", "foodie", "yummy", "delicious", "instafood",
    "instadaily", "picoftheday", "instagram", "love", "happy",
    "cute", "beautiful", "summer", "winter", "spring", "autumn",
    "street", "urban", "city", "night", "sunset", "sunrise",
    "minimal", "retro", "vintage", "modern"
]

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
    "Red": "bright red clothing, red car, red flower, crimson object, strong red color, ruby radiance, scarlet velvet, burning ember, cherry blossom red, blood orange intensity",
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
        self.device = "cpu"
        self.model = None
        self.processor = None
        self.s_feat = None
        self.c_feat = None
        self.h_feat = None
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        
        print("Loading CLIP model via transformers...")
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        s_prompts = []
        for s in STYLES:
            if s in STYLE_PROMPT_MAP:
                txt = STYLE_PROMPT_MAP[s]
            else:
                txt = f"a {s} style artwork"
            s_prompts.append(txt)

        c_prompts = []
        for c in COLORS:
            if c in COLOR_PROMPT_MAP:
                txt = COLOR_PROMPT_MAP[c]
            else:
                txt = f"dominant color is {c}"
            c_prompts.append(txt)
        
        h_prompts = [f"#{tag}" for tag in HASHTAGS]
        
        with torch.no_grad():
            s_inputs = self.processor(text=s_prompts, return_tensors="pt", padding=True).to(self.device)
            c_inputs = self.processor(text=c_prompts, return_tensors="pt", padding=True).to(self.device)
            h_inputs = self.processor(text=h_prompts, return_tensors="pt", padding=True).to(self.device)
            self.s_feat = self.model.get_text_features(**s_inputs)
            self.c_feat = self.model.get_text_features(**c_inputs)
            self.h_feat = self.model.get_text_features(**h_inputs)
            self.s_feat /= self.s_feat.norm(dim=-1, keepdim=True)
            self.c_feat /= self.c_feat.norm(dim=-1, keepdim=True)
            self.h_feat /= self.h_feat.norm(dim=-1, keepdim=True)
        
        self._loaded = True
        print("CLIP model loaded successfully")

    def predict(self, image_bytes: bytes, num_tags: int = 5) -> tuple[str, str, list[str]]:
        self.load()
        
        image = Image.open(BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        with torch.no_grad():
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            img_feat = self.model.get_image_features(**inputs)
            img_feat /= img_feat.norm(dim=-1, keepdim=True)
            
        s_probs = (100.0 * img_feat @ self.s_feat.T).softmax(dim=-1)
        c_probs = (100.0 * img_feat @ self.c_feat.T).softmax(dim=-1)
        h_probs = (100.0 * img_feat @ self.h_feat.T).softmax(dim=-1)
        
        s_idx = s_probs.argmax().item()
        c_idx = c_probs.argmax().item()
        
        top_h_indices = h_probs.topk(num_tags).indices
        # topk returns shape (1, k) for a single image; convert to a flat Python list
        if top_h_indices.dim() > 1:
            top_h_indices = top_h_indices[0]
        top_h_indices = top_h_indices.tolist()
        hashtags = [f"#{HASHTAGS[i]}" for i in top_h_indices]
        
        image.close()
        
        return STYLES[s_idx], COLORS[c_idx], hashtags


clip_service = ClipService()
