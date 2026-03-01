function clearGalleryEmptyState() {
  const empty = gallery.querySelector('.gallery-empty');
  if (empty) empty.remove();
}

function addFiles(fileList) {
  const arr = Array.from(fileList || []);
  if (!arr.length) return;

  clearGalleryEmptyState();

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

// Drag-over visual feedback
document.addEventListener('DOMContentLoaded', () => {
  const dz = document.getElementById('dropzoneEl');
  if (!dz) return;
  dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('drag-over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
  dz.addEventListener('drop', (e) => {
    e.preventDefault();
    dz.classList.remove('drag-over');
    if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
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

