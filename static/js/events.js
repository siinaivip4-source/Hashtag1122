fileInput.addEventListener("change", (e) => {
  addFiles(e.target.files);
  e.target.value = "";
});

folderInput.addEventListener("change", (e) => {
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

retryAllButton.addEventListener("click", () => {
  retryAll();
});

if (clearButton) {
  clearButton.addEventListener("click", () => {
    if (state.running) {
      showToast("Đang bận", "Vui lòng dừng quá trình trước khi xóa.", "warning");
      return;
    }
    clearAll();
    showToast("Đã xóa hết", "Toàn bộ ảnh trong danh sách đã được xóa.", "info");
  });
}

stopButton.addEventListener("click", () => {
  state.running = false;
  statusText.innerHTML = "Đang dừng... Đợi các luồng hiện tại hoàn tất.";
  stopButton.disabled = true;
});

// Event delegation for item actions
gallery.addEventListener("click", (e) => {
  const item = e.target.closest(".item");
  if (!item) return;

  const type = item.dataset.type;
  const index = parseInt(item.dataset.index);

  if (e.target.closest(".btn-run-single")) {
    runSingleTask(type, index);
  } else if (e.target.closest(".btn-delete-single")) {
    deleteTask(type, index);
  }
});

if (exportDropdownButton && exportDropdownMenu) {
  exportDropdownButton.addEventListener("click", (e) => {
    if (state.running) return;
    e.stopPropagation();
    if (exportDropdown) {
      exportDropdown.classList.toggle("dropdown--open");
    }
  });

  document.addEventListener("click", () => {
    if (exportDropdown) {
      exportDropdown.classList.remove("dropdown--open");
    }
  });

  exportDropdownMenu.addEventListener("click", (e) => {
    const item = e.target.closest("[data-export-type]");
    if (!item) return;
    const type = item.getAttribute("data-export-type");
    if (type === "json") {
      exportToJson();
    } else if (type === "excel") {
      exportToExcel();
    } else if (type === "csv") {
      exportToCsvPipe();
    }
    if (exportDropdown) {
      exportDropdown.classList.remove("dropdown--open");
    }
  });
}

startIndexInput.addEventListener("change", () => {
  let v = parseInt(startIndexInput.value, 10);
  if (isNaN(v) || v < 1) v = 1;
  startIndexInput.value = v;
  state.startIndex = v;
  refreshGallery();
});

modelSelect.addEventListener("change", () => {
  if (state.running) {
    showToast("Đang bận", "Vui lòng dừng quá trình trước khi đổi model.", "warning");
    modelSelect.value = state.model;
    return;
  }
  const key = modelSelect.value;
  prepareModel(key);

  // Cập nhật model cho các task chưa chạy (tùy chọn, tùy logic bạn muốn)
  state.files.forEach(f => { if (f.status === "pending") f.model = key; });
  state.urls.forEach(u => { if (u.status === "pending") u.model = key; });
  refreshGallery();
});
updateSummary();
initializeDefaultModel();
