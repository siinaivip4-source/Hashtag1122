/**
 * api.js
 * ─────────────────────────────────────────────────────────────────
 * Fetch logic cho từng ảnh (file upload hoặc URL).
 * Kết quả được render bằng renderResult() từ render.js.
 * ─────────────────────────────────────────────────────────────────
 */

const API_BASE = window.location.origin.replace(":5500", ":8000");

// ── Shared DOM helpers ────────────────────────────────────────────

/** Lấy các DOM element cần thiết trong một item card. */
function getItemEls(item) {
  return {
    statusDot: item.querySelector(".item-status-dot"),
    statusText: item.querySelector(".item-status-text"),
    tagsEl: item.querySelector(".item-tags"),
    footerMeta: item.querySelector(".item-footer-meta"),
    copyBtn: item.querySelector(".item-copy-btn"),
  };
}

/** Đặt trạng thái loading cho item card. */
function setItemLoading(els, modelName, loadingMsg) {
  const { statusDot, statusText, tagsEl, footerMeta, copyBtn } = els;
  statusDot.className = "item-status-dot";
  statusText.textContent = "Đang xử lý...";
  tagsEl.innerHTML = `<div class="loading-indicator"><span class="loading-spinner"></span> ${loadingMsg} <strong>${modelName}</strong>...</div>`;
  footerMeta.textContent = `Model: ${modelName}`;
  copyBtn.disabled = true;
}

/** Đặt trạng thái lỗi cho item card. */
function setItemError(obj, els, statusMsg, tagsMsg, footerMsg) {
  const { statusDot, statusText, tagsEl, footerMeta } = els;
  obj.status = "error";
  statusDot.className = "item-status-dot";
  statusText.textContent = statusMsg;
  tagsEl.textContent = tagsMsg;
  footerMeta.textContent = footerMsg;
  state.failed++;
}

// ── Shared fetch + parse ──────────────────────────────────────────

/**
 * Gửi FormData đến API endpoint, xử lý lỗi mạng và parse JSON.
 * @returns {{ ok: boolean, data?: object, errorCode?: string, errorText?: string }}
 */
async function fetchAPI(endpoint, form) {
  let resp;
  try {
    resp = await fetch(API_BASE + endpoint, { method: "POST", body: form });
  } catch (err) {
    return { ok: false, errorCode: "network", errorText: String(err) };
  }

  if (!resp.ok) {
    const text = await resp.text();
    return { ok: false, errorCode: `http_${resp.status}`, errorText: text };
  }

  try {
    const data = await resp.json();
    return { ok: true, data };
  } catch (err) {
    return { ok: false, errorCode: "json", errorText: String(err) };
  }
}

// ── runForFile ────────────────────────────────────────────────────

async function runForFile(fileObj, index, customVocab) {
  const item = gallery.querySelector(`.item[data-index="${index}"][data-type="file"]`);
  if (!item) return;

  const els = getItemEls(item);
  const modelName = getModelDisplayName(fileObj.model);

  setItemLoading(els, modelName, "Đang xử lý với");

  // Build form
  const form = new FormData();
  form.append("file", fileObj.file);
  form.append("num_tags", fileObj.numTags);
  form.append("language", fileObj.lang);
  form.append("model", fileObj.model);
  form.append("mode", fileObj.mode || state.mode);
  if (customVocab) form.append("custom_vocabulary", customVocab);

  const result = await fetchAPI("/tag-image", form);

  if (!result.ok) {
    const msgs = getErrorMessages(result.errorCode, result.errorText, "file");
    setItemError(fileObj, els, msgs.status, msgs.tags, msgs.footer);
    return;
  }

  applyResultToObj(fileObj, result.data);
  els.statusDot.className = "item-status-dot item-status-dot--ok";

  renderResult({
    obj: fileObj,
    stateKey: "files",
    index,
    tags: fileObj.tags,
    style: fileObj.style,
    color: fileObj.color,
    tagsEl: els.tagsEl,
    footerMeta: els.footerMeta,
    copyBtn: els.copyBtn,
    statusText: els.statusText,
  });

  state.completed++;
}

// ── runForUrl ─────────────────────────────────────────────────────

async function runForUrl(urlObj, index, customVocab) {
  const item = gallery.querySelector(`.item[data-index="${index}"][data-type="url"]`);
  if (!item) return;

  const els = getItemEls(item);
  const modelName = getModelDisplayName(urlObj.model);

  setItemLoading(els, modelName, "Đang tải ảnh & xử lý với");

  // Build form
  const form = new FormData();
  form.append("url", urlObj.url);
  form.append("num_tags", urlObj.numTags);
  form.append("language", urlObj.lang);
  form.append("model", urlObj.model);
  form.append("mode", urlObj.mode || state.mode);
  if (customVocab) form.append("custom_vocabulary", customVocab);

  const result = await fetchAPI("/tag-image/url", form);

  if (!result.ok) {
    const msgs = getErrorMessages(result.errorCode, result.errorText, "url");
    setItemError(urlObj, els, msgs.status, msgs.tags, msgs.footer);
    return;
  }

  applyResultToObj(urlObj, result.data);
  els.statusDot.className = "item-status-dot item-status-dot--ok";

  renderResult({
    obj: urlObj,
    stateKey: "urls",
    index,
    tags: urlObj.tags,
    style: urlObj.style,
    color: urlObj.color,
    tagsEl: els.tagsEl,
    footerMeta: els.footerMeta,
    copyBtn: els.copyBtn,
    statusText: els.statusText,
  });

  state.completed++;
}

// ── Private helpers ───────────────────────────────────────────────

/** Gán data từ API response vào state object. */
function applyResultToObj(obj, data) {
  obj.tags = Array.isArray(data.tags) ? data.tags : [];
  obj.caption = data.caption || "";
  obj.style = data.style || "";
  obj.color = data.color || "";
  obj.status = "done";
}

/** Tạo object thông báo lỗi dựa trên errorCode. */
function getErrorMessages(errorCode, errorText, type) {
  if (errorCode === "network") {
    return {
      status: "Lỗi kết nối",
      tags: type === "file"
        ? "Không kết nối được tới API. Kiểm tra server FastAPI và model local."
        : "Không kết nối được tới API.",
      footer: "Lỗi kết nối",
    };
  }
  if (errorCode.startsWith("http_")) {
    const code = errorCode.replace("http_", "");
    return {
      status: `HTTP ${code}`,
      tags: "API trả về lỗi: " + errorText,
      footer: `Lỗi HTTP ${code}`,
    };
  }
  // json parse error
  return {
    status: "Lỗi parse JSON",
    tags: "Không đọc được JSON từ API. Kiểm tra cấu trúc backend.",
    footer: "Lỗi JSON",
  };
}
