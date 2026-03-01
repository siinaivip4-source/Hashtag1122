function clearGalleryEmptyState() {
  const empty = gallery.querySelector('.gallery-empty');
  if (empty) empty.remove();
}

async function createThumbnail(file, maxWidth = 400, maxHeight = 400) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;

        if (width > height) {
          if (width > maxWidth) {
            height *= maxWidth / width;
            width = maxWidth;
          }
        } else {
          if (height > maxHeight) {
            width *= maxHeight / height;
            height = maxHeight;
          }
        }
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);
        resolve(canvas.toDataURL('image/jpeg', 0.7));
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

async function addFiles(fileList) {
  const arr = Array.from(fileList || []);
  if (!arr.length) return;

  clearGalleryEmptyState();

  for (const file of arr) {
    if (!file.type.startsWith("image/")) continue;

    const newIndex = state.files.length;
    // Tạo thumbnail để tiết kiệm RAM/GPU thay vì dùng URL.createObjectURL(file)
    const thumbUrl = await createThumbnail(file);

    const obj = {
      file,
      status: "pending",
      tags: [],
      caption: "",
      style: "",
      color: "",
      error: null,
      previewUrl: thumbUrl,
      lang: state.lang,
      numTags: state.numTags,
      model: state.model,
      mode: state.mode
    };
    state.files.push(obj);

    const item = createItem(obj, newIndex);
    gallery.appendChild(item);
  }
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

