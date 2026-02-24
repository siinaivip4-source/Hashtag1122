const state = {
  files: [],
  urls: [],
  lang: "en",
  numTags: 10,
  model: "vit-gpt2",
  mode: "both",
  running: false,
  completed: 0,
  failed: 0,
  inputMode: "file"
};

const fileInput = document.getElementById("fileInput");
const runButton = document.getElementById("runButton");
const clearButton = document.getElementById("clearButton");
const copyAllButton = document.getElementById("copyAllButton");
const exportJsonButton = document.getElementById("exportJsonButton");
const exportExcelButton = document.getElementById("exportExcelButton");
const threadsInput = document.getElementById("threadsInput");
const customVocabInput = document.getElementById("customVocabInput");
const modelSelect = document.getElementById("modelSelect");
const modeSelect = document.getElementById("modeSelect");
const summaryText = document.getElementById("summaryText");
const resultSummary = document.getElementById("resultSummary");
const gallery = document.getElementById("gallery");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const queueHint = document.getElementById("queueHint");
const urlInput = document.getElementById("urlInput");
const fileModeArea = document.getElementById("fileModeArea");
const urlModeArea = document.getElementById("urlModeArea");
const modeFileBtn = document.getElementById("modeFileBtn");
const modeUrlBtn = document.getElementById("modeUrlBtn");

function formatSize(bytes) {
  if (!bytes && bytes !== 0) return "";
  if (bytes < 1024) return bytes + "B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + "KB";
  return (bytes / (1024 * 1024)).toFixed(1) + "MB";
}

function getModelDisplayName(modelKey) {
  const modelNames = {
    "vit-gpt2": "ViT-GPT2",
    "blip-base": "BLIP",
    "git-base": "GIT"
  };
  return modelNames[modelKey] || modelKey;
}

function getModeDisplayName(mode) {
  const modeNames = {
    "both": "Cả 2",
    "clip": "CLIP",
    "vision": "Vision"
  };
  return modeNames[mode] || mode;
}

function updateSummary() {
  const modeDisplay = getModeDisplayName(state.mode);
  summaryText.textContent = `#${state.numTags} tag · ${modeDisplay} · ${state.model}`;
  const total = state.files.length + state.urls.length;
  resultSummary.textContent = `${total} ảnh · ${state.completed} xong · ${state.failed} lỗi`;

  if (!total) {
    queueHint.textContent = "";
    statusDot.className = "status-dot";
    statusText.innerHTML = "Sẵn sàng. Chưa có ảnh nào trong hàng đợi.";
  } else {
    queueHint.textContent = `Đã chọn ${total} ảnh.`;
  }
}

function setRunning(running, finishedMessage = null) {
  state.running = running;
  const hasItems = state.files.length > 0 || state.urls.length > 0;
  runButton.disabled = running || !hasItems;
  clearButton.disabled = running;
  copyAllButton.disabled = running || !(state.files.some(f => f.tags && f.tags.length) || state.urls.some(u => u.tags && u.tags.length));
  exportJsonButton.disabled = running;
  exportExcelButton.disabled = running;
  threadsInput.disabled = running;
  customVocabInput.disabled = running;
  modelSelect.disabled = running;
  modeSelect.disabled = running;
  fileInput.disabled = running;
  urlInput.disabled = running;
  modeFileBtn.disabled = running;
  modeUrlBtn.disabled = running;

  if (running) {
    statusDot.className = "status-dot status-dot--ok";
    statusText.innerHTML = "Đang chạy hashtag cho các ảnh đã chọn...";
  } else {
    if (!state.files.length && !state.urls.length) {
      statusDot.className = "status-dot";
      statusText.innerHTML = "Sẵn sàng (Done).";
    } else {
      statusDot.className = "status-dot status-dot--ok";
      statusText.innerHTML = finishedMessage || "Đã xử lý xong. Bạn có thể thêm ảnh mới.";
    }
  }
}

