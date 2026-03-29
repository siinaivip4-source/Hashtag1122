/**
 * search.js
 * ─────────────────────────────────────────────────────────────────
 * Tìm kiếm & lọc gallery theo tên file hoặc giá trị hashtag.
 * Gợi ý tự động (autocomplete) khi user gõ.
 * ─────────────────────────────────────────────────────────────────
 */

// ── Nguồn gợi ý theo loại ─────────────────────────────────────────
const SEARCH_SOURCES = {
  all:    () => [...TAGS_OBJECT, ...ALL_STYLES, ...ALL_COLORS, ...TAGS_MOOD, ...TAGS_GENDER],
  object: () => TAGS_OBJECT,
  style:  () => ALL_STYLES.filter(s => s !== "None"),
  color:  () => ALL_COLORS.filter(c => c !== "None"),
  mood:   () => TAGS_MOOD.filter(m => m !== "None"),
  gender: () => TAGS_GENDER.filter(g => g !== "None"),
};

// ── State nội bộ ─────────────────────────────────────────────────
let _searchQuery      = "";
let _searchFilterType = "all";
let _suggestionIndex  = -1;
let _suggestions      = [];

// ── Khởi tạo UI ──────────────────────────────────────────────────

function initSearch() {
  const searchInput   = document.getElementById("searchInput");
  const filterSelect  = document.getElementById("filterTypeSelect");
  const suggestBox    = document.getElementById("searchSuggestions");

  if (!searchInput || !filterSelect || !suggestBox) return;

  // Gõ → cập nhật gợi ý + lọc gallery
  searchInput.addEventListener("input", () => {
    _searchQuery = searchInput.value.trim().toLowerCase();
    _suggestionIndex = -1;
    updateSuggestions(searchInput, suggestBox, filterSelect);
    filterGallery();
  });

  // Đổi loại lọc → reset gợi ý + lọc lại
  filterSelect.addEventListener("change", () => {
    _searchFilterType = filterSelect.value;
    _suggestionIndex = -1;
    updateSuggestions(searchInput, suggestBox, filterSelect);
    filterGallery();
  });

  // Điều hướng bàn phím trong suggestions
  searchInput.addEventListener("keydown", (e) => {
    const items = suggestBox.querySelectorAll(".search-suggestion-item");
    if (!items.length) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      _suggestionIndex = Math.min(_suggestionIndex + 1, items.length - 1);
      highlightSuggestion(items);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      _suggestionIndex = Math.max(_suggestionIndex - 1, -1);
      highlightSuggestion(items);
    } else if (e.key === "Enter" && _suggestionIndex >= 0) {
      e.preventDefault();
      searchInput.value = items[_suggestionIndex].textContent;
      _searchQuery = searchInput.value.trim().toLowerCase();
      hideSuggestions(suggestBox);
      filterGallery();
    } else if (e.key === "Escape") {
      hideSuggestions(suggestBox);
      _suggestionIndex = -1;
    }
  });

  // Ẩn khi click ngoài
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".search-bar-row")) {
      hideSuggestions(suggestBox);
    }
  });

  // Nút xóa search
  const clearSearchBtn = document.getElementById("clearSearchBtn");
  if (clearSearchBtn) {
    clearSearchBtn.addEventListener("click", () => {
      searchInput.value = "";
      _searchQuery = "";
      _suggestionIndex = -1;
      hideSuggestions(suggestBox);
      filterGallery();
    });
  }
}

// ── Gợi ý tự động ────────────────────────────────────────────────

