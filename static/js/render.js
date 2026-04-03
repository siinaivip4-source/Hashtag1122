/**
 * render.js
 * ─────────────────────────────────────────────────────────────────
 * Shared rendering logic for tag results.
 * Called by both runForFile & runForUrl (api.js) after API response.
 * ─────────────────────────────────────────────────────────────────
 */

// ── Constants ────────────────────────────────────────────────────

const ALL_STYLES = [
    "None", "2D", "3D", "Cute", "Animeart", "Realism", "Aesthetic",
    "Cool", "Fantasy", "Comic", "Horror", "Cyberpunk", "Lofi",
    "Minimalism", "Digitalart", "Cinematic", "Pixelart", "Scifi", "Vangoghart"
];

const ALL_COLORS = [
    "None", "Black", "White", "Blackandwhite", "Red", "Yellow", "Blue",
    "Green", "Pink", "Orange", "Pastel", "Hologram", "Vintage", "Colorful",
    "Neutral", "Light", "Dark", "Warm", "Cold", "Neon", "Gradient",
    "Purple", "Brown", "Grey"
];

const TAGS_OBJECT = [
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
];

const TAGS_MOOD = ["Happy", "Sad", "Lonely", "Chill", "Funny", "None"];
const TAGS_GENDER = ["Boy", "Girl", "Man", "Woman", "Couple", "None"];

// ── Helpers ──────────────────────────────────────────────────────

// Biến theo dõi dropdown đang mở {wrapper, panel}
let _openDropdown = null;

document.addEventListener("mousedown", (e) => {
    if (_openDropdown) {
        const { wrapper, panel } = _openDropdown;
        if (!wrapper.contains(e.target) && !panel.contains(e.target)) {
            _closeDropdown();
        }
    }
});

function _closeDropdown() {
    if (!_openDropdown) return;
    const { panel } = _openDropdown;
    panel.classList.remove("ssd-panel--open");
    panel.style.display = "none";
    _openDropdown = null;
}

/**
 * Tạo custom searchable dropdown cho Style, Color, Object, Mood, Gender.
 * Có ô tìm kiếm bên trong dropdown để lọc nhanh.
 *
 * @param {string[]} options    - Danh sách option
 * @param {string}   selected   - Giá trị đang được chọn
 * @param {string}   label      - Nhãn hiển thị phía trên
 * @param {Function} onChange   - Callback(newValue) khi đổi giá trị
 * @returns {HTMLElement}
 */
