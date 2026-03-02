/**
 * api.js
 * ─────────────────────────────────────────────────────────────────
 * Fetch logic cho từng ảnh (file upload hoặc URL).
 * Kết quả được render bằng renderResult() từ render.js.
 * ─────────────────────────────────────────────────────────────────
 */

const API_BASE = window.location.origin.replace(":5500", ":8000");

// ── Shared DOM helpers ────────────────────────────────────────────

/** Đặt trạng thái lỗi cho item card. */
function setItemErrorState(obj, els, statusMsg, tagsMsg, footerMsg) {
  obj.status = "error";
  setItemError(obj, els, statusMsg, tagsMsg, footerMsg);
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

async function loadModelOnServer(modelKey) {
  const form = new FormData();
  if (modelKey) {
    form.append("model", modelKey);
  }
  return await fetchAPI("/tag-image/load-model", form);
}

async function prepareModel(modelKey) {
  const key = modelKey || state.model || (modelSelect ? modelSelect.value : "clip-openai");

  if (state.modelLoading) {
    return;
  }

  state.modelLoading = true;
  state.modelReady = false;

  const modelName = getModelDisplayName(key);

  if (statusDot) statusDot.className = "status-dot status-dot--ok";
  if (statusText) statusText.innerHTML = `Đang tải model <strong>${modelName}</strong>...`;
  if (runButton) runButton.disabled = true;

  const result = await loadModelOnServer(key);

  state.modelLoading = false;

  if (!result.ok) {
    const msgs = getErrorMessages(result.errorCode || "network", result.errorText || "", "file");
    state.modelReady = false;
    if (statusDot) statusDot.className = "status-dot";
    if (statusText) statusText.innerHTML = "Lỗi load model. Vui lòng thử lại hoặc kiểm tra server.";
    showToast("Lỗi load model", msgs.tags, "error", 6000);
    return;
  }

  state.modelReady = true;
  state.model = key;

  if (statusDot) statusDot.className = "status-dot status-dot--ok";
  if (statusText) statusText.innerHTML = `Model <strong>${modelName}</strong> đã sẵn sàng. Hãy thêm ảnh rồi bấm &quot;Chạy hashtag&quot;.`;

  showToast("Model đã sẵn sàng", `Đã load xong model ${modelName}.`, "success", 4000);
  updateSummary();
}

async function initializeDefaultModel() {
  const initialKey = state.model || (modelSelect ? modelSelect.value : "clip-openai");
  console.log("Initializing default model:", initialKey);
  await prepareModel(initialKey);
}

// ── runForFile ────────────────────────────────────────────────────

async function runForFile(fileObj, index) {
  fileObj.status = "processing";
  const modelName = getModelDisplayName(fileObj.model || state.model);

  const getEls = () => {
    const item = gallery.querySelector(`.item[data-id="${fileObj._id}"]`);
    return item ? getItemEls(item) : null;
  };

  let els = getEls();
  if (els) setItemLoading(els, modelName, "Đang xử lý...");

  // Build form
  const form = new FormData();
  form.append("file", fileObj.file);
  form.append("model", fileObj.model || state.model);
  const result = await fetchAPI("/tag-image", form);

  // Refresh els in case gallery was re-rendered
  els = getEls();

  if (!result.ok) {
    const msgs = getErrorMessages(result.errorCode, result.errorText, "file");
    setItemErrorState(fileObj, els, msgs.status, msgs.tags, msgs.footer);
    return;
  }

  applyResultToObj(fileObj, result.data);

  if (els) {
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
  }

  state.completed++;
}

// ── runForUrl ─────────────────────────────────────────────────────

async function runForUrl(urlObj, index) {
  urlObj.status = "processing";
  const modelName = getModelDisplayName(urlObj.model || state.model);
  const getEls = () => {
    const item = gallery.querySelector(`.item[data-id="${urlObj._id}"]`);
    return item ? getItemEls(item) : null;
  };

  let els = getEls();
  if (els) setItemLoading(els, modelName, "Đang tải ảnh & xử lý...");

  // Build form
  const form = new FormData();
  form.append("url", urlObj.url);
  form.append("model", urlObj.model || state.model);
  const result = await fetchAPI("/tag-image/url", form);

  // Refresh els in case gallery was re-rendered
  els = getEls();

  if (!result.ok) {
    const msgs = getErrorMessages(result.errorCode, result.errorText, "url");
    setItemErrorState(urlObj, els, msgs.status, msgs.tags, msgs.footer);
    return;
  }

  applyResultToObj(urlObj, result.data);

  if (els) {
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
  }

  state.completed++;
}

// ── Private helpers ───────────────────────────────────────────────

/** Gán data từ API response vào state object. */
function applyResultToObj(obj, data) {
  // Ưu tiên clip_hashtags (Object, Mood, Gender) nếu có
  if (Array.isArray(data.clip_hashtags) && data.clip_hashtags.length > 0) {
    obj.tags = data.clip_hashtags;
  } else {
    obj.tags = [];
  }

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
