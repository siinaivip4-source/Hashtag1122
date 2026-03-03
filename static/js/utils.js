function formatSize(bytes) {
  if (!bytes && bytes !== 0) return "";
  if (bytes < 1024) return bytes + "B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + "KB";
  return (bytes / (1024 * 1024)).toFixed(1) + "MB";
}

function getModelDisplayName(modelKey) {
  const modelNames = {
    "clip-openai": "CLIP (OpenAI)",
    "clip-openclip-laion": "OpenCLIP (LAION)",
    "clip-openclip-vit-h14": "OpenCLIP (LAION ViT-H/14)",
  };
  return modelNames[modelKey] || modelKey || "CLIP (OpenAI)";
}

function getModeDisplayName() {
  return "Hashtag extraction";
}

function updateSummary() {
  const modelDisplay = getModelDisplayName(state.model);
  summaryText.textContent = modelDisplay;
  const total = state.files.length + state.urls.length;
  resultSummary.textContent = `${total} ảnh · ${state.completed} xong · ${state.failed} lỗi`;

  if (!total) {
    queueHint.textContent = "";
    statusDot.className = "status-dot";
    statusText.innerHTML = "Sẵn sàng. Chưa có ảnh nào trong hàng đợi.";
  } else {
    queueHint.textContent = `Đã chọn ${total} ảnh.`;
  }

  // Cập nhật hiển thị nút Chạy lại
  if (retryAllButton) {
    const hasAnyDone = state.files.some(f => f.status === "done" || f.status === "error") ||
      state.urls.some(u => u.status === "done" || u.status === "error");
    retryAllButton.style.display = (hasAnyDone && !state.running) ? "inline-flex" : "none";
  }
}

function setRunning(running, finishedMessage = null) {
  state.running = running;
  const hasItems = (state.files && state.files.length > 0) || (state.urls && state.urls.length > 0);

  if (runButton) runButton.disabled = running || !hasItems || !state.modelReady;
  if (clearButton) clearButton.disabled = running;
  if (exportDropdownButton) exportDropdownButton.disabled = running;
  if (threadsInput) threadsInput.disabled = running;
  if (customVocabInput) customVocabInput.disabled = running;
  if (modelSelect) modelSelect.disabled = running;
  if (fileInput) fileInput.disabled = running;
  if (urlInput) urlInput.disabled = running;
  if (modeFileBtn) modeFileBtn.disabled = running;
  if (modeUrlBtn) modeUrlBtn.disabled = running;

  if (modeUrlBtn) modeUrlBtn.disabled = running;

  if (stopButton) {
    stopButton.style.display = running ? "inline-flex" : "none";
    stopButton.disabled = !running;
  }

  if (statusDot && statusText) {
    if (running) {
      statusDot.className = "status-dot status-dot--ok";
      statusText.innerHTML = "Đang chạy hashtag cho các ảnh đã chọn...";
    } else {
      if (!totalItems()) {
        statusDot.className = "status-dot";
        statusText.innerHTML = "Sẵn sàng (Done).";
      } else {
        statusDot.className = "status-dot status-dot--ok";
        statusText.innerHTML = finishedMessage || "Đã xử lý xong. Bạn có thể thêm ảnh mới.";
      }
    }
  }

  // Luôn cập nhật summary để đồng bộ UI (bao gồm nút Chạy lại)
  updateSummary();
}

function totalItems() {
  return (state.files ? state.files.length : 0) + (state.urls ? state.urls.length : 0);
}
