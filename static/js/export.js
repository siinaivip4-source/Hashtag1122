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

/**
 * Tạo dữ liệu export với 8 cột riêng biệt:
 * STT | Tên file | Object 1 | Object 2 | Style | Color | Mood | Gender
 *
 * selectedTags = [Object1, Object2, Mood, Gender]  ← format mới (4 phần tử)
 * Backward-compatible với format cũ [Object, Mood, Gender] (3 phần tử)
 */
function getExportData() {
  const data = [];
  let stt = state.startIndex;

  const buildRow = (obj, name) => {
    const tags = Array.isArray(obj.selectedTags) ? obj.selectedTags : [];
    let obj1 = "", obj2 = "", mood = "", gender = "";

    if (tags.length >= 4) {
      // Format mới
      obj1   = tags[0] !== "None" ? tags[0] : "";
      obj2   = tags[1] !== "None" ? tags[1] : "";
      mood   = tags[2] !== "None" ? tags[2] : "";
      gender = tags[3] !== "None" ? tags[3] : "";
    } else if (tags.length === 3) {
      // Format cũ [Obj, Mood, Gender]
      obj1   = tags[0] !== "None" ? tags[0] : "";
      mood   = tags[1] !== "None" ? tags[1] : "";
      gender = tags[2] !== "None" ? tags[2] : "";
    }

    const style  = obj.style  && obj.style  !== "None" ? obj.style  : "";
    const color  = obj.color  && obj.color  !== "None" ? obj.color  : "";

    return {
      "STT":      stt++,
      "Tên file": name,
      "Object 1": obj1,
      "Object 2": obj2,
      "Style":    style,
      "Color":    color,
      "Mood":     mood,
      "Gender":   gender,
    };
  };

  state.files.forEach((f) => {
    if (f.status === "done") {
      data.push(buildRow(f, f.file.name));
    }
  });
  state.urls.forEach((u) => {
    if (u.status === "done") {
      data.push(buildRow(u, u.url));
    }
  });
  return data;
}

// ── Các hàm export ────────────────────────────────────────────────

const EXPORT_HEADERS = ["STT", "Tên file", "Object 1", "Object 2", "Style", "Color", "Mood", "Gender"];

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
    // Fallback sang CSV nếu XLSX chưa tải
    let csv = EXPORT_HEADERS.join(",") + "\n";
    data.forEach(row => {
      const values = EXPORT_HEADERS.map(h =>
        h === "STT" ? row[h] : escapeCsvValue(row[h] || "")
      );
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

  const rows = [EXPORT_HEADERS];
  data.forEach(row => {
    rows.push(EXPORT_HEADERS.map(h => row[h] || (h === "STT" ? 0 : "")));
  });

  const worksheet = XLSX.utils.aoa_to_sheet(rows);

  // Đặt độ rộng cột
  worksheet["!cols"] = [
    { wch: 6  }, // STT
    { wch: 40 }, // Tên file
    { wch: 20 }, // Object 1
    { wch: 20 }, // Object 2
    { wch: 14 }, // Style
    { wch: 14 }, // Color
    { wch: 10 }, // Mood
    { wch: 10 }, // Gender
  ];

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
  const data = getExportData();
  if (!data.length) return;

  const delimiter = "|";
  let csv = EXPORT_HEADERS.join(delimiter) + "\n";

  data.forEach(row => {
    const values = EXPORT_HEADERS.map(h =>
      h === "STT" ? row[h] : escapeCsvValue(row[h] || "")
    );
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
