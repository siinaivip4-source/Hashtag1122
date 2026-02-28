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

