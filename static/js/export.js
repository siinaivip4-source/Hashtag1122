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

function escapeCsvValue(value) {
  const v = (value || "").toString().replace(/"/g, '""');
  return `"${v}"`;
}

function getExportData(hashtagSeparator) {
  const sep = typeof hashtagSeparator === "string" && hashtagSeparator.length ? hashtagSeparator : " ";
  const data = [];
  let stt = state.startIndex;

  const buildHashtags = (obj) => {
    const parts = [];

    const style = obj.style && obj.style !== "None" ? obj.style : null;
    const color = obj.color && obj.color !== "None" ? obj.color : null;

    const baseTags = Array.isArray(obj.selectedTags) && obj.selectedTags.length
      ? obj.selectedTags
      : (Array.isArray(obj.tags) ? obj.tags : []);

    const objectTag = baseTags[0];
    const moodTag = baseTags[1];
    const genderTag = baseTags[2];

    if (style) parts.push(style);
    if (color) parts.push(color);
    if (objectTag && objectTag !== "None") parts.push(objectTag);
    if (moodTag && moodTag !== "None") parts.push(moodTag);
    if (genderTag && genderTag !== "None") parts.push(genderTag);

    return parts.join(sep);
  };

  state.files.forEach((f) => {
    if (f.status === "done") {
      data.push({
        "STT": stt++,
        "Tên file": f.file.name,
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

  if (typeof XLSX === "undefined") {
    const headers = ["STT", "Tên file", "Style", "Color", "Hashtags"];
    let csv = headers.join(",") + "\n";

    data.forEach(row => {
      const values = [
        row["STT"],
        escapeCsvValue(row["Tên file"] || ""),
        escapeCsvValue(row["Style"] || ""),
        escapeCsvValue(row["Color"] || ""),
        escapeCsvValue(row["Hashtags"] || "")
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
    return;
  }

  const headers = ["STT", "Tên file", "Style", "Color", "Hashtags"];
  const rows = [headers];

  data.forEach(row => {
    rows.push([
      row["STT"],
      row["Tên file"] || "",
      row["Style"] || "",
      row["Color"] || "",
      row["Hashtags"] || ""
    ]);
  });

  const worksheet = XLSX.utils.aoa_to_sheet(rows);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Hashtags");

  const wbout = XLSX.write(workbook, { bookType: "xlsx", type: "array" });
  const blob = new Blob([wbout], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "hashtags_export.xlsx";
  a.click();
  URL.revokeObjectURL(url);
}

function exportToCsvPipe() {
  const data = getExportData(",");
  if (!data.length) return;

  const headers = ["STT", "Tên file", "Hashtag (style,color,object,mood,gender)"];
  const delimiter = "|";
  let csv = headers.join(delimiter) + "\n";

  data.forEach(row => {
    const values = [
      row["STT"],
      escapeCsvValue(row["Tên file"] || ""),
      escapeCsvValue(row["Hashtags"] || "")
    ];
    csv += values.join(delimiter) + "\n";
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "hashtags_export_pipe.csv";
  a.click();
  URL.revokeObjectURL(url);
}

