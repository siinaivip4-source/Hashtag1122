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