function createItem(fileObj, index) {
  const item = document.createElement("div");
  item.className = "item";
  item.dataset.index = index;
  item.dataset.type = "file";
  item.dataset.model = fileObj.model || state.model;

  const thumb = document.createElement("div");
  thumb.className = "item-thumb";

  const img = document.createElement("img");
  img.alt = fileObj.file.name;
  img.src = fileObj.previewUrl || "";

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
      <span>EN</span>
      <span>#${fileObj.numTags}</span>
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
    <button type="button" class="item-copy-btn" disabled>Sao chép</button>
  `;

  body.appendChild(rowTop);
  body.appendChild(tagsEl);
  body.appendChild(footer);

  item.appendChild(thumb);
  item.appendChild(body);

  return item;
}

function createUrlItem(urlObj, index) {
  const item = document.createElement("div");
  item.className = "item";
  item.dataset.index = index;
  item.dataset.type = "url";
  item.dataset.model = urlObj.model || state.model;

  const thumb = document.createElement("div");
  thumb.className = "item-thumb";

  const img = document.createElement("img");
  img.alt = urlObj.url;
  img.src = urlObj.url;
  img.onerror = function () {
    this.style.display = "none";
    this.parentElement.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6b7280;font-size:11px;">Ảnh không tải được</div>';
  };

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
      <span>EN</span>
      <span>#${urlObj.numTags}</span>
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
    <button type="button" class="item-copy-btn" disabled>Sao chép</button>
  `;

  body.appendChild(rowTop);
  body.appendChild(tagsEl);
  body.appendChild(footer);

  item.appendChild(thumb);
  item.appendChild(body);

  return item;
}

function refreshGallery() {
  gallery.innerHTML = "";
  state.files.forEach((fileObj, index) => {
    const item = createItem(fileObj, index);
    gallery.appendChild(item);
  });
  state.urls.forEach((urlObj, index) => {
    const item = createUrlItem(urlObj, index);
    gallery.appendChild(item);
  });
  copyAllButton.disabled = !(state.files.some(f => f.tags && f.tags.length) || state.urls.some(u => u.tags && u.tags.length));
}

function addFiles(fileList) {
  const arr = Array.from(fileList || []);
  if (!arr.length) return;

  const startIndex = state.files.length;
  arr.forEach((file, i) => {
    if (!file.type.startsWith("image/")) return;
    const obj = {
      file,
      status: "pending",
      tags: [],
      caption: "",
      style: "",
      color: "",
      error: null,
      previewUrl: URL.createObjectURL(file),
      lang: state.lang,
      numTags: state.numTags,
      model: state.model,
      mode: state.mode
    };
    state.files.push(obj);

    const item = createItem(obj, startIndex + i);
    gallery.appendChild(item);
  });
  updateSummary();
  runButton.disabled = !(state.files.length > 0 || state.urls.length > 0);
}

function parseUrls(text) {
  const lines = text.split(/[\r\n]+/);
  const urls = [];
  const urlRegex = /^https?:\/\/[^\s]+$/i;
  lines.forEach(line => {
    const trimmed = line.trim();
    if (trimmed && urlRegex.test(trimmed)) {
      urls.push(trimmed);
    }
  });
  return urls;
}

function addUrls(urlList) {
  if (!urlList.length) return;

  const startIndex = state.urls.length;
  urlList.forEach((url, i) => {
    const obj = {
      url,
      status: "pending",
      tags: [],
      caption: "",
      style: "",
      color: "",
      error: null,
      lang: state.lang,
      numTags: state.numTags,
      model: state.model,
      mode: state.mode
    };
    state.urls.push(obj);

    const item = createUrlItem(obj, startIndex + i);
    gallery.appendChild(item);
  });
  updateSummary();
  runButton.disabled = !(state.files.length > 0 || state.urls.length > 0);
}

