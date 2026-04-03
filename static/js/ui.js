/** Lấy các DOM element cần thiết trong một item card. */
function getItemEls(item) {
  if (!item) return null;
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
  if (!els) return;
  const { statusDot, statusText, tagsEl, footerMeta, copyBtn } = els;
  if (statusDot) statusDot.className = "item-status-dot";
  if (statusText) statusText.textContent = "Đang xử lý...";
  if (tagsEl) tagsEl.innerHTML = `<div class="loading-indicator"><span class="loading-spinner"></span> ${loadingMsg} <strong>${modelName}</strong>...</div>`;
  if (footerMeta) footerMeta.textContent = `Model: ${modelName}`;
  if (copyBtn) copyBtn.disabled = true;
}

/** Đặt trạng thái lỗi cho item card. */
function setItemError(obj, els, statusMsg, tagsMsg, footerMsg) {
  obj.status = "error";
  if (!els) return;
  const { statusDot, statusText, tagsEl, footerMeta } = els;
  if (statusDot) statusDot.className = "item-status-dot";
  if (statusText) statusText.textContent = statusMsg;
  if (tagsEl) tagsEl.textContent = tagsMsg;
  if (footerMeta) footerMeta.textContent = footerMsg;
  if (els.copyBtn) els.copyBtn.disabled = true;
}

function createItem(fileObj, index) {
  const item = document.createElement("div");
  item.className = "item";
  item.dataset.index = index;
  item.dataset.id = fileObj._id;
  item.dataset.type = "file";
  item.dataset.model = fileObj.model || state.model;

  const thumb = document.createElement("div");
  thumb.className = "item-thumb";

  const img = document.createElement("img");
  img.alt = fileObj.file.name;
  img.src = fileObj.previewUrl || "";
  img.loading = "lazy";
  img.decoding = "async";
  img.style.cursor = "zoom-in";
  img.onclick = () => openImagePreview(fileObj.previewUrl || "");

  // Actions overlay
  const actions = document.createElement("div");
  actions.className = "item-actions";
  actions.innerHTML = `
    <button type="button" class="item-action-btn btn-delete-single" title="Xóa">✕</button>
  `;

  const label = document.createElement("div");
  label.className = "item-thumb-label";
  label.innerHTML = `<span>${fileObj.file.name}</span>`;

  const pill = document.createElement("div");
  pill.className = "item-thumb-pill";
  pill.innerHTML = `<span class="item-thumb-pill-dot"></span>${formatSize(fileObj.file.size)}`;

  thumb.appendChild(img);
  thumb.appendChild(label);
  thumb.appendChild(pill);

  const body = document.createElement("div");
  body.className = "item-body";

  const modelName = getModelDisplayName(fileObj.model || state.model);

  const rowTop = document.createElement("div");
  rowTop.className = "item-row-top";
  rowTop.innerHTML = `
    <div class="item-meta">
      <span class="stt-badge">STT: ${state.startIndex + index}</span>
      <span class="model-badge model-badge--${fileObj.model || state.model}">${modelName}</span>
    </div>
    <div class="item-status">
      <span class="item-status-dot"></span>
      <span class="item-status-text">Chưa chạy</span>
    </div>
  `;

  const tagsEl = document.createElement("div");
  tagsEl.className = "item-tags";
  tagsEl.textContent = "Hashtag sẽ xuất hiện ở đây sau khi chạy.";

  const footer = document.createElement("div");
  footer.className = "item-footer";
  footer.innerHTML = `
    <span class="item-footer-meta">Chưa xử lý</span>
    <button type="button" class="item-action-btn btn-run-single" title="Xử lý ảnh này">▶</button>
  `;

  body.appendChild(rowTop);
  body.appendChild(tagsEl);
  body.appendChild(footer);

  item.appendChild(thumb);
  item.appendChild(body);
  item.appendChild(actions);

  // Restore state if already processed
  if (fileObj.status === "done") {
    const els = getItemEls(item);
    renderResult({
      obj: fileObj,
      stateKey: "files",
      index: index,
      tags: fileObj.tags || [],
      style: fileObj.style,
      color: fileObj.color,
      tagsEl: els.tagsEl,
      footerMeta: els.footerMeta,
      copyBtn: els.copyBtn,
      statusText: els.statusText
    });
    els.statusDot.className = "item-status-dot item-status-dot--ok";
  } else if (fileObj.status === "error") {
    const els = getItemEls(item);
    setItemError(fileObj, els, "Thất bại", fileObj.error || "Lỗi không xác định", "Xử lý lỗi");
  } else if (fileObj.status === "processing") {
    const els = getItemEls(item);
    const mName = getModelDisplayName(fileObj.model || state.model);
    setItemLoading(els, mName, "Đang xử lý với");
  }

  return item;
}

