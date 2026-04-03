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

# ==========================================
# 1. DICTIONARY DỮ LIỆU ĐỊNH NGHĨA PROMPT
# ==========================================

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

SUBJECT_PROMPT_MAP = {
    "sport": "dynamic sports action, athletic movement, sweat, intense competition, stadium lighting, motion blur, energetic atmosphere",
    "football": "soccer match, green football pitch, players in uniform, stadium crowd, kicking the ball, action shot, sports photography",
    "messi": "Lionel Messi, Argentina football legend, number 10 jersey, dribbling the ball, intense focus, realistic portrait, dynamic pose",
    "lamineyamal": "Lamine Yamal, young football prodigy, FC Barcelona jersey, agile movement, rising star, dynamic sports portrait",
    "ronaldo": "Cristiano Ronaldo, CR7, Portuguese football icon, iconic Siuuu celebration, athletic physique, intense determination, hyper-realistic",
    "mbappe": "Kylian Mbappe, French football star, explosive speed, sprinting with the ball, realistic sports photography, dynamic action",
    "flamengo": "Clube de Regatas do Flamengo, red and black jersey, Maracana stadium, passionate Brazilian football fans, team logo",
    "sepalmeiras": "SE Palmeiras, green and white jersey, Brazilian football club, Allianz Parque, passionate supporters",
    "sccorinthianspaulista": "SC Corinthians Paulista, black and white kit, Brazilian football, Neo Quimica Arena, faithful crowd",
    "juventus": "Juventus FC, black and white striped jersey, Italian football, Serie A, Allianz Stadium, professional sports portrait",
    "realmadrid": "Real Madrid CF, iconic white kit, Santiago Bernabeu stadium, Los Blancos, royal football club, champions league atmosphere",
    "dortmund": "Borussia Dortmund, yellow and black jersey, Signal Iduna Park, the Yellow Wall, passionate German fans",
    "chelsea": "Chelsea FC, royal blue jersey, Stamford Bridge stadium, Premier League action, pride of London",
    "intermiami": "Inter Miami CF, pink and black jersey, MLS soccer, South Florida vibe, flamingo pink aesthetics",
    "neymar": "Neymar Jr, Brazilian football star, flashy skills, joyful expression, dribbling, dynamic sports action, detailed portrait",
    "manchesterunited": "Manchester United, red devils, red jersey, Old Trafford stadium, premier league, historic football club",
    "manchestercity": "Manchester City, sky blue jersey, Etihad stadium, modern football, dynamic team play, premier league champions",
    "bayernmunich": "FC Bayern Munich, red and white kit, Allianz Arena, German football powerhouse, Mia San Mia",
    "barcelona": "FC Barcelona, blaugrana jersey, Camp Nou, tiki-taka style, Spanish football, passionate culers",
    "liverpool": "Liverpool FC, iconic red jersey, Anfield stadium, You'll Never Walk Alone banner, intense premier league match",
    "sonheungmin": "Son Heung-min, South Korean football star, Tottenham Hotspur, camera celebration, dynamic forward, realistic portrait",
    "atleticomadrid": "Atletico de Madrid, red and white striped jersey, Metropolitano stadium, intense defensive football, Spanish La Liga",
    "arsenal": "Arsenal FC, red and white jersey, Emirates stadium, the Gunners, premier league, cannon logo",
    "cricket": "cricket match, batsman hitting the ball, cricket pitch, stadium crowd, test match whites or T20 colors",
    "dhoni": "MS Dhoni, Indian cricket legend, wicketkeeper batsman, number 7, finishing shot, helicopter shot, detailed sports portrait",
    "basketball": "basketball game, slam dunk action, hardwood court, players jumping, hoop, NBA style, dynamic lighting",
    "phoenixsuns": "Phoenix Suns, purple and orange jersey, NBA basketball, Footprint Center, fiery sun logo aesthetic",
    "milwaukeebucks": "Milwaukee Bucks, green and cream jersey, NBA, Fiserv Forum, deer logo, basketball action",
    "michaeljordan": "Michael Jordan, Chicago Bulls number 23, iconic jumpman pose, basketball legend, slam dunk, flying through air",
    "stephencurry": "Stephen Curry, Golden State Warriors, number 30, shooting a three-pointer, splash brother, realistic NBA portrait",
    "goldenstatewarriors": "Golden State Warriors, blue and yellow jersey, NBA, Chase Center, fast-paced basketball play",
    "superbowl": "Super Bowl championship game, American football, massive stadium, halftime show fireworks, Lombardi trophy, NFL",
    "animal": "wild animal, wildlife photography, natural habitat, highly detailed, national geographic style",
    "lion": "majestic male lion, golden mane, roaring, African savanna, wildlife photography, regal posture",
    "wolf": "wild gray wolf, howling at the moon, snowy forest night, piercing glowing eyes, mysterious atmosphere",
    "leopard": "spotted leopard, resting on a tree branch, African jungle, stealthy predator, detailed fur texture",
    "phoenix": "mythical phoenix bird, rising from ashes, glowing fire feathers, majestic wingspan, fantasy creature, magical flames",
    "pet": "cute domestic pet, cozy home environment, fluffy fur, adorable expression, wholesome vibe",
    "dog": "cute dog, happy golden retriever, playful pup, wagging tail, outdoors in a park, detailed fur",
    "cow": "dairy cow, black and white patches, eating grass, sunny green pasture, peaceful farm life",
    "butterfly": "vibrant butterfly, macro photography, resting on a blooming flower, delicate wings, beautiful colorful patterns",
    "dragon": "epic fantasy dragon, breathing fire, scaled armor, massive leathery wings, flying over mountains, mythical beast",
    "cat": "adorable fluffy cat, big curious eyes, resting in sunlight, soft whiskers, cute feline, detailed fur",
    "rabbit": "cute white bunny rabbit, long ears, eating a carrot, soft fluffy fur, spring garden",
    "panda": "giant panda, eating bamboo, black and white fur, cute and chubby, bamboo forest background",
    "bear": "wild grizzly bear, catching fish in a river, brown fur, forest wilderness, powerful predator",
    "hamster": "tiny cute hamster, chubby cheeks, holding a seed, soft golden fur, adorable pet",
    "fish": "colorful tropical fish, swimming in a coral reef, underwater photography, clear blue water, glowing scales",
    "bird": "beautiful wild bird, perched on a branch, colorful plumage, nature photography, crisp details",
    "eagle": "bald eagle, soaring through the sky, sharp talons, majestic wingspan, symbol of freedom, realistic bird of prey",
    "tiger": "bengal tiger, fierce gaze, orange and black stripes, walking through jungle foliage, wildlife masterpiece",
    "unicorn": "magical white unicorn, glowing horn, flowing sparkling mane, enchanted forest background, fantasy art",
    "duck": "cute yellow duckling, swimming in a clear pond, water ripples, sunny day, fluffy feathers",
    "peacock": "majestic peacock, displaying colorful tail feathers, iridescent green and blue, elegant bird, intricate patterns",
    "capybara": "chill capybara, relaxing by the water, peaceful expression, yuzu bath, cute giant rodent",
    "elephant": "massive African elephant, long tusks, dusty savanna background, wrinkled skin texture, gentle giant",
    "pig": "cute little pink piglet, smiling, farm mud puddle, adorable snout, wholesome farm animal",
    "fox": "red fox, bushy tail, clever eyes, standing in an autumn forest, orange fur contrasting with green leaves",
    "monkey": "playful monkey, swinging on vines, tropical jungle, expressive face, wildlife nature",
    "penguins": "emperor penguin family, icy antarctic landscape, snow and glaciers, cute waddling birds",
    "squirrel": "cute fluffy squirrel, holding an acorn, sitting on a tree branch, bushy tail, autumn leaves",
    "horse": "majestic wild horse, galloping in a dusty field, muscular build, flowing mane, sunset lighting",
    "sheep": "fluffy white sheep, grazing in a green meadow, peaceful farm, thick wool",
    "camel": "desert camel, walking on sand dunes, Sahara desert, hot sun, caravan journey",
    "universe": "vast universe, glowing galaxies, infinite stars, cosmic dust, deep space exploration, awe-inspiring",
    "planet": "exoplanet in deep space, glowing atmosphere, planetary rings, orbiting a distant star, sci-fi landscape",
    "astronaut": "astronaut in a high-tech spacesuit, floating in zero gravity, Earth in the background, helmet reflection",
    "galaxy": "spiral galaxy, vibrant cosmic colors, purple and blue nebulae, millions of shining stars, Hubble telescope style",
    "spaceship": "futuristic spaceship, cruising through the cosmos, glowing thrusters, sci-fi metallic design, warp speed",
    "aurora": "aurora borealis, northern lights, glowing green and purple sky, snowy mountain landscape, magical night",
    "game": "epic video game scene, gaming setup, glowing RGB lights, immersive digital world, action-packed",
    "gamepad": "modern video game controller, glowing buttons, resting on a gamer desk, neon background, macro shot",
    "pubg": "PUBG battle royale, character with level 3 helmet, holding an assault rifle, Erangel map landscape, survival",
    "minecraft": "Minecraft blocky world, voxel art, diamond pickaxe, creeper, lush green biomes, survival crafting",
    "mario": "Super Mario, jumping over pipes, mushroom kingdom, colorful nintendo style, gold coins, retro gaming",
    "leagueoflegends": "League of Legends champion, summoner's rift, epic fantasy battle, MOBA gameplay, glowing magic",
    "jinx": "Jinx from Arcane, blue braids, chaotic energy, holding her minigun, neon Zaun background, crazy smile",
    "valorant": "Valorant agent, tactical shooter, stylish character design, holding a futuristic glowing weapon, dynamic pose",
    "mortalkombat": "Mortal Kombat fighter, Scorpion or Sub-Zero, flawless victory, dramatic lighting, martial arts, realistic game render",
    "grandtheftauto": "GTA style artwork, urban city landscape, luxury sports car, sunset in Los Santos, cinematic crime game",
    "freefire": "Free Fire battle royale character, stylish tactical outfit, holding a weapon, intense survival action",
    "callofduty": "Call of Duty soldier, modern warfare, tactical gear, warzone battlefield, realistic FPS perspective",
    "genshinimpact": "Genshin Impact character, anime aesthetic, Teyvat landscape, elemental magic glowing, highly detailed gacha art",
    "halo": "Master Chief from Halo, Spartan green armor, energy sword, sci-fi ringworld background, epic gaming moment",
    "hololive": "Hololive VTuber character, anime girl, colorful design, streaming setup, expressive face, cute idol",
    "hollowknight": "Hollow Knight, wandering bug knight, nail weapon, dark gloomy Hallownest, beautifully atmospheric indie game",
    "mobilelegends": "Mobile Legends Bang Bang champion, Land of Dawn, fantasy MOBA hero, dynamic skill effect",
    "arenaofvalor": "Arena of Valor hero, epic fantasy armor, magical battlegrounds, intense MOBA teamfight",
    "naraka": "Naraka Bladepoint, wuxia style warrior, grappling hook, ancient Asian architecture, martial arts battle",
    "film": "cinematic movie poster, blockbuster film scene, dramatic lighting, 8k resolution, IMAX quality",
    "dc": "DC Comics universe, dark and gritty aesthetic, Gotham or Metropolis, legendary superheroes, epic lighting",
    "batman": "Batman, dark knight, Gotham city gargoyle, bat suit, raining night, glowing white eyes, brooding atmosphere",
    "theflash": "The Flash, red suit, running at light speed, yellow lightning trails, slow motion environment, DC hero",
    "superman": "Superman, Man of Steel, red cape flowing, flying over Metropolis, sunlight beaming, symbol of hope",
    "joker": "The Joker, chaotic villain, green hair, purple suit, crazy manic smile, dark gritty Gotham alleyway",
    "marvel": "Marvel Cinematic Universe, Avengers, superhero team-up, explosive action scene, comic book style",
    "spiderman": "Spider-Man, swinging through New York City skyscrapers, red and blue suit, dynamic web-shooting pose",
    "wolverine": "Wolverine, Logan, adamantium claws extended, angry expression, yellow and blue X-Men suit, battle damage",
    "deadpool": "Deadpool, merc with a mouth, red and black suit, holding katanas, breaking the fourth wall, action pose",
    "thanos": "Thanos the mad titan, Infinity Gauntlet with glowing stones, massive imposing figure, epic cosmic villain",
    "blackpanther": "Black Panther, T'Challa, vibranium suit, Wakanda forever pose, sleek black armor, glowing purple energy",
    "captainmarvel": "Captain Marvel, binary form, glowing cosmic aura, flying through space, powerful superheroine",
    "ghostrider": "Ghost Rider, flaming skull, leather jacket, riding a burning hellfire motorcycle, dark supernatural hero",
    "scarletwitch": "Scarlet Witch, Wanda Maximoff, glowing red chaos magic, floating, darkhold aura, powerful witch",
    "thor": "Thor God of Thunder, holding Mjolnir, lightning striking down, Asgardian armor, epic thunder storm",
    "ironman": "Iron Man, Tony Stark, glowing arc reactor, red and gold high-tech armor, flying with repulsor blasts",
    "venom": "Venom symbiote, massive muscular figure, long tongue, sharp teeth, black gooey texture, terrifying anti-hero",
    "captainamerica": "Captain America, Steve Rogers, holding vibranium shield, star-spangled uniform, heroic leadership pose",
    "hulk": "The Incredible Hulk, massive angry green giant, smashing ground, ripped purple pants, unstoppable rage",
    "gameofthrones": "Game of Thrones aesthetic, Westeros, iron throne, dragons flying, medieval fantasy politics, winter is coming",
    "wukong": "Sun Wukong, the Monkey King, holding Ruyi Jingu Bang, traditional Chinese armor, standing on a cloud, Black Myth style",
    "it": "IT movie, scary red balloon, rainy sewer grate, Derry town, creepy horror atmosphere",
    "pennywise": "Pennywise the dancing clown, terrifying smile, glowing eyes, holding a red balloon, horror villain",
    "frankenstein": "Frankenstein's monster, green skin, stitches, neck bolts, gothic horror laboratory, lightning strike",
    "zombie": "undead zombie, decaying flesh, glowing eyes, post-apocalyptic ruined city, walking dead, horror survival",
    "ghostface": "Ghostface killer from Scream, iconic white mask, black hooded robe, holding a hunting knife, slasher horror",
    "fridaythe13th": "Friday movement, Camp Crystal Lake, dark foggy woods, horror slasher vibe",
    "jasonvoorhees": "Jason Voorhees, worn hockey mask, holding a machete, standing in the dark woods, slasher icon",
    "theaddamsfamily": "The Addams Family, gothic spooky house, Wednesday Addams, dark comedy aesthetic, creepy and kooky",
    "scream": "Scream movie aesthetic, suspenseful horror, scary phone call, 90s slasher film vibe",
    "michaelmyers": "Michael Myers, Halloween slasher, pale expressionless mask, dark coveralls, holding a knife, silent stalker",
    "chucky": "Chucky the killer doll, Good Guys overalls, stitched face, holding a knife, creepy horror toy",
    "dracula": "Count Dracula, classic vampire, long black cape with red lining, sharp fangs, gothic transylvanian castle",
    "oppenheimer": "Oppenheimer movie, atomic bomb explosion in the reflection of glasses, 1940s vintage cinematic style, intense portrait",
    "dune": "Dune movie, Arrakis desert landscape, giant sandworm, Paul Atreides, spice melange, sci-fi epic",
    "beetlejuice": "Beetlejuice, black and white striped suit, messy green hair, Tim Burton gothic comedy style, creepy fun",
    "theironclaw": "The Iron Claw, Von Erich family wrestling, 1980s vintage sports aesthetics, emotional wrestling drama",
    "gundam": "Mobile Suit Gundam, giant mecha robot, space battle, laser sword, high-tech Japanese sci-fi",
    "kpopdemonhunter": "K-pop idol looking like a demon hunter, stylish tech-wear, holding magical weapons, dark urban fantasy",
    "lokahchapter1chandra": "epic fantasy adventure, Chandra character, mystical powers, detailed lore-rich environment",
    "strangerthings": "Stranger Things aesthetic, 1980s retro, the Upside Down, glowing red lightning, Demogorgon, kids on bikes",
    "predator": "The Predator, alien hunter, dreadlocks, biomask, shoulder cannon, invisible cloaking effect, deep jungle",
    "nowyouseeme": "Now You See Me, illusionist magic show, glowing playing cards, mysterious magicians, stage lighting",
    "theboys": "The Boys, dark superhero satire, Homelander with glowing red eyes, gritty realistic comic book style",
    "avatar": "Avatar Pandora landscape, glowing bioluminescent forest, Na'vi character, floating mountains, visually stunning 3D CGI",
    "godzilla": "Godzilla, King of the Monsters, atomic breath glowing blue, massive kaiju destroying a neon city",
    "kingkong": "King Kong, giant angry gorilla, beating his chest, standing on top of a skyscraper, monster verse",
    "cartoon": "classic 2D cartoon style, vibrant colors, expressive characters, nostalgic animation",
    "theamazingworldofgumball": "The Amazing World of Gumball, mixed media animation, bright colorful weird world",
    "gumballwatterson": "Gumball Watterson, blue cat cartoon character, wearing a sweater, funny expression",
    "darwinwatterson": "Darwin Watterson, orange walking goldfish, wearing green shoes, happy cartoon",
    "familyguy": "Family Guy cartoon style, Quahog town, 2d animated sitcom setup",
    "petergriffin": "Peter Griffin, white shirt green pants, laughing, cartoon dad",
    "stewiegriffin": "Stewie Griffin, baby in yellow and red, holding a ray gun, evil genius",
    "briangriffin": "Brian Griffin, white talking dog, holding a martini glass",
    "glennquagmire": "Glenn Quagmire, wearing hawaiian shirt, giggity expression",
    "clevelandbrown": "Cleveland Brown, calm expression, yellow shirt, cartoon character",
    "joeswanson": "Joe Swanson, cartoon cop in a wheelchair, intense angry face",
    "thesimpsons": "The Simpsons style, yellow skin characters, Springfield, classic 2D animation",
    "bartsimpson": "Bart Simpson, spiky hair, riding a skateboard, eating a squishee, mischievous",
    "natra": "Nezha (Na Tra), Chinese mythology cartoon, holding fire-tipped spear, wind fire wheels, fierce child deity",
    "aobing": "Ao Bing, Chinese dragon prince, elegant blue and white robes, ice magic, beautiful donghua style",
    "disney": "Disney 3D animation style, Pixar quality, magical, highly expressive characters, beautiful lighting",
    "insideout": "Inside Out characters, glowing emotions in the mind headquarters, colorful Pixar 3D art",
    "coco": "Coco movie, Disney Pixar, colorful Dia de los Muertos, glowing marigold bridge, skeleton musician",
    "zootopia": "Zootopia, modern city populated by animals, Judy Hopps and Nick Wilde, Disney 3D style",
    "baymax": "Baymax, big white inflatable robot, cute and huggable, Big Hero 6, tech lab background",
    "spongebob": "SpongeBob SquarePants, underwater pineapple house, Bikini Bottom, yellow sponge cartoon",
    "peanuts": "Peanuts cartoon, Snoopy and Charlie Brown, simple comic strip art style, classic nostalgia",
    "bighero6": "Big Hero 6, San Fransokyo city, neon lights, high-tech superhero team, Disney animation",
    "tomandjerry": "Tom and Jerry, classic cat and mouse chase, slapstick comedy, retro animation style",
    "ben10": "Ben 10, wearing the Omnitrix, green glowing alien tech, transforming, cartoon network action",
    "bugsbunny": "Bugs Bunny, eating a carrot, Looney Tunes style, what's up doc, classic cartoon rabbit",
    "stitch": "Stitch from Lilo & Stitch, blue alien, cute but destructive, Hawaiian beach background",
    "sonic": "Sonic the Hedgehog, running super fast, blue blur, collecting gold rings, SEGA mascot",
    "minions": "Minions, yellow pill-shaped creatures, wearing goggles and denim overalls, laughing, Pixar style",
    "paddington": "Paddington Bear, wearing a red hat and blue duffle coat, eating a marmalade sandwich, London background",
    "nightmarebeforechristmas": "The Nightmare Before Christmas, Tim Burton stop-motion style, Halloween Town, gothic claymation",
    "jackskellington": "Jack Skellington, the Pumpkin King, wearing a pinstripe suit, spooky graveyard, Tim Burton style",
    "howtotrainyourdragon": "How to Train Your Dragon, Toothless the Night Fury, flying through clouds, Viking island of Berk",
    "kungfupanda": "Kung Fu Panda, Po the dragon warrior, martial arts pose, eating dumplings, ancient China background",
    "pocoyo": "Pocoyo, 3D toddler character, white background, simple colorful shapes, cute educational cartoon",
    "metroman": "Metro Man from Megamind, exaggerated superhero, floating, glowing white outfit, hyper-confident smile",
    "avatarthelastairbender": "Avatar The Last Airbender, bending the four elements, Asian martial arts fantasy, animated series style",
    "walle": "WALL-E, small trash-compacting robot, rusty metal, expressive binocular eyes, holding a green plant, dystopian Earth",
    "iceage": "Ice Age movie, Scrat the squirrel chasing an acorn, snowy prehistoric landscape, 3D animation",
    "regularshow": "Regular Show, Mordecai and Rigby, surreal cartoon network sitcom, park background",
    "couragethecowardlydog": "Courage the Cowardly Dog, purple dog, screaming in fear, creepy Nowhere farmhouse background",
    "adventuretime": "Adventure Time style, Land of Ooo, colorful surreal fantasy, 2D flat vector cartoon",
    "finn": "Finn the Human, wearing a white animal hat, holding a golden sword, Adventure Time style",
    "jake": "Jake the Dog, yellow stretchy magical dog, Adventure Time style",
    "marceline": "Marceline the Vampire Queen, floating, playing an axe bass guitar, Adventure Time style",
    "princessbubblegum": "Princess Bubblegum, pink hair, wearing a crown, science lab, Adventure Time",
    "iceking": "Ice King, long white beard, wearing a magic crown, ice magic, Adventure Time",
    "bmo": "BMO, living game console, cute teal gameboy character, Adventure Time",
    "gunter": "Gunter the penguin, cute but secretly evil, Adventure Time style",
    "rickandmorty": "Rick and Morty, traveling through a glowing green portal, sci-fi animated comedy style",
    "webarebears": "We Bare Bears, Grizz Panda and Ice Bear stacked on top of each other, modern cute cartoon",
    "toystory": "Toy Story, Woody and Buzz Lightyear, living toys, Andy's room, Pixar 3D animation",
    "anime": "high-quality anime style, studio ufotable or mappa quality, detailed cel shading, vibrant 2d animation",
    "dragonball": "Dragon Ball Z aesthetic, spiky hair, energy auras, martial arts, akira toriyama style",
    "goku": "Goku, Super Saiyan, glowing golden aura, charging a Kamehameha, battle-damaged orange gi",
    "vegeta": "Vegeta, Prince of all Saiyans, arrogant smirk, Galick Gun, blue saiyan armor",
    "frieza": "Frieza, final form, white and purple alien emperor, holding a death ball, menacing villain",
    "gohan": "Gohan, Super Saiyan 2, electric aura, wearing piccolo's purple gi, fierce determination",
    "piccolo": "Piccolo, Namekian warrior, green skin, wearing a white cape and turban, charging Special Beam Cannon",
    "trunks": "Future Trunks, holding a sword, purple hair, Capsule Corp jacket, serious expression",
    "majinbuu": "Majin Buu, pink fat alien, smiling, steam coming from head, Dragon Ball Z",
    "onepiece": "One Piece anime style, Grand Line, pirates, epic shonen adventure, Eiichiro Oda style",
    "luffy": "Monkey D. Luffy, Gear 5, laughing, glowing white hair, straw hat, stretching rubber powers",
    "sanji": "Sanji, holding a cigarette, black suit, kicking with a flaming leg, Diable Jambe",
    "chopper": "Tony Tony Chopper, cute reindeer doctor, wearing a pink hat, One Piece",
    "ace": "Portgas D. Ace, no shirt, orange hat, manipulating glowing orange fire, One Piece",
    "zoro": "Roronoa Zoro, using three sword style, green hair, glowing red eye, epic samurai slash",
    "animeboy": "handsome anime boy, detailed eyes, trendy clothing, cool aesthetic, shoujo manga style",
    "animegirl": "beautiful anime girl, flowing hair, expressive big eyes, waifu, kawaii aesthetic, detailed lighting",
    "jujutsukaisen": "Jujutsu Kaisen style, dark fantasy, glowing cursed energy, MAPPA studio animation",
    "yujiitadori": "Yuji Itadori, glowing blue cursed energy on his fists, Jujutsu uniform, dynamic fighting pose",
    "ryomensukuna": "Ryomen Sukuna, King of Curses, evil smirk, tattoos on face, sitting on a throne of skulls",
    "megumifushiguro": "Megumi Fushiguro, summoning divine dogs with hand signs, black shadow magic, Jujutsu Kaisen",
    "tojifushiguro": "Toji Fushiguro, muscular, holding the Inverted Spear of Heaven, menacing assassin",
    "getosuguru": "Suguru Geto, Jujutsu sorcerer, traditional monk robes, surrounded by cursed spirits",
    "satorugojo": "Satoru Gojo, blindfold, white hair, glowing blue six eyes, casting Hollow Purple, infinite void",
    "narutoshippuden": "Naruto Shippuden style, ninja shinobi, Hidden Leaf Village, epic jutsu effects",
    "sasuke": "Sasuke Uchiha, glowing red Sharingan and purple Rinnegan, holding a chidori, dark ninja clothes",
    "uzumakinaruto": "Uzumaki Naruto, Kurama Nine Tails chakra mode, glowing orange aura, holding a Rasengan",
    "sharingan": "Sharingan eye, glowing red, black tomoe spinning, naruto ocular jutsu, close up macro",
    "itachi": "Itachi Uchiha, Akatsuki cloak, red clouds, flock of black crows, glowing Mangekyou Sharingan",
    "kakashi": "Kakashi Hatake, reading a book, face mask, ninja headband covering one eye, lightning blade",
    "hinata": "Hinata Hyuga, Byakugan eyes, gentle fist stance, kind expression, Naruto shippuden",
    "jiraiya": "Jiraiya the toad sage, white spiky hair, red lines on face, standing on a giant toad",
    "sakura": "Sakura Haruno, concentrating chakra into a powerful punch, shattering the ground, pink hair",
    "garaa": "Gaara of the Sand, manipulating floating sand, kanji for love on forehead, serious gaze",
    "madara": "Madara Uchiha, epic villain, red samurai armor, massive Susanoo aura behind him, god of shinobi",
    "crayonshinchan": "Crayon Shin-chan, Shinnosuke Nohara, simple 2D cartoon style, funny mischievous kid",
    "shinchan": "Shin-chan, red shirt and yellow shorts, funny dance, classic Japanese anime",
    "sanrio": "Sanrio aesthetic, pastel colors, super cute kawaii, Hello Kitty universe",
    "hellokitty": "Hello Kitty, wearing a pink bow, cute minimalist design, pastel pink background",
    "kuromi": "Kuromi, cheeky black rabbit, wearing a black jester hat with a pink skull, gothic kawaii",
    "demonslayer": "Demon Slayer (Kimetsu no Yaiba) style, Ufotable animation, stunning water or fire breathing effects",
    "tanjirokamado": "Tanjiro Kamado, green and black checkered haori, holding a katana, stunning water breathing dragon effect",
    "nezukokamado": "Nezuko Kamado, bamboo muzzle, cute demon girl, pink kimono, shrinking size",
    "shinobu": "Shinobu Kocho, insect hashira, butterfly hairpiece, elegant purple poison sword, beautiful smile",
    "rengoku": "Kyojuro Rengoku, flame hashira, fiery yellow and red hair, enthusiastic smile, flame breathing slash",
    "akaza": "Akaza, upper rank demon, pink hair, blue tattoos on skin, martial arts stance, compass needle technique",
    "zenitsuagatsuma": "Zenitsu Agatsuma, sleeping pose, thunder breathing first form, glowing yellow lightning, extreme speed",
    "inosukehashibira": "Inosuke Hashibira, wearing a hollowed-out boar head, dual jagged swords, beast breathing",
    "dandadan": "Dandadan manga style, supernatural action, crazy chaotic perspective, aliens and ghosts",
    "kentakakura": "Okarun from Dandadan, turbo granny powers, creepy fast movement, supernatural action",
    "tsubasajinnouchi": "Momo Ayase from Dandadan, psychic powers, controlling aura, intense manga panel style",
    "blackclover": "Black Clover, Asta holding anti-magic demon slayer sword, grimmoire, glowing black energy",
    "pokemon": "Pokemon, vibrant colors, catching monsters, Nintendo game aesthetic, anime style",
    "charmande": "Charmander, cute orange lizard pokemon, fire burning on the tip of its tail",
    "pikachu": "Pikachu, electric mouse pokemon, red cheeks, yellow fur, sparking yellow electricity",
    "cubone": "Cubone, wearing a skull helmet, holding a bone club, lonely but cute pokemon",
    "bulbasaur": "Bulbasaur, grass type starter, green skin, large plant bulb on its back, cute smile",
    "gengar": "Gengar, purple ghost pokemon, sinister wide grin, glowing red eyes, spooky shadow",
    "squirtle": "Squirtle, cute blue turtle pokemon, shooting water, wearing black sunglasses",
    "psyduck": "Psyduck, confused yellow duck pokemon, holding its head, psychic headache",
    "sailormoon": "Sailor Moon, Usagi Tsukino, magical girl transformation, sparkling background, 90s retro anime",
    "thegodofhighschool": "The God of High School, epic martial arts anime, high-speed combat, webtoon style",
    "jinmori": "Jin Mori, Monkey King form, extending staff, taekwondo kicks, epic webtoon action",
    "sakamotodays": "Sakamoto Days, chubby assassin in a convenience store apron, John Wick style action in manga",
    "haikyu": "Haikyuu!!, intense volleyball match, jumping for a spike, dynamic sports anime, realistic sweat",
    "shoyohinata": "Shoyo Hinata, jumping incredibly high, spiking a volleyball, orange hair, intense focus",
    "tobiokageyama": "Tobio Kageyama, setting the volleyball with precision, intense aura, King of the Court",
    "swordartonline": "Sword Art Online, Aincrad background, virtual reality MMORPG, glowing UI interfaces, epic sword fight",
    "asuna": "Asuna Yuuki, Knights of the Blood Oath uniform, holding a rapier, lightning fast thrusts, SAO",
    "alice": "Alice Zuberg, golden armor, glowing fragrant olive sword, SAO Alicization, beautiful knight",
    "ghibli": "Studio Ghibli style, lush watercolor backgrounds, magical realism, nostalgic and peaceful",
    "totoro": "My Neighbor Totoro, giant fluffy friendly forest spirit, holding an umbrella in the rain, Ghibli",
    "spiritedaway": "Spirited Away, Chihiro running through a magical spirit world, mysterious bathhouse background, Ghibli",
    "ponyo": "Ponyo, cute magical fish girl, running on giant blue ocean waves, Studio Ghibli art",
    "bluelock": "Blue Lock anime, intense soccer manga style, glowing puzzle pieces, glowing eyes, egoist striker",
    "kurokonobasket": "Kuroko's Basketball, glowing eye zone, supernatural basketball moves, high speed action",
    "darlinginthefranxx": "Darling in the FranXX, futuristic mecha, post-apocalyptic world, neon glowing interfaces",
    "zerotwo": "Zero Two, pink hair, cute red horns, wearing a red pilot suit, darling in the franxx waifu",
    "myheroacademia": "My Hero Academia, plus ultra, superhero high school, comic book shading, epic quirks",
    "izuku": "Izuku Midoriya, Deku, glowing green lightning full cowl, heroic punch, My Hero Academia",
    "himikotoga": "Himiko Toga, crazy yandere smile, blonde buns, holding a knife, villain outfit",
    "chainsawman": "Chainsaw Man style, dark gritty anime, blood and gore, cinematic MAPPA lighting",
    "denji": "Denji as Chainsaw Man, chainsaws extending from head and arms, revving engine, bloody epic battle",
    "slamdunk": "Slam Dunk retro anime style, 90s basketball manga, realistic anatomy, intense high school match",
    "conan": "Detective Conan, Edogawa Conan pointing his finger, truth is always one, mystery solving",
    "doraemon": "Doraemon, blue robot cat from the future, bamboo copter, anywhere door, classic anime",
    "sololeveling": "Solo Leveling webtoon style, glowing blue system UI, shadow monarch, dark epic fantasy",
    "sungjinwoo": "Sung Jin-Woo, glowing blue eyes, holding dual daggers, commanding an army of black shadows",
    "bleach": "Bleach anime, shinigami, soul society, hollow masks, epic sword releases, Tite Kubo style",
    "ichigokurosaki": "Ichigo Kurosaki, bankai form, holding Zangetsu sword, black and red getsuga tensho aura",
    "toshirohitsugaya": "Toshiro Hitsugaya, ice dragon wings, Daiguren Hyorinmaru, freezing cold aura, captain coat",
    "shihouinyoruichi": "Yoruichi Shihoin, flash goddess, glowing lightning aura, martial arts stance, Bleach",
    "aizensosuke": "Sosuke Aizen, slicked back hair, arrogant god complex smile, crushing glasses, Bleach villain",
    "ranma": "Ranma 1/2, classic Rumiko Takahashi anime style, martial arts comedy, 90s aesthetic",
    "worldtrigger": "World Trigger, trion weapons, sci-fi tactical squad battle, glowing green cubes",
    "frieren": "Frieren Beyond Journey's End, beautiful elven mage, casting glowing magical spell, peaceful fantasy landscape",
    "spyxfamily": "Spy x Family, wholesome fake family, 1960s retro spy aesthetic, comedy anime",
    "loidforger": "Loid Forger, Twilight, handsome spy, wearing a green suit, holding a silenced pistol",
    "anyaforger": "Anya Forger, pink hair, cute smug expression, reading minds, holding a peanut, Spy x Family",
    "yorforger": "Yor Forger, Thorn Princess, wearing a black assassin dress, holding golden stilettos, deadly but beautiful",
    "rezero": "Re:Zero, starting life in another world, dark psychological fantasy, epic magic, isekai",
    "ram": "Ram, pink-haired maid, cute but sarcastic expression, holding a cleaning mop, Re:Zero",
    "rem": "Rem, blue-haired maid, holding a chained morningstar, sweet expression, Re:Zero waifu",
    "subaru": "Natsuki Subaru, return by death, suffering expression, wearing a tracksuit, Re:Zero",
    "attackontitan": "Attack on Titan, vertical maneuvering equipment, massive flesh titans, walled city, MAPPA gritty style",
    "leviackerman": "Levi Ackerman, survey corps cape, holding dual blades, spinning attack, intensely fast, AoT",
    "erenyeager": "Eren Yeager, Attack Titan form, roaring, glowing green eyes, rumbling, dark and gritty",
    "oshinoko": "Oshi no Ko, idol culture, glowing starry eyes, gorgeous colorful stage lights, dramatic shadows",
    "fullmetalalchemist": "Fullmetal Alchemist Brotherhood, alchemy transmutation circles, glowing blue electricity, steampunk aesthetic",
    "mobpsycho100": "Mob Psycho 100, 100% psychic explosion, chaotic colorful animation, surreal psychic powers",
    "overlord": "Overlord anime, Ainz Ooal Gown, giant skeletal lich, glowing red eyes, supreme ruler of Nazarick",
    "fate": "Fate/Stay Night, holy grail war, beautifully animated Ufotable fight scene, noble phantasm clash",
    "saber": "Saber Artoria Pendragon, holding glowing Excalibur, blue knight dress, holy light, Fate series",
    "hunterxhunter": "Hunter x Hunter, nen aura, epic shonen battles, Yoshihiro Togashi manga style",
    "humans": "realistic human portrait, cinematic lighting, raw photo, highly detailed face features, 8k",
    "kpop": "K-pop idol aesthetic, stage performance, glowing concert lights, fashionable outfits, attractive dancing",
    "bigbang": "BIGBANG K-pop group, legendary hip-hop stage presence, crown lightsticks, yellow glowing ocean",
    "bts": "BTS K-pop group, army bomb lightsticks, synchronized dancing, stadium concert, stylish outfits",
    "blackpink": "BLACKPINK, K-pop girl group, pink venom aesthetic, high fashion outfits, charismatic stage presence",
    "celeb": "Hollywood celebrity portrait, red carpet event, paparazzi camera flashes, glamorous designer fashion",
    "taylorswift": "Taylor Swift, eras tour concert, sparkly dress, playing an acoustic guitar, massive stadium crowd",
    "pesopluma": "Peso Pluma, Mexican singer, regional mexican music, mullet haircut, stylish streetwear",
    "kingvon": "King Von, Chicago drill rapper, O'Block, dreadlocks, hip hop aesthetic, urban streetwear",
    "juicewrld": "Juice WRLD, rapper, 999 aesthetic, emo rap, holding a microphone, purple aesthetic lighting",
    "travisscott": "Travis Scott, rap concert, raging crowd, Astroworld aesthetic, intense stage pyrotechnics, autotune mic",
    "warrior": "epic ancient warrior, battle scars, holding a bloodied sword, standing on a battlefield, cinematic",
    "knight": "medieval knight in shining armor, holding a shield and broadsword, heroic stance, castle background",
    "samurai": "Japanese samurai, ronin, wearing a straw hat, drawing a katana sword, cherry blossoms falling, dramatic lighting",
    "cowboy": "Wild West cowboy, wearing a Stetson hat, holding a revolver, dusty saloon town, high noon standoff",
    "king": "majestic king sitting on a golden throne, wearing a heavy crown, royal robes, regal atmosphere",
    "ninja": "stealthy ninja shinobi, wearing all black, holding a kunai, jumping across rooftops under a full moon",
    "nature": "breathtaking nature landscape, National Geographic photography, peaceful and serene environment, 4k detail",
    "mountain": "snow-capped mountain peaks, towering over a valley, majestic landscape, crisp alpine air, clear blue sky",
    "beach": "tropical beach, white sand, crystal clear turquoise water, palm trees swaying in the wind, sunny paradise",
    "flowers": "field of blooming colorful flowers, spring season, macro photography, soft sunlight, morning dew",
    "sunflower": "bright yellow sunflower field, facing the sun, clear blue sky, happy summer vibe",
    "peony": "beautiful pink peony flower, lush petals, elegant and soft floral photography",
    "rose": "romantic red rose, velvety petals, water droplets on the flower, dark moody background",
    "cherryblossom": "Japanese sakura cherry blossom trees, pink petals falling in the wind, spring time aesthetic",
    "lotus": "pink lotus flower blooming in a calm pond, green lily pads, spiritual zen atmosphere",
    "waterfall": "massive roaring waterfall, crashing into a river below, misty air, lush green jungle surroundings",
    "ocean": "vast deep blue ocean, rolling waves, white sea foam, majestic seascape, calming water",
    "sky": "beautiful dramatic sky, fluffy cumulus clouds, sunset pastel colors, majestic atmosphere",
    "disaster": "natural disaster, cinematic destruction, intense raw power of nature, apocalyptic landscape",
    "storm": "intense thunderstorm, dark ominous clouds, massive lightning strike, heavy rain, dramatic weather",
    "landscape": "epic fantasy landscape, sweeping vistas, rolling hills, glowing sunlight, masterpiece concept art",
    "tree": "giant ancient oak tree, thick roots, lush green leaves, sunlight piercing through the branches",
    "leaf": "macro shot of a single green leaf, detailed veins, water droplet reflecting the forest, nature texture",
    "rain": "heavy rain downpour, water splashing on a dark street, moody cinematic lighting, cyberpunk city or nature",
    "moon": "giant glowing full moon, night sky, detailed lunar craters, mystical and serene nighttime",
    "stone": "ancient glowing runestone, mossy rock texture, mystical forest, fantasy element",
    "winter": "snowy winter landscape, frozen lake, pine trees covered in thick snow, cold serene atmosphere",
    "snowman": "cute snowman, carrot nose, wearing a red scarf and top hat, falling snow, winter wonderland",
    "desert": "Sahara desert sand dunes, golden hour lighting, harsh sun, barren dry landscape",
    "summer": "bright sunny summer day, clear skies, vibrant green grass, warm happy nostalgic feeling",
    "forest": "deep enchanted forest, tall pine trees, misty fog, mysterious and magical woods",
    "vehicle": "high-performance vehicle, sleek design, realistic automotive photography, 8k resolution",
    "car": "sports car driving fast on a mountain road, motion blur, sleek aerodynamic design",
    "audi": "Audi R8, sleek modern luxury car, glowing LED headlights, dark city street background",
    "porsche": "Porsche 911, classic curves, speeding down a coastal highway, luxury sports car photography",
    "lamborghini": "Lamborghini Aventador, aggressive sharp angles, neon synthwave background, hypercar",
    "ferrari": "Ferrari red sports car, racing track, Italian luxury, speed and power, automotive masterpiece",
    "mclaren": "McLaren hypercar, butterfly doors open, sleek carbon fiber body, futuristic design",
    "bmw": "BMW M4, aggressive front grille, drifting on a track, tire smoke, luxury performance",
    "mercedes": "Mercedes-Benz AMG, elegant luxury sedan, sleek silver paint, driving through a modern city",
    "toyota": "Toyota Supra Mk4, JDM legend, tuned street racing car, neon Tokyo underground",
    "ship": "massive cruise ship, sailing on the open ocean, luxury travel, majestic marine vessel",
    "train": "high-speed bullet train, zooming past a futuristic city, motion blur, modern transportation",
    "boat": "small wooden rowboat, floating on a calm misty lake, peaceful serene morning",
    "motorbike": "sleek sports motorcycle, Ducati or Yamaha, racing on a highway, biker in full gear",
    "formula1racing": "Formula 1 race car, zooming past the grandstands, sparking on the asphalt, apex motorsport",
    "abstract": "abstract contemporary art, non-representational, fluid shapes, expressive colors, modern museum piece",
    "pattern": "seamless geometric pattern, intricate mandala, repeating tessellation, mesmerizing background",
    "geometric": "sharp geometric shapes, 3d render, cubes and spheres, modern minimalist architecture style",
    "iphonewallpaper": "aesthetic mobile phone wallpaper, 9:16 aspect ratio, clean design, satisfying colors",
    "firework": "bursting colorful fireworks in the night sky, celebration, long exposure photography, glowing sparks",
    "brokenscreen": "shattered glass screen, realistic cracks, broken phone display prank, sharp glass shards",
    "smoke": "thick billowing colorful smoke bombs, smooth fluid dynamics, abstract misty background",
    "love": "romantic love theme, warm aesthetic, affectionate emotion, beautiful lighting",
    "heart": "glowing red neon heart shape, romantic symbol, valentine aesthetic, 3d rendered icon",
    "couple": "romantic couple, holding hands, walking on the beach at sunset, cinematic silhouette, deep love",
    "fnb": "Food and beverage photography, appetizing, high-resolution food styling, delicious lighting",
    "food": "gourmet restaurant food, beautifully plated dish, steam rising, mouth-watering macro shot",
    "fruit": "fresh juicy sliced fruits, splashing in clear water, high-speed photography, refreshing",
    "drink": "ice cold refreshing cocktail, condensation on the glass, fruit garnish, neon bar lighting",
    "religion": "religious and spiritual aesthetic, divine lighting, sacred atmosphere, respectful portrayal",
    "god": "ethereal divine being, glowing holy light, majestic presence, religious renaissance painting style",
    "cross": "wooden Christian cross, glowing sunlight beaming from behind, symbol of faith, hilltop background",
    "flag": "national flag waving proudly in the wind, photorealistic fabric texture, clear blue sky",
    "vietnam": "Vietnam aesthetic, traditional Ao Dai, Ha Long Bay landscape, bustling Hanoi streets, cultural pride",
    "brazil": "Brazil aesthetic, Christ the Redeemer statue, Rio de Janeiro carnival, vibrant tropical colors",
    "hindugods": "Lord Shiva or Ganesha, beautiful intricate Hindu mythology art, glowing divine aura, colorful",
    "mexico": "Mexico aesthetic, Chichen Itza pyramid, Dia de los Muertos skulls, vibrant cultural fiesta",
    "zodiac": "astrological zodiac sign symbol, glowing constellation in the night sky, mystical astrology art",
    "holiday": "festive holiday celebration, joyful atmosphere, thematic decorations, family warmth",
    "christmas": "cozy Christmas aesthetic, falling snow, warm fireplace, wrapped presents, festive joy",
    "santaclaus": "Santa Claus, wearing red suit, riding a sleigh pulled by reindeer, magical snowy night",
    "christmastree": "tall beautiful Christmas tree, glowing fairy lights, shiny ornaments, star on top",
    "thanksgiving": "Thanksgiving dinner table, roasted turkey, autumn decorations, warm family gathering",
    "newyear": "New Year's Eve celebration, massive midnight fireworks, 2024 glowing sign, party atmosphere",
    "valentine": "Valentine's Day romantic aesthetic, red roses, heart-shaped chocolates, Cupid's arrow",
    "ramadan": "Ramadan aesthetic, glowing crescent moon, beautiful traditional lantern, peaceful night, Islamic art",
    "diwali": "Diwali festival of lights, glowing diya oil lamps, colorful rangoli patterns, Indian celebration",
    "quote": "typography art, inspiring quote text, beautiful background, aesthetic poster design",
    "sadquote": "melancholic background, rainy window, sad emotional typography quote, dark moody aesthetic",
    "funnyquote": "humorous text quote, bright colorful background, meme style typography, funny joke",
    "lovequote": "romantic love quote typography, soft pink aesthetic, elegant cursive font",
    "lifequote": "deep philosophical life quote, nature background, sunset, inspiring typography",
    "motivatequote": "highly motivational gym quote, bold aggressive typography, dark gritty background",
    "scenery": "beautiful breathtaking scenery, cinematic landscape photography, wide angle shot",
    "city": "modern futuristic metropolis, towering skyscrapers, glowing neon lights, cyberpunk or clean aesthetic",
    "village": "cozy European countryside village, cobblestone streets, old stone cottages, peaceful rustic life",
    "architecture": "stunning modern architecture, brutalist concrete or sleek glass design, architectural photography",
    "home": "cozy aesthetic bedroom interior, warm lighting, comfortable bed, lofi study space",
    "wonders": "Seven Wonders of the World, majestic historical monument, awe-inspiring ancient architecture",
    "road": "long empty highway road, stretching to the horizon, desert landscape, road trip feeling",
    "season": "beautiful seasonal transition, changing weather, expressive environmental mood",
    "spring": "Spring season, blooming colorful flowers, fresh green grass, bright warm sunlight, rebirth",
    "autumn": "Autumn fall season, orange and red maple leaves falling, cozy sweater weather, golden hour",
    "meme": "internet meme aesthetic, funny reaction image, viral humor, relatable",
    "middlefinger": "hand showing the middle finger, aggressive punk attitude, blurred background",
    "67": "number 67, bold typography, glowing neon numbers, creative graphic design",
    "warning": "danger warning alert, bold red and yellow colors, hazard symbol, industrial aesthetic",
    "warningsign": "triangular yellow warning sign, exclamation mark, industrial danger zone",
    "warningtext": "WARNING text written in bold red hazard font, glitching screen effect, error message",
    "manhua": "beautiful Chinese Manhua art style, ancient xianxia cultivation, flowing hanfu robes, elegant",
    "tianguancifu": "Heaven Official's Blessing (TGCF), Xie Lian and Hua Cheng, beautiful romantic manhua art, red umbrella, silver butterflies",
    "donghua": "high quality 3D Chinese Donghua animation, epic wuxia fantasy, flying swords, magical martial arts",
    "xianni": "Renegade Immortal (Xian Ni), Wang Lin, cold ruthless cultivator, epic xianxia magic, bloody slaughter",
    "manga": "highly detailed Japanese manga panel, black and white ink style, screentones, dramatic shading",
    "vagabond": "Vagabond manga style, Takehiko Inoue art, Miyamoto Musashi, realistic samurai ink drawing, intense brush strokes",
    "other": "miscellaneous creative concept, highly detailed focal point",
    "ghost": "spooky translucent ghost, floating in a haunted house, glowing blue ectoplasm, Halloween aesthetic",
    "sillyface": "funny silly face expression, exaggerated cartoonish features, goofy smile, crossed eyes",
    "glitter": "sparkling shiny glitter texture, macro photography, reflecting rainbow light, glamorous aesthetic",
    "logo": "professional minimalist logo design, sleek vector graphic, corporate branding, clean mockup",
    "emoji": "3d rendered emoji face, highly detailed, glossy texture, expressive emotion",
    "bt21": "BT21 Line Friends characters, cute colorful mascots, Tata, Chimmy, Cooky, Kpop aesthetic",
    "fire": "roaring hot fire flames, intense glowing heat, dark background, realistic combustion",
    "labubu": "Labubu art toy figure, cute and creepy monster, big teeth smile, trendy designer toy aesthetic",
    "flashlight": "bright beam of light from a flashlight, cutting through dark fog, mysterious exploration",
    "money": "stacks of hundred dollar bills, flying money, wealthy luxury aesthetic, gold coins",
    "dollars": "US dollar bills, macro shot of Benjamin Franklin, green paper money texture, financial wealth",
    "yinyang": "Yin and Yang symbol, perfectly balanced black and white, mystical glowing aura, Daoist philosophy",
    "doublewallpaper": "matching couple wallpaper halves, cohesive aesthetic connecting two phone screens",
    "crybaby": "Pop Mart Crybaby figure, tears on face, cute but sad toy aesthetic, designer collectible",
    "twinkletwinkle": "twinkle twinkle little star, magical glowing starlight, nursery rhyme aesthetic, dreamy night sky"
}