async function runForFile(fileObj, index, customVocab) {
  const item = gallery.querySelector(`.item[data-index="${index}"][data-type="file"]`);
  if (!item) return;

  const statusDot = item.querySelector(".item-status-dot");
  const statusText = item.querySelector(".item-status-text");
  const tagsEl = item.querySelector(".item-tags");
  const footerMeta = item.querySelector(".item-footer-meta");
  const copyBtn = item.querySelector(".item-copy-btn");
  const modelName = getModelDisplayName(fileObj.model);

  statusDot.className = "item-status-dot";
  statusText.textContent = "Đang xử lý...";
  tagsEl.innerHTML = `<div class="loading-indicator"><span class="loading-spinner"></span> Đang xử lý với <strong>${modelName}</strong>...</div>`;
  footerMeta.textContent = `Model: ${modelName}`;
  copyBtn.disabled = true;

  const form = new FormData();
  form.append("file", fileObj.file);
  form.append("num_tags", fileObj.numTags);
  form.append("language", fileObj.lang);
  form.append("model", fileObj.model);
  form.append("mode", fileObj.mode || state.mode);
  if (customVocab) {
    form.append("custom_vocabulary", customVocab);
  }

  let resp;
  try {
    resp = await fetch(window.location.origin.replace(":5500", ":8000") + "/tag-image", {
      method: "POST",
      body: form
    });
  } catch (err) {
    fileObj.status = "error";
    fileObj.error = err;
    statusDot.className = "item-status-dot";
    statusText.textContent = "Lỗi kết nối";
    tagsEl.textContent =
      "Không kết nối được tới API. Kiểm tra server FastAPI và Qwen3 local.";
    footerMeta.textContent = "Lỗi kết nối";
    state.failed++;
    return;
  }

  let data;
  if (!resp.ok) {
    fileObj.status = "error";
    statusDot.className = "item-status-dot";
    statusText.textContent = `HTTP ${resp.status}`;
    tagsEl.textContent = "API trả về lỗi: " + (await resp.text());
    footerMeta.textContent = `Lỗi HTTP ${resp.status}`;
    state.failed++;
    return;
  }

  try {
    data = await resp.json();
  } catch (err) {
    fileObj.status = "error";
    statusDot.className = "item-status-dot";
    statusText.textContent = "Lỗi parse JSON";
    tagsEl.textContent =
      "Không đọc được JSON từ API. Kiểm tra cấu trúc backend.";
    footerMeta.textContent = "Lỗi JSON";
    state.failed++;
    return;
  }

  const tags = Array.isArray(data.tags) ? data.tags : [];
  const caption = data.caption || "";
  const style = data.style || "";
  const color = data.color || "";

  fileObj.caption = caption;
  fileObj.style = style;
  fileObj.color = color;
  fileObj.status = "done";
  fileObj.tags = tags;
  statusDot.className = "item-status-dot item-status-dot--ok";

  let resultHtml = "";
  if (caption) {
    resultHtml += `<div class="result-caption">📝 ${caption}</div>`;
  }
  if (style || color) {
    const badges = [];
    if (style) badges.push(`<span class="badge-style">🎨 ${style}</span>`);
    if (color) badges.push(`<span class="badge-color">${color}</span>`);
    resultHtml += `<div class="result-badges">${badges.join(" ")}</div>`;
  }

  statusText.textContent = tags.length ? "Đã hoàn thành" : "Không nhận được hashtag";
  tagsEl.innerHTML = "";

  if (resultHtml) {
    tagsEl.innerHTML = resultHtml;
  }

  if (tags.length) {
    const tagsContainer = document.createElement("div");
    tagsContainer.className = "tags-list-container";
    tags.forEach((tag) => {
      const el = document.createElement("code");
      el.textContent = tag;
      tagsContainer.appendChild(el);
    });
    tagsEl.appendChild(tagsContainer);

    footerMeta.textContent = `${tags.length} hashtag`;
    copyBtn.disabled = false;
    copyBtn.onclick = () => {
      navigator.clipboard.writeText(tags.join(" ")).catch(() => { });
    };
  } else {
    const noTagsMsg = document.createElement("div");
    noTagsMsg.textContent = "Không có hashtag nào (do bộ lọc whitelist?)";
    tagsEl.appendChild(noTagsMsg);

    footerMeta.textContent = "Không có hashtag";
    copyBtn.disabled = true;
  }

  state.completed++;
}

