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