# ==========================================
# 2. TẠO LIST ĐỘNG TRỰC TIẾP TỪ DICTIONARY 
#    (Chống lệch Index)
# ==========================================

STYLES = list(STYLE_PROMPT_MAP.keys())
COLORS = list(COLOR_PROMPT_MAP.keys())
TAGS_OBJECT = ["None"] + list(SUBJECT_PROMPT_MAP.keys())

TAGS_MOOD = ["Happy", "Sad", "Lonely", "Chill", "Funny", "None"]
TAGS_GENDER = ["Boy", "Girl", "Man", "Woman", "Couple", "None"]

# ==========================================
# 3. CLASS DỊCH VỤ CLIP
# ==========================================

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
            
            # Khử hashtag cứng, thay bằng ngữ cảnh tự nhiên cực kỳ chi tiết từ SUBJECT_PROMPT_MAP
            obj_prompts = []
            for tag in TAGS_OBJECT:
                if tag == "None":
                    obj_prompts.append("an empty background scene with no main subject, abstract, plain context")
                else:
                    obj_prompts.append(SUBJECT_PROMPT_MAP.get(tag, f"a clear photo of {tag}"))
            
            mood_prompts = []
            for tag in TAGS_MOOD:
                if tag == "None":
                    mood_prompts.append("inanimate object, landscape, neutral scene, abstract image without any emotion")
                else:
                    mood_prompts.append(f"a person, character, or scene strongly expressing a {tag.lower()} feeling or mood")
            
            gender_prompts = []
            for tag in TAGS_GENDER:
                if tag == "None":
                    gender_prompts.append("an object, landscape, or abstract concept without humans, no people, empty scene")
                else:
                    gender_prompts.append(f"a photo or portrait focusing on a {tag.lower()} character")
            
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

            # ── Object: lọc theo threshold
            # Có ~180 object => random chance là ~0.55%.
            # Threshold = 2.0% (mức tin tưởng cao hơn random gấp ~4 lần)
            OBJ_THRESHOLD = 0.02
            obj_scores = obj_probs[0]
            obj_top2_indices = obj_scores.topk(2).indices.tolist()
            
            obj1 = "None"
            obj2 = "None"
            
            if obj_scores[obj_top2_indices[0]].item() >= OBJ_THRESHOLD:
                obj1 = TAGS_OBJECT[obj_top2_indices[0]]
            if obj_scores[obj_top2_indices[1]].item() >= OBJ_THRESHOLD:
                obj2 = TAGS_OBJECT[obj_top2_indices[1]]

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