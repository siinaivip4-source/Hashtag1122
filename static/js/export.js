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

function copyAllHashtags() {
  const allTags = [];
  state.files.forEach((f) => {
    if (Array.isArray(f.tags) && f.tags.length) {
      allTags.push(...f.tags);
    }
  });
  state.urls.forEach((u) => {
    if (Array.isArray(u.tags) && u.tags.length) {
      allTags.push(...u.tags);
    }
  });
  if (!allTags.length) return;
  navigator.clipboard.writeText(allTags.join(" ")).catch(() => { });
}

function getExportData() {
  const data = [];
  let stt = 1;

  const buildHashtags = (obj) => {
    let t = Array.isArray(obj.tags) ? [...obj.tags] : [];
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