function createUrlItem(urlObj, index, offset = 0) {
  const item = document.createElement("div");
  item.className = "item";
  item.dataset.index = index;
  item.dataset.id = urlObj._id;
  item.dataset.type = "url";
  item.dataset.model = urlObj.model || state.model;

  const thumb = document.createElement("div");
  thumb.className = "item-thumb";

  const img = document.createElement("img");
  img.alt = urlObj.url;
  img.src = urlObj.url;
  img.loading = "lazy";
  img.decoding = "async";
  img.style.cursor = "zoom-in";
  img.onclick = () => openImagePreview(urlObj.url);
  img.onerror = function () {
    this.style.display = "none";
    this.parentElement.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6b7280;font-size:11px;">Ảnh không tải được</div>';
  };

  // Actions overlay
  const actions = document.createElement("div");
  actions.className = "item-actions";
  actions.innerHTML = `
    <button type="button" class="item-action-btn btn-delete-single" title="Xóa">✕</button>
  `;

  const label = document.createElement("div");
  label.className = "item-thumb-label";
  const displayUrl = urlObj.url.length > 30 ? urlObj.url.substring(0, 27) + "..." : urlObj.url;
  label.innerHTML = `<span>${displayUrl}</span>`;

  const pill = document.createElement("div");
  pill.className = "item-thumb-pill";
  pill.innerHTML = `<span class="item-thumb-pill-dot"></span>URL`;

  thumb.appendChild(img);
  thumb.appendChild(label);
  thumb.appendChild(pill);

  const body = document.createElement("div");
  body.className = "item-body";

  const modelName = getModelDisplayName(urlObj.model || state.model);

  const rowTop = document.createElement("div");
  rowTop.className = "item-row-top";
  rowTop.innerHTML = `
    <div class="item-meta">
      <span class="stt-badge">STT: ${state.startIndex + index + offset}</span>
      <span class="model-badge model-badge--${urlObj.model || state.model}">${modelName}</span>
    </div>
    <div class="item-status">
      <span class="item-status-dot"></span>
      <span class="item-status-text">Chưa chạy</span>
    </div>
  `;

  const tagsEl = document.createElement("div");
  tagsEl.className = "item-tags";
  tagsEl.textContent = "Hashtag sẽ xuất hiện ở đây sau khi chạy.";

  const footer = document.createElement("div");
  footer.className = "item-footer";
  footer.innerHTML = `
    <span class="item-footer-meta">Chưa xử lý</span>
    <button type="button" class="item-action-btn btn-run-single" title="Xử lý ảnh này">▶</button>
  `;

  body.appendChild(rowTop);
  body.appendChild(tagsEl);
  body.appendChild(footer);

  item.appendChild(thumb);
  item.appendChild(body);
  item.appendChild(actions);

  // Restore state if already processed
  if (urlObj.status === "done") {
    const els = getItemEls(item);
    renderResult({
      obj: urlObj,
      stateKey: "urls",
      index: index,
      tags: urlObj.tags || [],
      style: urlObj.style,
      color: urlObj.color,
      tagsEl: els.tagsEl,
      footerMeta: els.footerMeta,
      copyBtn: els.copyBtn,
      statusText: els.statusText
    });
    els.statusDot.className = "item-status-dot item-status-dot--ok";
  } else if (urlObj.status === "error") {
    const els = getItemEls(item);
    setItemError(urlObj, els, "Thất bại", urlObj.error || "Lỗi không xác định", "Xử lý lỗi");
  } else if (urlObj.status === "processing") {
    const els = getItemEls(item);
    const mName = getModelDisplayName(urlObj.model || state.model);
    setItemLoading(els, mName, "Đang tải ảnh & xử lý với");
  }

  return item;
}

function refreshGallery() {
  console.log("refreshGallery: files=", state.files.length, "urls=", state.urls.length, "startIndex=", state.startIndex);
  gallery.innerHTML = "";
  state.files.forEach((fileObj, index) => {
    const item = createItem(fileObj, index);
    gallery.appendChild(item);
  });
  const filesCount = state.files.length;
  state.urls.forEach((urlObj, index) => {
    const item = createUrlItem(urlObj, index, filesCount);
    gallery.appendChild(item);
  });
}

// ── Image Preview Logic ──────────────────────────────────────────

const previewModal = document.getElementById("imagePreviewModal");
const previewImg   = document.getElementById("imagePreviewImg");

// Zoom state
let _zoom      = 1;
let _dragStart = null;   // { x, y, ox, oy } origin khi bắt đầu kéo
let _offset    = { x: 0, y: 0 };

const ZOOM_MIN  = 0.2;
const ZOOM_MAX  = 8;
const ZOOM_STEP = 0.15;

function _applyTransform() {
  if (!previewImg) return;
  previewImg.style.transform =
    `translate(${_offset.x}px, ${_offset.y}px) scale(${_zoom})`;
  previewImg.style.cursor = _zoom > 1 ? "grab" : "zoom-in";
}

function _resetZoom() {
  _zoom   = 1;
  _offset = { x: 0, y: 0 };
  _applyTransform();
}