function createSelectEl(options, selected, label, onChange) {
    // Sắp xếp A-Z, None ở đầu
    let sortedOptions = [...options].sort((a, b) => a.localeCompare(b));
    if (sortedOptions.includes("None")) {
        sortedOptions = ["None", ...sortedOptions.filter(o => o !== "None")];
    }
    // Nếu giá trị chọn không có trong list → thêm vào
    if (selected && !sortedOptions.includes(selected)) {
        sortedOptions = [selected, ...sortedOptions];
    }

    let currentValue = selected || sortedOptions[0] || "";

    // ── Wrapper ngoài cùng
    const wrapper = document.createElement("div");
    wrapper.className = "result-select-label ssd-wrapper";

    // ── Nhãn (Object 1, Style...)
    const nameEl = document.createElement("span");
    nameEl.className = "result-select-name";
    nameEl.textContent = label;

    // ── Trigger button (hiển thị giá trị đang chọn)
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "ssd-trigger custom-val-select";
    trigger.textContent = _cap(currentValue) || "—";

    // ── Panel dropdown (input + list)
    const panel = document.createElement("div");
    panel.className = "ssd-panel";
    panel.style.display = "none";

    // Input search bên trong panel
    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.className = "ssd-search";
    searchInput.placeholder = "🔍 Tìm...";
    searchInput.autocomplete = "off";
    searchInput.spellcheck = false;

    // List các option
    const list = document.createElement("div");
    list.className = "ssd-list";

    function renderList(query) {
        const q = (query || "").toLowerCase().trim();
        list.innerHTML = "";
        const filtered = q
            ? sortedOptions.filter(o => o.toLowerCase().includes(q))
            : sortedOptions;

        if (!filtered.length) {
            const empty = document.createElement("div");
            empty.className = "ssd-empty";
            empty.textContent = "Không tìm thấy";
            list.appendChild(empty);
            return;
        }

        filtered.forEach(opt => {
            const item = document.createElement("div");
            item.className = "ssd-item" + (opt === currentValue ? " ssd-item--active" : "");

            if (q) {
                const lower = opt.toLowerCase();
                const idx = lower.indexOf(q);
                if (idx >= 0) {
                    item.innerHTML =
                        _escHtml(opt.slice(0, idx)) +
                        `<mark>${_escHtml(opt.slice(idx, idx + q.length))}</mark>` +
                        _escHtml(opt.slice(idx + q.length));
                } else {
                    item.textContent = opt;
                }
            } else {
                item.textContent = opt;
            }

            item.addEventListener("mousedown", (e) => {
                e.preventDefault();
                currentValue = opt;
                trigger.textContent = _cap(opt);
                onChange(opt);
                _closeDropdown();
                searchInput.value = "";
                renderList("");
            });

            list.appendChild(item);
        });
    }

    renderList("");

    searchInput.addEventListener("input", () => renderList(searchInput.value));

    panel.appendChild(searchInput);
    panel.appendChild(list);

    // Mở / đóng panel
    trigger.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = panel.style.display !== "none";
        if (isOpen) {
            _closeDropdown();
        } else {
            if (_openDropdown) _closeDropdown();
            const rect = trigger.getBoundingClientRect();
            panel.style.top = (rect.bottom + 4) + "px";
            panel.style.left = rect.left + "px";
            panel.style.minWidth = Math.max(rect.width, 160) + "px";
            panel.style.display = "block";
            _openDropdown = { wrapper, panel };
            searchInput.value = "";
            renderList("");
            setTimeout(() => {
                const activeItem = list.querySelector(".ssd-item--active");
                if (activeItem) activeItem.scrollIntoView({ block: "nearest" });
                searchInput.focus();
            }, 30);
        }
    });

    wrapper.appendChild(nameEl);
    wrapper.appendChild(trigger);
    // Panel gắn vào body để không bị clip bởi overflow của card
    document.body.appendChild(panel);
    return wrapper;
}

