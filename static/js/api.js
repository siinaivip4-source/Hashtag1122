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

  const allStyles = ["None", "2D", "3D", "Cute", "Animeart", "Realism", "Aesthetic", "Cool", "Fantasy", "Comic", "Horror", "Cyberpunk", "Lofi", "Minimalism", "Digitalart", "Cinematic", "Pixelart", "Scifi", "Vangoghart"];
  const allColors = ["None", "Black", "White", "Blackandwhite", "Red", "Yellow", "Blue", "Green", "Pink", "Orange", "Pastel", "Hologram", "Vintage", "Colorful", "Neutral", "Light", "Dark", "Warm", "Cold", "Neon", "Gradient", "Purple", "Brown", "Grey"];

  let resultHtml = "";

  const createSelectHtml = (options, selectedValue, label) => {
    const opts = options.map(opt => `<option value="${opt}" ${opt === selectedValue ? "selected" : ""}>${opt}</option>`).join('');
    return `<label style="display:inline-flex; flex-direction:column; font-size:10px; color:#9ca3af; gap:2px;">
              ${label}
              <select class="custom-val-select" style="font-size:11px; padding:2px 4px; border-radius:4px; max-width: 100px;" onchange="
                const val = this.value;
                const field = '${label.toLowerCase()}';
                const fileIndex = ${index};
                state.files[fileIndex][field] = val;
              ">
                ${opts}
              </select>
            </label>`;
  };

  resultHtml += `<div class="result-badges" style="display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:8px; margin-bottom:8px;">`;
  resultHtml += createSelectHtml(allStyles, style || "None", "Style");
  resultHtml += createSelectHtml(allColors, color || "None", "Color");
  resultHtml += `</div>`;

  statusText.textContent = tags.length ? "Đã hoàn thành" : "Không nhận được hashtag";
  tagsEl.innerHTML = "";

  if (resultHtml) {
    tagsEl.innerHTML = resultHtml;
  }

  if (tags.length) {
    const tagsContainer = document.createElement("div");
    tagsContainer.className = "tags-list-container";

    tags.forEach((tag, tagIndex) => {
      const el = document.createElement("code");
      el.textContent = tag;
      tagsContainer.appendChild(el);
    });

    tagsEl.appendChild(tagsContainer);

    footerMeta.textContent = `${tags.length} hashtag`;
    copyBtn.disabled = false;
    copyBtn.onclick = () => {
      const t = Array.isArray(fileObj.tags) ? fileObj.tags : [];
      let cnf = [fileObj.style, fileObj.color];
      cnf = cnf.filter(x => x && x !== "None");
      const resTags = [...t, ...cnf];
      navigator.clipboard.writeText(resTags.join(" ")).catch(() => { });
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

  const allStyles = ["None", "2D", "3D", "Cute", "Animeart", "Realism", "Aesthetic", "Cool", "Fantasy", "Comic", "Horror", "Cyberpunk", "Lofi", "Minimalism", "Digitalart", "Cinematic", "Pixelart", "Scifi", "Vangoghart"];
  const allColors = ["None", "Black", "White", "Blackandwhite", "Red", "Yellow", "Blue", "Green", "Pink", "Orange", "Pastel", "Hologram", "Vintage", "Colorful", "Neutral", "Light", "Dark", "Warm", "Cold", "Neon", "Gradient", "Purple", "Brown", "Grey"];

  let resultHtml = "";

  const createSelectHtml = (options, selectedValue, label) => {
    const opts = options.map(opt => `<option value="${opt}" ${opt === selectedValue ? "selected" : ""}>${opt}</option>`).join('');
    return `<label style="display:inline-flex; flex-direction:column; font-size:10px; color:#9ca3af; gap:2px;">
              ${label}
              <select class="custom-val-select" style="font-size:11px; padding:2px 4px; border-radius:4px; max-width: 100px;" onchange="
                const val = this.value;
                const field = '${label.toLowerCase()}';
                const fileIndex = ${index};
                state.urls[fileIndex][field] = val;
              ">
                ${opts}
              </select>
            </label>`;
  };

  resultHtml += `<div class="result-badges" style="display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:8px; margin-bottom:8px;">`;
  resultHtml += createSelectHtml(allStyles, style || "None", "Style");
  resultHtml += createSelectHtml(allColors, color || "None", "Color");
  resultHtml += `</div>`;

  statusText.textContent = tags.length ? "Đã hoàn thành" : "Không nhận được hashtag";
  tagsEl.innerHTML = "";

  if (resultHtml) {
    tagsEl.innerHTML = resultHtml;
  }

  if (tags.length) {
    const tagsContainer = document.createElement("div");
    tagsContainer.className = "tags-list-container";

    tags.forEach((tag, tagIndex) => {
      const el = document.createElement("code");
      el.textContent = tag;
      tagsContainer.appendChild(el);
    });

    tagsEl.appendChild(tagsContainer);

    footerMeta.textContent = `${tags.length} hashtag`;
    copyBtn.disabled = false;
    copyBtn.onclick = () => {
      const t = Array.isArray(urlObj.tags) ? urlObj.tags : [];
      let cnf = [urlObj.style, urlObj.color];
      cnf = cnf.filter(x => x && x !== "None");
      const resTags = [...t, ...cnf];
      navigator.clipboard.writeText(resTags.join(" ")).catch(() => { });
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

