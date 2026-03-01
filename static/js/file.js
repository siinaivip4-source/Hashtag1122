function clearGalleryEmptyState() {
  const empty = gallery.querySelector('.gallery-empty');
  if (empty) empty.remove();
}

function addFiles(fileList) {
  const arr = Array.from(fileList || []);
  if (!arr.length) return;

  clearGalleryEmptyState();

  arr.forEach((file) => {
    if (!file.type.startsWith("image/")) return;

    const newIndex = state.files.length;
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

    const item = createItem(obj, newIndex);
    gallery.appendChild(item);
  });
  updateSummary();
  runButton.disabled = !(state.files.length > 0 || state.urls.length > 0);
}

// Drag-over visual feedback
document.addEventListener('DOMContentLoaded', () => {
  // Improved Drag-over visual feedback
  const dz = document.getElementById('dropzoneEl');
  if (!dz) return;

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dz.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    }, false);
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dz.addEventListener(eventName, () => dz.classList.add('drag-over'), false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dz.addEventListener(eventName, () => dz.classList.remove('drag-over'), false);
  });

  dz.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      addFiles(files);
    }
  }, false);

  // Trigger fileInput when clicking anywhere else in the dropzone
  dz.addEventListener('click', (e) => {
    if (e.target.tagName.toLowerCase() !== 'label') {
      fileInput.click();
    }
  });
});

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

  clearGalleryEmptyState();

  urlList.forEach((url) => {
    const newIndex = state.urls.length;
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

    const item = createUrlItem(obj, newIndex);
    gallery.appendChild(item);
  });
  updateSummary();
  runButton.disabled = !(state.files.length > 0 || state.urls.length > 0);
}