function _escHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/** Viết hoa chữ cái đầu tiên của chuỗi */
function _cap(str) {
    if (!str) return str;
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// ── Main render function ──────────────────────────────────────────

/**
 * Hiển thị kết quả hashtag vào DOM của một item card.
 *
 * @param {object}   params.obj        - fileObj | urlObj trong state
 * @param {string}   params.stateKey   - "files" | "urls"
 * @param {number}   params.index      - Vị trí trong state[stateKey]
 * @param {string[]} params.tags       - Hashtag trả về từ API [Object, Mood, Gender]
 * @param {string}   params.style      - Style từ API
 * @param {string}   params.color      - Color từ API
 * @param {Element}  params.tagsEl     - .item-tags
 * @param {Element}  params.footerMeta - .item-footer-meta
 * @param {Element}  params.copyBtn    - .item-copy-btn
 * @param {Element}  params.statusText - .item-status-text
 */
function renderResult({ obj, stateKey, index, tags, style, color, tagsEl, footerMeta, copyBtn, statusText }) {
    if (statusText) {
        statusText.textContent = tags.length ? "Đã hoàn thành" : "Không nhận được hashtag";
    }
    if (tagsEl) {
        tagsEl.innerHTML = "";
    } else {
        return; // Không có chỗ để render kết quả
    }

    // ── Row 1: Object1, Object2, Style, Color, Mood, Gender ──────
    const metaRow = document.createElement("div");
    metaRow.className = "result-badges";

    // tags dự kiến là [Object1, Object2, Mood, Gender] từ CLIP (4 phần tử)
    // Backward-compatible với [Object, Mood, Gender] (3 phần tử)
    if (tags.length >= 3) {
        // Khởi tạo selectedTags nếu chưa có (lần đầu render)
        if (!obj.selectedTags) {
            if (tags.length >= 4) {
                // Format mới: [Obj1, Obj2, Mood, Gender]
                const finalObj1   = TAGS_OBJECT.includes(tags[0]) ? tags[0] : "None";
                const finalObj2   = TAGS_OBJECT.includes(tags[1]) ? tags[1] : "None";
                const finalMood   = TAGS_MOOD.includes(tags[2])   ? tags[2] : "None";
                const finalGender = TAGS_GENDER.includes(tags[3]) ? tags[3] : "None";
                obj.selectedTags = [finalObj1, finalObj2, finalMood, finalGender];
            } else {
                // Format cũ: [Obj, Mood, Gender] — Object2 = "None"
                const finalObj1   = TAGS_OBJECT.includes(tags[0]) ? tags[0] : "None";
                const finalMood   = TAGS_MOOD.includes(tags[1])   ? tags[1] : "None";
                const finalGender = TAGS_GENDER.includes(tags[2]) ? tags[2] : "None";
                obj.selectedTags = [finalObj1, "None", finalMood, finalGender];
            }
        }

        // Dropdown 1: Object 1
        metaRow.appendChild(createSelectEl(TAGS_OBJECT, obj.selectedTags[0], "Object 1", val => {
            obj.selectedTags[0] = val;
        }));

        // Dropdown 2: Object 2
        metaRow.appendChild(createSelectEl(TAGS_OBJECT, obj.selectedTags[1], "Object 2", val => {
            obj.selectedTags[1] = val;
        }));

        // Dropdown 3: Style
        metaRow.appendChild(createSelectEl(ALL_STYLES, style || "None", "Style",
            val => { obj.style = val; })
        );

        // Dropdown 4: Color
        metaRow.appendChild(createSelectEl(ALL_COLORS, color || "None", "Color",
            val => { obj.color = val; })
        );

        // Dropdown 5: Mood
        metaRow.appendChild(createSelectEl(TAGS_MOOD, obj.selectedTags[2], "Mood", val => {
            obj.selectedTags[2] = val;
        }));

        // Dropdown 6: Gender
        metaRow.appendChild(createSelectEl(TAGS_GENDER, obj.selectedTags[3], "Gender", val => {
            obj.selectedTags[3] = val;
        }));

        tagsEl.appendChild(metaRow);

        footerMeta.textContent = `Phân loại xong`;
        footerMeta.style.color = "";

        if (copyBtn) {
            copyBtn.disabled = false;
            copyBtn.onclick = () => {
                // Thứ tự hashtag copy: Object1, Object2, Style, Color, Mood, Gender
                const allParts = [
                    obj.selectedTags[0], // Object 1
                    obj.selectedTags[1], // Object 2
                    obj.style,           // Style
                    obj.color,           // Color
                    obj.selectedTags[2], // Mood
                    obj.selectedTags[3]  // Gender
                ]
                    .filter(t => t && t !== "None")
                    .map(t => (t.startsWith("#") ? t : `#${t.toLowerCase().replace(/\s+/g, '')}`));

                navigator.clipboard.writeText(allParts.join(" ")).catch(() => { });
            };
        }

    } else {
        const msg = document.createElement("div");
        msg.style.cssText = "font-size:11.5px; color:var(--text-muted); padding:6px 0;";
        msg.textContent = "Không đủ dữ liệu phân loại (Cần ít nhất Object, Mood, Gender)";
        tagsEl.appendChild(msg);
        footerMeta.textContent = "Lỗi dữ liệu";
        if (copyBtn) copyBtn.disabled = true;
    }
}

