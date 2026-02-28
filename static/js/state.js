var state = {
  files: [],
  urls: [],
  lang: "en",
  numTags: 10,
  model: "vit-gpt2",
  mode: "both",
  running: false,
  completed: 0,
  failed: 0,
  inputMode: "file"
};

var fileInput = document.getElementById("fileInput");
var runButton = document.getElementById("runButton");
var clearButton = document.getElementById("clearButton");
var copyAllButton = document.getElementById("copyAllButton");
var exportJsonButton = document.getElementById("exportJsonButton");
var exportExcelButton = document.getElementById("exportExcelButton");
var threadsInput = document.getElementById("threadsInput");
var customVocabInput = document.getElementById("customVocabInput");
var modelSelect = document.getElementById("modelSelect");
var modeSelect = document.getElementById("modeSelect");
var summaryText = document.getElementById("summaryText");
var resultSummary = document.getElementById("resultSummary");
var gallery = document.getElementById("gallery");
var statusDot = document.getElementById("statusDot");
var statusText = document.getElementById("statusText");
var queueHint = document.getElementById("queueHint");
var urlInput = document.getElementById("urlInput");
var fileModeArea = document.getElementById("fileModeArea");
var urlModeArea = document.getElementById("urlModeArea");
var modeFileBtn = document.getElementById("modeFileBtn");
var modeUrlBtn = document.getElementById("modeUrlBtn");

