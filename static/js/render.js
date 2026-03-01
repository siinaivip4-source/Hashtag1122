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

// Đồng bộ với HASHTAGS trong src/services/clip.py
const ALL_HASHTAGS = [
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
];

// ── Helpers ──────────────────────────────────────────────────────

/**
 * Tạo <label> + <select> cho Style, Color hoặc một hashtag.
 * @param {string[]} options    - Danh sách option
 * @param {string}   selected   - Giá trị đang được chọn
 * @param {string}   label      - Nhãn hiển thị phía trên
 * @param {Function} onChange   - Callback(newValue) khi đổi giá trị
 * @returns {HTMLElement} label element
 */
function createSelectEl(options, selected, label, onChange) {
    const wrapper = document.createElement("label");
    wrapper.className = "result-select-label";

    const name = document.createElement("span");
    name.className = "result-select-name";
    name.textContent = label;

    const sel = document.createElement("select");
    sel.className = "custom-val-select";

    // Nếu giá trị hiện tại không có trong danh sách → thêm vào đầu
    const allOpts = options.includes(selected) || !selected
        ? options
        : [selected, ...options];

    allOpts.forEach(opt => {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt;
        if (opt === selected) o.selected = true;
        sel.appendChild(o);
    });

    sel.addEventListener("change", () => onChange(sel.value));

    wrapper.appendChild(name);
    wrapper.appendChild(sel);
    return wrapper;
}

// ── Main render function ──────────────────────────────────────────

/**
 * Hiển thị kết quả hashtag vào DOM của một item card.
 *
 * @param {object}   params.obj        - fileObj | urlObj trong state
 * @param {string}   params.stateKey   - "files" | "urls"
 * @param {number}   params.index      - Vị trí trong state[stateKey]
 * @param {string[]} params.tags       - Hashtag trả về từ API
 * @param {string}   params.style      - Style từ API
 * @param {string}   params.color      - Color từ API
 * @param {Element}  params.tagsEl     - .item-tags
 * @param {Element}  params.footerMeta - .item-footer-meta
 * @param {Element}  params.copyBtn    - .item-copy-btn
 * @param {Element}  params.statusText - .item-status-text
 */
function renderResult({ obj, stateKey, index, tags, style, color, tagsEl, footerMeta, copyBtn, statusText }) {
    statusText.textContent = tags.length ? "Đã hoàn thành" : "Không nhận được hashtag";
    tagsEl.innerHTML = "";

    // ── Row 1: Style & Color ─────────────────────────────────────
    const metaRow = document.createElement("div");
    metaRow.className = "result-badges";

    metaRow.appendChild(
        createSelectEl(ALL_STYLES, style || "None", "Style",
            val => { obj.style = val; })
    );
    metaRow.appendChild(
        createSelectEl(ALL_COLORS, color || "None", "Color",
            val => { obj.color = val; })
    );

    tagsEl.appendChild(metaRow);

    // ── Row 2: Hashtag dropdowns ─────────────────────────────────
    if (tags.length) {
        // Lưu bản copy có thể chỉnh sửa — mỗi phần tử là giá trị hiện tại của dropdown đó
        obj.selectedTags = [...tags];

        const tagsRow = document.createElement("div");
        tagsRow.className = "result-tags-row";

        tags.forEach((tag, i) => {
            const sel = createSelectEl(
                ALL_HASHTAGS,
                tag,
                `#${i + 1}`,
                val => {
                    obj.selectedTags[i] = val;
                }
            );
            tagsRow.appendChild(sel);
        });

        tagsEl.appendChild(tagsRow);

        footerMeta.textContent = `${tags.length} hashtag`;
        footerMeta.style.color = "";
        copyBtn.disabled = false;

        copyBtn.onclick = () => {
            const hashTags = obj.selectedTags.map(t => (t.startsWith("#") ? t : `#${t}`));
            const extras = [obj.style, obj.color].filter(x => x && x !== "None");
            navigator.clipboard.writeText([...hashTags, ...extras].join(" ")).catch(() => { });
        };

    } else {
        const msg = document.createElement("div");
        msg.style.cssText = "font-size:11.5px; color:var(--text-muted); padding:6px 0;";
        msg.textContent = "Không có hashtag nào (do bộ lọc whitelist?)";
        tagsEl.appendChild(msg);
        footerMeta.textContent = "Không có hashtag";
        copyBtn.disabled = true;
    }
}