async function runForUrl(urlObj, index, customVocab) {
  const item = gallery.querySelector(`.item[data-index="${index}"][data-type="url"]`);
  if (!item) return;

  const statusDot = item.querySelector(".item-status-dot");
  const statusText = item.querySelector(".item-status-text");
  const tagsEl = item.querySelector(".item-tags");
  const footerMeta = item.querySelector(".item-footer-meta");
  const copyBtn = item.querySelector(".item-copy-btn");
  const modelName = getModelDisplayName(urlObj.model);

  statusDot.className = "item-status-dot";
  statusText.textContent = "Đang xử lý...";
  tagsEl.innerHTML = `<div class="loading-indicator"><span class="loading-spinner"></span> Đang tải ảnh & xử lý với <strong>${modelName}</strong>...</div>`;
  footerMeta.textContent = `Model: ${modelName}`;
  copyBtn.disabled = true;

  const form = new FormData();
  form.append("url", urlObj.url);
  form.append("num_tags", urlObj.numTags);
  form.append("language", urlObj.lang);
  form.append("model", urlObj.model);
  form.append("mode", urlObj.mode || state.mode);
  if (customVocab) {
    form.append("custom_vocabulary", customVocab);
  }

  let resp;
  try {
    resp = await fetch(window.location.origin.replace(":5500", ":8000") + "/tag-image/url", {
      method: "POST",
      body: form
    });
  } catch (err) {
    urlObj.status = "error";
    urlObj.error = err;
    statusDot.className = "item-status-dot";
    statusText.textContent = "Lỗi kết nối";
    tagsEl.textContent = "Không kết nối được tới API.";
    footerMeta.textContent = "Lỗi kết nối";
    state.failed++;
    return;
  }

  let data;
  if (!resp.ok) {
    urlObj.status = "error";
    statusDot.className = "item-status-dot";
    statusText.textContent = `HTTP ${resp.status}`;
    const errorText = await resp.text();
    tagsEl.textContent = "Lỗi: " + errorText;
    footerMeta.textContent = `Lỗi HTTP ${resp.status}`;
    state.failed++;
    return;
  }

  try {
    data = await resp.json();
  } catch (err) {
    urlObj.status = "error";
    statusDot.className = "item-status-dot";
    statusText.textContent = "Lỗi parse JSON";
    tagsEl.textContent = "Không đọc được JSON từ API.";
    footerMeta.textContent = "Lỗi JSON";
    state.failed++;
    return;
  }

  const tags = Array.isArray(data.tags) ? data.tags : [];
  const caption = data.caption || "";
  const style = data.style || "";
  const color = data.color || "";

  urlObj.caption = caption;
  urlObj.style = style;
  urlObj.color = color;
  urlObj.status = "done";
  urlObj.tags = tags;
  statusDot.className = "item-status-dot item-status-dot--ok";

  let resultHtml = "";
  if (caption) {
    resultHtml += `<div class="result-caption">📝 ${caption}</div>`;
  }
  if (style || color) {
    const badges = [];
    if (style) badges.push(`<span class="badge-style">🎨 ${style}</span>`);
    if (color) badges.push(`<span class="badge-color">${color}</span>`);
    resultHtml += `<div class="result-badges">${badges.join(" ")}</div>`;
  }

  statusText.textContent = tags.length ? "Đã hoàn thành" : "Không nhận được hashtag";
  tagsEl.innerHTML = "";

  if (resultHtml) {
    tagsEl.innerHTML = resultHtml;
  }

  if (tags.length) {
    const tagsContainer = document.createElement("div");
    tagsContainer.className = "tags-list-container";
    tags.forEach((tag) => {
      const el = document.createElement("code");
      el.textContent = tag;
      tagsContainer.appendChild(el);
    });
    tagsEl.appendChild(tagsContainer);

    footerMeta.textContent = `${tags.length} hashtag`;
    copyBtn.disabled = false;
    copyBtn.onclick = () => {
      navigator.clipboard.writeText(tags.join(" ")).catch(() => { });
    };
  } else {
    const noTagsMsg = document.createElement("div");
    noTagsMsg.textContent = "Không có hashtag nào (do bộ lọc whitelist?)";
    tagsEl.appendChild(noTagsMsg);

    footerMeta.textContent = "Không có hashtag";
    copyBtn.disabled = true;
  }

  state.completed++;
}

