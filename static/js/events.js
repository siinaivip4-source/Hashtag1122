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