function _zoomBy(delta, cx, cy) {
  const prevZoom = _zoom;
  _zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, _zoom + delta));
  if (_zoom === prevZoom) return;

  // Zoom về tâm con trỏ / tâm modal
  if (cx !== undefined && cy !== undefined && previewImg) {
    const rect = previewImg.getBoundingClientRect();
    const imgCx = rect.left + rect.width  / 2;
    const imgCy = rect.top  + rect.height / 2;
    const dx = cx - imgCx;
    const dy = cy - imgCy;
    const ratio = _zoom / prevZoom - 1;
    _offset.x -= dx * ratio;
    _offset.y -= dy * ratio;
  }
  _applyTransform();
}

// ── Nút điều khiển zoom ────────────────────────────────────────
function _buildZoomControls() {
  const bar = document.createElement("div");
  bar.className = "preview-zoom-bar";
  bar.id = "previewZoomBar";
  bar.innerHTML = `
    <button class="pzb-btn" id="pzbZoomIn"  title="Zoom in (+)">＋</button>
    <button class="pzb-btn" id="pzbReset"   title="Reset zoom (0)">↺</button>
    <button class="pzb-btn" id="pzbZoomOut" title="Zoom out (−)">－</button>
    <span   class="pzb-label" id="pzbLabel">100%</span>
  `;
  previewModal.appendChild(bar);

  document.getElementById("pzbZoomIn") .addEventListener("click", e => { e.stopPropagation(); _zoomBy(+ZOOM_STEP * 2); _updateLabel(); });
  document.getElementById("pzbZoomOut").addEventListener("click", e => { e.stopPropagation(); _zoomBy(-ZOOM_STEP * 2); _updateLabel(); });
  document.getElementById("pzbReset")  .addEventListener("click", e => { e.stopPropagation(); _resetZoom(); _updateLabel(); });
}

function _updateLabel() {
  const lbl = document.getElementById("pzbLabel");
  if (lbl) lbl.textContent = Math.round(_zoom * 100) + "%";
}

// ── Scroll wheel zoom ─────────────────────────────────────────
if (previewModal) {
  previewModal.addEventListener("wheel", e => {
    if (!previewModal.classList.contains("active")) return;
    e.preventDefault();
    const delta = e.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP;
    _zoomBy(delta, e.clientX, e.clientY);
    _updateLabel();
  }, { passive: false });

  // ── Drag to pan ───────────────────────────────────────────────
  previewModal.addEventListener("mousedown", e => {
    if (e.target === previewModal) { closeImagePreview(); return; }
    if (_zoom <= 1) return;
    e.preventDefault();
    _dragStart = { x: e.clientX, y: e.clientY, ox: _offset.x, oy: _offset.y };
    previewImg.style.cursor = "grabbing";
  });

  window.addEventListener("mousemove", e => {
    if (!_dragStart) return;
    _offset.x = _dragStart.ox + (e.clientX - _dragStart.x);
    _offset.y = _dragStart.oy + (e.clientY - _dragStart.y);
    _applyTransform();
  });

  window.addEventListener("mouseup", () => {
    if (!_dragStart) return;
    _dragStart = null;
    _applyTransform(); // reset cursor
  });

  // Click backdrop → đóng (chỉ khi không đang drag)
  previewModal.addEventListener("click", e => {
    if (e.target === previewModal) closeImagePreview();
  });

  // Ngăn click trên ảnh khi không zoom / không kéo kích hoạt đóng modal
  previewImg && previewImg.addEventListener("click", e => e.stopPropagation());

  _buildZoomControls();
}

// ── Phím tắt ─────────────────────────────────────────────────
document.addEventListener("keydown", e => {
  if (!previewModal || !previewModal.classList.contains("active")) return;
  if (e.key === "Escape")    { closeImagePreview(); }
  if (e.key === "0")          { _resetZoom(); _updateLabel(); }
  if (e.key === "+" || e.key === "=") { _zoomBy(+ZOOM_STEP * 2); _updateLabel(); }
  if (e.key === "-")          { _zoomBy(-ZOOM_STEP * 2); _updateLabel(); }
});

/** Mở modal xem ảnh full */
function openImagePreview(src) {
  if (!previewModal || !previewImg) return;
  previewImg.src = src;
  previewImg.style.transform = "";
  _resetZoom();
  _updateLabel();
  previewModal.classList.add("active");
}

/** Đóng modal xem ảnh */
function closeImagePreview() {
  if (!previewModal) return;
  previewModal.classList.remove("active");
  _resetZoom();
  _updateLabel();
}

/**
 * Hiển thị thông báo toast.
 * @param {string} title Tiêu đề
 * @param {string} message Nội dung
 * @param {'success'|'error'|'warning'} type Loại thông báo
 * @param {number} duration Thời gian hiển thị (ms)
 */
function showToast(title, message, type = "success", duration = 4000) {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;

  const iconMap = {
    "success": "✓",
    "error": "✕",
    "warning": "⚠",
    "info": "ℹ"
  };
  const icon = iconMap[type] || "•";

  toast.innerHTML = `
    <div class="toast-icon">${icon}</div>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
  `;

  container.appendChild(toast);

  // Tự động xóa sau duration
  setTimeout(() => {
    toast.classList.add("toast--exit");
    setTimeout(() => {
      if (toast.parentElement) {
        container.removeChild(toast);
      }
    }, 300);
  }, duration);
}