async function runAll() {
  const hasFiles = state.files.length > 0;
  const hasUrls = state.urls.length > 0;
  if ((!hasFiles && !hasUrls) || state.running) return;
  state.completed = 0;
  state.failed = 0;
  setRunning(true);

  const concurrency = parseInt(threadsInput.value) || 1;
  const customVocab = customVocabInput.value;

  const queue = [];
  state.files.forEach((fileObj, i) => queue.push({ type: "file", obj: fileObj, index: i }));
  state.urls.forEach((urlObj, i) => queue.push({ type: "url", obj: urlObj, index: i }));

  async function worker() {
    while (queue.length > 0 && state.running) {
      const task = queue.shift();
      try {
        if (task.type === "file") {
          await runForFile(task.obj, task.index, customVocab);
        } else {
          await runForUrl(task.obj, task.index, customVocab);
        }
      } catch (e) {
        console.error("Task failed", e);
      }
      updateSummary();
    }
  }

  const startTime = Date.now();

  const promises = [];
  for (let i = 0; i < concurrency; i++) {
    promises.push(worker());
  }

  await Promise.all(promises);

  const durationStr = ((Date.now() - startTime) / 1000).toFixed(2);
  setRunning(false, `Đã xử lý xong toàn bộ trong <b>${durationStr}s</b>. Bạn có thể thêm ảnh mới.`);
}

function clearAll() {
  if (state.running) return;
  state.files.forEach((f) => {
    if (f.previewUrl) URL.revokeObjectURL(f.previewUrl);
  });
  state.files = [];
  state.urls = [];
  state.completed = 0;
  state.failed = 0;
  urlInput.value = "";
  refreshGallery();
  updateSummary();
}

function copyAllHashtags() {
  const allTags = [];
  state.files.forEach((f) => {
    if (Array.isArray(f.tags) && f.tags.length) {
      allTags.push(...f.tags);
    }
  });
  state.urls.forEach((u) => {
    if (Array.isArray(u.tags) && u.tags.length) {
      allTags.push(...u.tags);
    }
  });
  if (!allTags.length) return;
  navigator.clipboard.writeText(allTags.join(" ")).catch(() => { });
}

function getExportData() {
  const data = [];
  let stt = 1;
  state.files.forEach((f) => {
    if (f.status === "done") {
      data.push({
        "STT": stt++,
        "Tên file": f.file.name,
        "Caption": f.caption || "",
        "Style": f.style || "",
        "Color": f.color || "",
        "Hashtags": (f.tags || []).join(" ")
      });
    }
  });
  state.urls.forEach((u) => {
    if (u.status === "done") {
      data.push({
        "STT": stt++,
        "Tên file": u.url,
        "Caption": u.caption || "",
        "Style": u.style || "",
        "Color": u.color || "",
        "Hashtags": (u.tags || []).join(" ")
      });
    }
  });
  return data;
}

function exportToJson() {
  const data = getExportData();
  if (!data.length) return;

  const jsonStr = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "hashtags_export.json";
  a.click();
  URL.revokeObjectURL(url);
}