function updateSuggestions(searchInput, suggestBox, filterSelect) {
  const q = searchInput.value.trim().toLowerCase();

  if (!q || q.length < 1) {
    hideSuggestions(suggestBox);
    return;
  }

  const type   = filterSelect ? filterSelect.value : "all";
  const source = (SEARCH_SOURCES[type] || SEARCH_SOURCES["all"])();

  _suggestions = source
    .filter(item => item.toLowerCase().includes(q))
    .slice(0, 10); // Tối đa 10 gợi ý

  if (!_suggestions.length) {
    hideSuggestions(suggestBox);
    return;
  }

  suggestBox.innerHTML = "";
  _suggestions.forEach((item, idx) => {
    const li = document.createElement("div");
    li.className = "search-suggestion-item";

    // Highlight phần khớp
    const lower = item.toLowerCase();
    const start = lower.indexOf(q);
    if (start >= 0) {
      li.innerHTML =
        escapeHtml(item.slice(0, start)) +
        `<mark>${escapeHtml(item.slice(start, start + q.length))}</mark>` +
        escapeHtml(item.slice(start + q.length));
    } else {
      li.textContent = item;
    }

    li.addEventListener("mousedown", (e) => {
      e.preventDefault();
      searchInput.value = item;
      _searchQuery = item.toLowerCase();
      hideSuggestions(suggestBox);
      filterGallery();
    });

    suggestBox.appendChild(li);
  });

  suggestBox.style.display = "block";
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function hideSuggestions(suggestBox) {
  if (suggestBox) {
    suggestBox.style.display = "none";
    suggestBox.innerHTML = "";
  }
}

function highlightSuggestion(items) {
  items.forEach((el, i) => {
    el.classList.toggle("search-suggestion-item--active", i === _suggestionIndex);
  });
}

// ── Lọc gallery ──────────────────────────────────────────────────

/**
 * Ẩn/hiện các .item card dựa trên query và loại lọc.
 * Không xóa data, chỉ thay đổi display.
 */
function filterGallery() {
  const q    = _searchQuery;
  const type = _searchFilterType;
  const items = document.querySelectorAll("#gallery .item");

  if (!q) {
    // Không có query → hiện tất cả
    items.forEach(item => { item.style.display = ""; });
    updateSearchCount(items.length, items.length);
    return;
  }

  let visibleCount = 0;

  items.forEach(item => {
    const matched = itemMatchesFilter(item, q, type);
    item.style.display = matched ? "" : "none";
    if (matched) visibleCount++;
  });

  updateSearchCount(visibleCount, items.length);
}

/**
 * Kiểm tra xem một item card có khớp với query & filter type không.
 */
function itemMatchesFilter(item, q, type) {
  // Lấy data từ state thông qua _id
  const id   = item.dataset.id;
  const kind = item.dataset.type; // "file" | "url"
  const obj  = findObjById(id, kind);
  if (!obj) return false;

  const candidates = getCandidates(obj, type);
  return candidates.some(c => c && c.toLowerCase().includes(q));
}

/** Tìm object trong state theo _id */
function findObjById(id, kind) {
  if (kind === "file") return state.files.find(f => f._id === id);
  if (kind === "url")  return state.urls.find(u => u._id === id);
  return null;
}

/** Lấy danh sách giá trị cần so sánh theo loại lọc */
function getCandidates(obj, type) {
  const tags = Array.isArray(obj.selectedTags) ? obj.selectedTags : [];
  // selectedTags = [Obj1, Obj2, Mood, Gender]
  const [obj1 = "", obj2 = "", mood = "", gender = ""] = tags;
  const style  = obj.style  || "";
  const color  = obj.color  || "";
  const name   = obj.file ? obj.file.name : (obj.url || "");

  switch (type) {
    case "object": return [obj1, obj2];
    case "style":  return [style];
    case "color":  return [color];
    case "mood":   return [mood];
    case "gender": return [gender];
    default:       return [name, obj1, obj2, style, color, mood, gender];
  }
}

/** Cập nhật badge đếm kết quả tìm kiếm */
function updateSearchCount(visible, total) {
  const badge = document.getElementById("searchCountBadge");
  if (!badge) return;
  if (!_searchQuery) {
    badge.textContent = "";
    badge.style.display = "none";
  } else {
    badge.textContent = `${visible}/${total}`;
    badge.style.display = "inline-block";
  }
}

// ── Khởi chạy sau khi DOM sẵn sàng ─────────────────────────────
document.addEventListener("DOMContentLoaded", initSearch);
