function clearAll() {
  if (state.running) return;
  state.files.forEach((f) => {
    if (f.previewUrl) URL.revokeObjectURL(f.previewUrl);
  });
  state.files = [];
  state.urls = [];
  state.completed = 0;
  state.failed = 0;
  urlInput.value = "";
  refreshGallery();
  updateSummary();
}

function deleteTask(type, index) {
  if (state.running) {
    showToast("Đang bận", "Vui lòng dừng quá trình trước khi xóa.", "warning");
    return;
  }

  const obj = type === "file" ? state.files[index] : state.urls[index];
  if (!obj) return;

  // Cập nhật đếm số lượng nếu ảnh đã xử lý
  if (obj.status === "done") state.completed--;
  if (obj.status === "error") state.failed--;

  if (type === "file") {
    if (obj.previewUrl) URL.revokeObjectURL(obj.previewUrl);
    state.files.splice(index, 1);
  } else {
    state.urls.splice(index, 1);
  }

  refreshGallery();
  updateSummary();
  showToast("Đã xóa", "Đã xóa ảnh khỏi danh sách.", "info");
}


function getExportData() {
  const data = [];
  let stt = state.startIndex;

  const buildHashtags = (obj) => {
    let t = Array.isArray(obj.selectedTags) ? [...obj.selectedTags] : (Array.isArray(obj.tags) ? [...obj.tags] : []);
    // Nếu có selectedTags thì đã được lọc/giới hạn sẵn, 
    // nếu chưa chạy (có .tags nhưng chưa .selectedTags) thì build tạm
    if (obj.style && obj.style !== "None") t.push(obj.style);
    if (obj.color && obj.color !== "None") t.push(obj.color);
    return t.join(" ");
  };

  state.files.forEach((f) => {
    if (f.status === "done") {
      data.push({
        "STT": stt++,
        "Tên file": f.file.name,
        "Caption": f.caption || "",
        "Style": f.style || "",
        "Color": f.color || "",
        "Hashtags": buildHashtags(f)
      });
    }
  });
  state.urls.forEach((u) => {
    if (u.status === "done") {
      data.push({
        "STT": stt++,
        "Tên file": u.url,
        "Caption": u.caption || "",
        "Style": u.style || "",
        "Color": u.color || "",
        "Hashtags": buildHashtags(u)
      });
    }
  });
  return data;
}

function exportToJson() {
  const data = getExportData();
  if (!data.length) return;

  const jsonStr = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "hashtags_export.json";
  a.click();
  URL.revokeObjectURL(url);
}

function exportToExcel() {
  const data = getExportData();
  if (!data.length) return;

  const headers = ["STT", "Tên file", "Caption", "Style", "Color", "Hashtags"];
  let csv = headers.join(",") + "\n";

  data.forEach(row => {
    const values = [
      row["STT"],
      `"${(row["Tên file"] || "").replace(/"/g, '""')}"`,
      `"${(row["Caption"] || "").replace(/"/g, '""')}"`,
      `"${(row["Style"] || "").replace(/"/g, '""')}"`,
      `"${(row["Color"] || "").replace(/"/g, '""')}"`,
      `"${(row["Hashtags"] || "").replace(/"/g, '""')}"`
    ];
    csv += values.join(",") + "\n";
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "hashtags_export.csv";
  a.click();
  URL.revokeObjectURL(url);
}