function exportToExcel() {
  const data = getExportData();
  if (!data.length) return;

  const headers = ["STT", "Tên file", "Caption", "Style", "Color", "Hashtags"];
  let csv = headers.join(",") + "\n";

  data.forEach(row => {
    const values = [
      row["STT"],
      `"${(row["Tên file"] || "").replace(/"/g, '""')}"`,
      `"${(row["Caption"] || "").replace(/"/g, '""')}"`,
      `"${(row["Style"] || "").replace(/"/g, '""')}"`,
      `"${(row["Color"] || "").replace(/"/g, '""')}"`,
      `"${(row["Hashtags"] || "").replace(/"/g, '""')}"`
    ];
    csv += values.join(",") + "\n";
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "hashtags_export.csv";
  a.click();
  URL.revokeObjectURL(url);
}

fileInput.addEventListener("change", (e) => {
  addFiles(e.target.files);
  e.target.value = "";
});

urlInput.addEventListener("change", () => {
  const urls = parseUrls(urlInput.value);
  if (urls.length > 0) {
    addUrls(urls);
    urlInput.value = "";
  }
});

modeFileBtn.addEventListener("click", () => {
  if (state.running) return;
  state.inputMode = "file";
  modeFileBtn.classList.add("toggle--active");
  modeUrlBtn.classList.remove("toggle--active");
  fileModeArea.style.display = "block";
  urlModeArea.style.display = "none";
});

modeUrlBtn.addEventListener("click", () => {
  if (state.running) return;
  state.inputMode = "url";
  modeUrlBtn.classList.add("toggle--active");
  modeFileBtn.classList.remove("toggle--active");
  fileModeArea.style.display = "none";
  urlModeArea.style.display = "block";
});

window.switchMode = function (mode) {
  if (state.running) return;
  if (mode === "url") {
    state.inputMode = "url";
    modeUrlBtn.classList.add("toggle--active");
    modeFileBtn.classList.remove("toggle--active");
    fileModeArea.style.display = "none";
    urlModeArea.style.display = "block";
  } else {
    state.inputMode = "file";
    modeFileBtn.classList.add("toggle--active");
    modeUrlBtn.classList.remove("toggle--active");
    fileModeArea.style.display = "block";
    urlModeArea.style.display = "none";
  }
};

runButton.addEventListener("click", () => {
  runAll();
});

clearButton.addEventListener("click", () => {
  clearAll();
});

copyAllButton.addEventListener("click", () => {
  copyAllHashtags();
});

exportJsonButton.addEventListener("click", () => {
  exportToJson();
});

exportExcelButton.addEventListener("click", () => {
  exportToExcel();
});

/*
numTagsInput.addEventListener("change", () => {
  let v = parseInt(numTagsInput.value, 10);
  if (isNaN(v) || v < 1) v = 1;
  if (v > 50) v = 50;
  numTagsInput.value = v;
  state.numTags = v;
  state.files.forEach((f) => {
    if (f.status === "pending") {
      f.numTags = v;
    }
  });
  state.urls.forEach((u) => {
    if (u.status === "pending") {
      u.numTags = v;
    }
  });
  updateSummary();
  refreshGallery();
});
*/

modelSelect.addEventListener("change", () => {
  state.model = modelSelect.value;
  state.files.forEach((f) => {
    f.model = state.model;
  });
  state.urls.forEach((u) => {
    u.model = state.model;
  });
  updateSummary();
  refreshGallery();
});

modeSelect.addEventListener("change", () => {
  state.mode = modeSelect.value;
  state.files.forEach((f) => {
    f.mode = state.mode;
  });
  state.urls.forEach((u) => {
    u.mode = state.mode;
  });
  updateSummary();
  refreshGallery();
});

/*
langToggle.addEventListener("click", (e) => {
  if (e.target.matches("button[data-lang]")) {
    const lang = e.target.getAttribute("data-lang");
    state.lang = lang;
    Array.from(langToggle.querySelectorAll("button")).forEach((btn) => {
      btn.classList.toggle("toggle--active", btn === e.target);
    });
    state.files.forEach((f) => {
      if (f.status === "pending") {
        f.lang = lang;
      }
    });
    state.urls.forEach((u) => {
      if (u.status === "pending") {
        u.lang = lang;
      }
    });
    updateSummary();
    refreshGallery();
  }
});
*/

updateSummary();
